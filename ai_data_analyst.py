import os
import re
import tempfile
import csv
import duckdb
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
from huggingface_hub import InferenceClient

# ─── Load environment variables ──────────────────────────────────────────────
load_dotenv()
# HF_API_KEY = os.getenv("HF_API_KEY")
GROQ_API_KEY = os.getenv("GROQ_API_KEY") 

# ─── Page config ─────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="AI Data Analysis Agent",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded", 
) 

# ─── Custom CSS ──────────────────────────────────────────────────────────────
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}

/* Dark gradient background */
.stApp {
    background: linear-gradient(135deg, #0f0c29, #302b63, #24243e);
    min-height: 100vh;
}

/* Hero header */
.hero-header {
    text-align: center;
    padding: 2rem 0 1rem 0;
    background: linear-gradient(90deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    font-size: 2.8rem;
    font-weight: 700;
    letter-spacing: -1px;
}

.hero-sub {
    text-align: center;
    color: rgba(255,255,255,0.55);
    font-size: 1.05rem;
    margin-bottom: 2rem;
}

/* Metric cards */
.metric-card {
    background: rgba(255,255,255,0.05);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 16px;
    padding: 1.2rem 1.5rem;
    backdrop-filter: blur(12px);
    text-align: center;
    transition: transform 0.2s, box-shadow 0.2s;
}
.metric-card:hover {
    transform: translateY(-4px);
    box-shadow: 0 8px 32px rgba(102,126,234,0.3);
}
.metric-label {
    color: rgba(255,255,255,0.5);
    font-size: 0.78rem;
    font-weight: 500;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
}
.metric-value {
    color: #fff;
    font-size: 1.9rem;
    font-weight: 700;
}
.metric-sub {
    color: rgba(255,255,255,0.45);
    font-size: 0.75rem;
}

/* Tab styling */
.stTabs [data-baseweb="tab-list"] {
    gap: 8px;
    background: rgba(255,255,255,0.04);
    border-radius: 12px;
    padding: 4px;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 8px;
    color: rgba(255,255,255,0.55);
    font-weight: 500;
    padding: 8px 20px;
}
.stTabs [aria-selected="true"] {
    background: linear-gradient(135deg, #667eea, #764ba2) !important;
    color: white !important;
}

/* Section headers */
.section-header {
    color: white;
    font-size: 1.3rem;
    font-weight: 600;
    margin-bottom: 1rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid rgba(255,255,255,0.1);
}

/* Chat bubbles */
.chat-user {
    background: linear-gradient(135deg, #667eea, #764ba2);
    border-radius: 18px 18px 4px 18px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: white;
    max-width: 75%;
    margin-left: auto;
    font-size: 0.95rem;
}
.chat-assistant {
    background: rgba(255,255,255,0.06);
    border: 1px solid rgba(255,255,255,0.1);
    border-radius: 18px 18px 18px 4px;
    padding: 0.8rem 1.2rem;
    margin: 0.5rem 0;
    color: rgba(255,255,255,0.9);
    max-width: 85%;
    font-size: 0.95rem;
}
.chat-label {
    font-size: 0.7rem;
    font-weight: 600;
    text-transform: uppercase;
    letter-spacing: 1px;
    margin-bottom: 0.3rem;
    color: rgba(255,255,255,0.4);
}

/* Sidebar */
section[data-testid="stSidebar"] {
    background: rgba(15, 12, 41, 0.7);
    border-right: 1px solid rgba(255,255,255,0.08);
}

/* Upload area */
.uploadedFile {
    border-radius: 12px !important;
}

/* Scrollbar */
::-webkit-scrollbar { width: 6px; }
::-webkit-scrollbar-track { background: rgba(255,255,255,0.05); }
::-webkit-scrollbar-thumb { background: rgba(102,126,234,0.5); border-radius: 3px; }

/* Dataframe */
.stDataFrame { border-radius: 12px; overflow: hidden; }

/* Buttons */
.stButton > button {
    background: linear-gradient(135deg, #667eea, #764ba2);
    color: white;
    border: none;
    border-radius: 10px;
    padding: 0.5rem 1.5rem;
    font-weight: 600;
    transition: opacity 0.2s, transform 0.2s;
}
.stButton > button:hover {
    opacity: 0.88;
    transform: translateY(-1px);
}
</style>
""", unsafe_allow_html=True)


# ─── Helper: preprocess uploaded file ────────────────────────────────────────
def preprocess_and_save(file):
    try:
        if file.name.endswith('.csv'):
            df = pd.read_csv(file, encoding='utf-8', na_values=['NA', 'N/A', 'missing'])
        elif file.name.endswith('.xlsx'):
            df = pd.read_excel(file, na_values=['NA', 'N/A', 'missing'])
        else:
            st.error("Unsupported file format. Please upload a CSV or Excel file.")
            return None, None, None

        # Parse dates and try numeric conversion on object cols
        for col in df.columns:
            if 'date' in col.lower():
                df[col] = pd.to_datetime(df[col], errors='coerce')
            elif df[col].dtype == 'object':
                try:
                    df[col] = pd.to_numeric(df[col])
                except (ValueError, TypeError):
                    pass

        with tempfile.NamedTemporaryFile(delete=False, suffix=".csv") as tmp:
            temp_path = tmp.name
            df.to_csv(temp_path, index=False, quoting=csv.QUOTE_ALL)

        return temp_path, df.columns.tolist(), df
    except Exception as e:
        st.error(f"Error processing file: {e}")
        return None, None, None


# ─── Helper: build plotly graphs ─────────────────────────────────────────────
def build_visualizations(df):
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    cat_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()

    PLOT_BG = "rgba(0,0,0,0)"
    PAPER_BG = "rgba(0,0,0,0)"
    FONT_COLOR = "rgba(255,255,255,0.85)"
    GRID_COLOR = "rgba(255,255,255,0.08)"
    PALETTE = px.colors.sequential.Plasma

    layout_defaults = dict(
        plot_bgcolor=PLOT_BG,
        paper_bgcolor=PAPER_BG,
        font=dict(color=FONT_COLOR, family="Inter"),
        margin=dict(l=20, r=20, t=40, b=20),
        xaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
        yaxis=dict(gridcolor=GRID_COLOR, zerolinecolor=GRID_COLOR),
    )

    # ── 1. Missing values heatmap ─────────────────────────────────────────
    st.markdown('<div class="section-header">🔍 Missing Values</div>', unsafe_allow_html=True)
    missing = df.isnull().sum()
    missing_pct = (missing / len(df) * 100).round(2)
    missing_df = pd.DataFrame({"Column": missing.index, "Missing": missing.values, "Pct": missing_pct.values})
    fig_miss = px.bar(
        missing_df, x="Column", y="Pct",
        color="Pct", color_continuous_scale="RdYlGn_r",
        title="Missing Values (%)",
        labels={"Pct": "Missing %"},
        template="plotly_dark",
    )
    fig_miss.update_layout(**layout_defaults)
    st.plotly_chart(fig_miss, use_container_width=True)

    # ── 2. Numeric distributions (histograms) ────────────────────────────
    if numeric_cols:
        st.markdown('<div class="section-header">📈 Numeric Distributions</div>', unsafe_allow_html=True)
        cols_per_row = 2
        for i in range(0, len(numeric_cols), cols_per_row):
            row_cols = st.columns(cols_per_row)
            for j, col in enumerate(numeric_cols[i: i + cols_per_row]):
                with row_cols[j]:
                    fig = px.histogram(
                        df, x=col, nbins=40,
                        marginal="box",
                        color_discrete_sequence=["#667eea"],
                        title=f"Distribution: {col}",
                        template="plotly_dark",
                    )
                    fig.update_layout(**layout_defaults)
                    st.plotly_chart(fig, use_container_width=True)

        # ── 3. Box plots ──────────────────────────────────────────────────
        st.markdown('<div class="section-header">📦 Box Plots</div>', unsafe_allow_html=True)
        fig_box = go.Figure()
        for col in numeric_cols:
            fig_box.add_trace(go.Box(
                y=df[col].dropna(),
                name=col,
                boxmean='sd',
                marker_color="#764ba2",
            ))
        fig_box.update_layout(
            title="Box Plots – All Numeric Columns",
            template="plotly_dark",
            **layout_defaults,
        )
        st.plotly_chart(fig_box, use_container_width=True)

        # ── 4. Correlation heatmap ────────────────────────────────────────
        if len(numeric_cols) >= 2:
            st.markdown('<div class="section-header">🔥 Correlation Heatmap</div>', unsafe_allow_html=True)
            corr = df[numeric_cols].corr()
            fig_corr = go.Figure(data=go.Heatmap(
                z=corr.values,
                x=corr.columns.tolist(),
                y=corr.index.tolist(),
                colorscale="Plasma",
                text=corr.round(2).values,
                texttemplate="%{text}",
                showscale=True,
                hoverongaps=False,
            ))
            fig_corr.update_layout(
                title="Pearson Correlation Matrix",
                template="plotly_dark",
                **layout_defaults,
            )
            st.plotly_chart(fig_corr, use_container_width=True)

            # ── 5. Scatter matrix ─────────────────────────────────────────
            show_cols = numeric_cols[:5]  # limit for performance
            st.markdown('<div class="section-header">🔗 Scatter Matrix (first 5 numeric cols)</div>', unsafe_allow_html=True)
            fig_splom = px.scatter_matrix(
                df[show_cols].dropna(),
                dimensions=show_cols,
                color_discrete_sequence=["#f093fb"],
                template="plotly_dark",
                title="Scatter Matrix",
            )
            fig_splom.update_traces(marker=dict(size=3, opacity=0.6))
            fig_splom.update_layout(**layout_defaults)
            st.plotly_chart(fig_splom, use_container_width=True)

            # ── 6. Violin plots ───────────────────────────────────────────
            st.markdown('<div class="section-header">🎻 Violin Plots</div>', unsafe_allow_html=True)
            cols_per_row = 2
            for i in range(0, len(numeric_cols), cols_per_row):
                row_cols = st.columns(cols_per_row)
                for j, col in enumerate(numeric_cols[i: i + cols_per_row]):
                    with row_cols[j]:
                        fig_v = px.violin(
                            df, y=col,
                            box=True,
                            points="outliers",
                            color_discrete_sequence=["#f093fb"],
                            title=f"Violin: {col}",
                            template="plotly_dark",
                        )
                        fig_v.update_layout(**layout_defaults)
                        st.plotly_chart(fig_v, use_container_width=True)

    # ── 7. Categorical bar charts ─────────────────────────────────────────
    if cat_cols:
        st.markdown('<div class="section-header">📊 Categorical Columns</div>', unsafe_allow_html=True)
        for col in cat_cols[:6]:  # limit for performance
            vc = df[col].value_counts().head(20).reset_index()
            vc.columns = [col, "Count"]
            fig_bar = px.bar(
                vc, x=col, y="Count",
                color="Count",
                color_continuous_scale="Viridis",
                title=f"Value Counts: {col}",
                template="plotly_dark",
            )
            fig_bar.update_layout(**layout_defaults)
            st.plotly_chart(fig_bar, use_container_width=True)

            # Pie chart for low-cardinality cols
            if df[col].nunique() <= 10:
                fig_pie = px.pie(
                    vc, names=col, values="Count",
                    color_discrete_sequence=px.colors.sequential.Plasma,
                    title=f"Proportion: {col}",
                    template="plotly_dark",
                )
                fig_pie.update_layout(**layout_defaults)
                st.plotly_chart(fig_pie, use_container_width=True)

    # ── 8. Time series (if date cols exist) ──────────────────────────────
    date_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    if date_cols and numeric_cols:
        st.markdown('<div class="section-header">📅 Time Series</div>', unsafe_allow_html=True)
        date_col = date_cols[0]
        for ncol in numeric_cols[:3]:
            fig_ts = px.line(
                df.sort_values(date_col),
                x=date_col, y=ncol,
                title=f"{ncol} over Time",
                template="plotly_dark",
                color_discrete_sequence=["#667eea"],
            )
            fig_ts.update_layout(**layout_defaults)
            st.plotly_chart(fig_ts, use_container_width=True)

    # ── 9. Cumulative Distribution (ECDF) ────────────────────────────────
    if numeric_cols:
        st.markdown('<div class="section-header">📉 Cumulative Distribution (ECDF)</div>', unsafe_allow_html=True)
        cols_per_row = 2
        for i in range(0, len(numeric_cols), cols_per_row):
            row_cols = st.columns(cols_per_row)
            for j, col in enumerate(numeric_cols[i: i + cols_per_row]):
                with row_cols[j]:
                    fig_ecdf = px.ecdf(
                        df, x=col,
                        title=f"ECDF: {col}",
                        template="plotly_dark",
                        color_discrete_sequence=["#f093fb"],
                    )
                    fig_ecdf.update_layout(**layout_defaults)
                    st.plotly_chart(fig_ecdf, use_container_width=True)

    # ── 10. Bubble Chart (first 3 numeric cols) ──────────────────────────
    if len(numeric_cols) >= 3:
        st.markdown('<div class="section-header">🫧 Bubble Chart</div>', unsafe_allow_html=True)
        x_c, y_c, s_c = numeric_cols[0], numeric_cols[1], numeric_cols[2]
        color_col = cat_cols[0] if cat_cols else None
        fig_bub = px.scatter(
            df.dropna(subset=[x_c, y_c, s_c]),
            x=x_c, y=y_c,
            size=s_c,
            color=color_col,
            size_max=40,
            title=f"Bubble: {x_c} vs {y_c} (size={s_c})",
            template="plotly_dark",
        )
        fig_bub.update_layout(**layout_defaults)
        st.plotly_chart(fig_bub, use_container_width=True)

    # ── 11. Treemap (categorical) ─────────────────────────────────────────
    if cat_cols and numeric_cols:
        st.markdown('<div class="section-header">🌳 Treemap</div>', unsafe_allow_html=True)
        tc = cat_cols[0]
        nc = numeric_cols[0]
        tm_df = df.groupby(tc)[nc].sum().reset_index().rename(columns={nc: "Total"})
        fig_tree = px.treemap(
            tm_df, path=[tc], values="Total",
            title=f"Treemap: {tc} by {nc}",
            template="plotly_dark",
            color="Total",
            color_continuous_scale="Plasma",
        )
        fig_tree.update_layout(**layout_defaults)
        st.plotly_chart(fig_tree, use_container_width=True)

    # ── 12. Sunburst (up to 2 cat cols) ──────────────────────────────────
    if len(cat_cols) >= 2 and numeric_cols:
        st.markdown('<div class="section-header">☀️ Sunburst Chart</div>', unsafe_allow_html=True)
        try:
            sb_df = df.groupby([cat_cols[0], cat_cols[1]])[numeric_cols[0]].sum().reset_index()
            fig_sun = px.sunburst(
                sb_df, path=[cat_cols[0], cat_cols[1]], values=numeric_cols[0],
                title=f"Sunburst: {cat_cols[0]} → {cat_cols[1]} by {numeric_cols[0]}",
                template="plotly_dark",
                color=numeric_cols[0],
                color_continuous_scale="Plasma",
            )
            fig_sun.update_layout(**layout_defaults)
            st.plotly_chart(fig_sun, use_container_width=True)
        except Exception:
            pass

    # ── 13. Funnel Chart (top categorical) ───────────────────────────────
    if cat_cols:
        st.markdown('<div class="section-header">🔽 Funnel Chart</div>', unsafe_allow_html=True)
        fc = cat_cols[0]
        fv = df[fc].value_counts().head(10).reset_index()
        fv.columns = [fc, "Count"]
        fig_fun = px.funnel(
            fv, x="Count", y=fc,
            title=f"Funnel: Top values in {fc}",
            template="plotly_dark",
            color_discrete_sequence=["#667eea"],
        )
        fig_fun.update_layout(**layout_defaults)
        st.plotly_chart(fig_fun, use_container_width=True)

    # ── 14. Grouped Bar (cat vs numeric) ─────────────────────────────────
    if cat_cols and len(numeric_cols) >= 2:
        st.markdown('<div class="section-header">📊 Grouped Bar Chart</div>', unsafe_allow_html=True)
        try:
            grp_df = df.groupby(cat_cols[0])[numeric_cols[:3]].mean().reset_index()
            fig_grp = px.bar(
                grp_df.melt(id_vars=cat_cols[0], value_vars=numeric_cols[:3]),
                x=cat_cols[0], y="value", color="variable",
                barmode="group",
                title=f"Grouped Avg by {cat_cols[0]}",
                template="plotly_dark",
                color_discrete_sequence=px.colors.qualitative.Vivid,
            )
            fig_grp.update_layout(**layout_defaults)
            st.plotly_chart(fig_grp, use_container_width=True)
        except Exception:
            pass

    # ── 15. Numeric heatmap (pivot: cat × numeric bins) ───────────────────
    if cat_cols and numeric_cols:
        st.markdown('<div class="section-header">🟥 Pivot Heatmap (Category × Numeric)</div>', unsafe_allow_html=True)
        try:
            piv = df.pivot_table(values=numeric_cols[0], index=cat_cols[0],
                                  aggfunc='mean').reset_index()
            piv_sorted = piv.sort_values(numeric_cols[0], ascending=False).head(20)
            fig_ph = px.bar(
                piv_sorted, x=cat_cols[0], y=numeric_cols[0],
                color=numeric_cols[0],
                color_continuous_scale="RdBu",
                title=f"Mean {numeric_cols[0]} by {cat_cols[0]}",
                template="plotly_dark",
            )
            fig_ph.update_layout(**layout_defaults)
            st.plotly_chart(fig_ph, use_container_width=True)
        except Exception:
            pass


# ─── Helper: dataset summary stats ───────────────────────────────────────────
def show_overview(df):
    numeric_cols = df.select_dtypes(include=np.number).columns.tolist()
    rows, cols = df.shape
    missing_total = int(df.isnull().sum().sum())
    dup_rows = int(df.duplicated().sum())
    missing_pct = round(missing_total / (rows * cols) * 100, 2) if rows * cols > 0 else 0

    # ── Metric cards ──────────────────────────────────────────────────────
    c1, c2, c3, c4, c5 = st.columns(5)
    metrics = [
        (c1, "Rows", f"{rows:,}", "records"),
        (c2, "Columns", f"{cols}", "features"),
        (c3, "Numeric", f"{len(numeric_cols)}", "columns"),
        (c4, "Missing", f"{missing_pct}%", f"{missing_total} cells"),
        (c5, "Duplicates", f"{dup_rows:,}", "rows"),
    ]
    for container, label, value, sub in metrics:
        with container:
            st.markdown(f"""
            <div class="metric-card">
                <div class="metric-label">{label}</div>
                <div class="metric-value">{value}</div>
                <div class="metric-sub">{sub}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("<br>", unsafe_allow_html=True)

    # ── Data preview ──────────────────────────────────────────────────────
    st.markdown('<div class="section-header">👁️ Data Preview</div>', unsafe_allow_html=True)
    st.dataframe(df.head(50), use_container_width=True, height=300)

    # ── Descriptive statistics ────────────────────────────────────────────
    st.markdown('<div class="section-header">📐 Descriptive Statistics</div>', unsafe_allow_html=True)
    st.dataframe(df.describe(include='all').T, use_container_width=True)

    # ── Column types table ────────────────────────────────────────────────
    st.markdown('<div class="section-header">🗂️ Column Info</div>', unsafe_allow_html=True)
    info_df = pd.DataFrame({
        "Column": df.columns,
        "DType": df.dtypes.values.astype(str),
        "Non-Null": df.count().values,
        "Null": df.isnull().sum().values,
        "Null%": (df.isnull().sum().values / len(df) * 100).round(2),
        "Unique": df.nunique().values,
        "Sample": [str(df[c].dropna().iloc[0]) if df[c].dropna().shape[0] > 0 else "—" for c in df.columns],
    })
    st.dataframe(info_df, use_container_width=True)


# ─── Sidebar ──────────────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## 📊 AI Data Analyst")
    st.markdown("---")
    st.markdown("**Upload your dataset** to get started.\nSupports CSV and Excel files.")
    st.markdown("---")
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=["csv", "xlsx"],
        help="Upload a CSV or Excel file to begin analysis",
    )
    st.markdown("---")
    # if HF_API_KEY:
    #     st.success("✅ HuggingFace API connected")
    # else:
    #     st.error("❌ HF_API_KEY not found in .env")
    GROQ_API_KEY = os.getenv("GROQ_API_KEY")
    if GROQ_API_KEY:   
        st.success("✅ Groq API connected")
    else:
        st.error("❌ GROQ_API_KEY not found in .env")
    st.markdown("---")
    # st.markdown("**Model:** meta-llama/Meta-Llama-3-8B-Instruct")
    st.markdown("**Model:** llama-3.3-70b-versatile")
    st.markdown("**Powered by:** Groq Inference API")
 

# ─── Main content ─────────────────────────────────────────────────────────────
st.markdown('<div class="hero-header">📊 AI Data Analysis Agent</div>', unsafe_allow_html=True)
st.markdown('<div class="hero-sub">Upload a dataset and explore insights instantly</div>', unsafe_allow_html=True)

if uploaded_file is None:
    st.info("👈 Upload a CSV or Excel file from the sidebar to begin.")
    st.stop()

# Process file
if "processed_data" not in st.session_state or st.session_state.get("last_file") != uploaded_file.name:
    with st.spinner("Processing your dataset…"):
        temp_path, columns, df = preprocess_and_save(uploaded_file)
    if temp_path is None:
        st.stop() 
    st.session_state.processed_data = (temp_path, columns, df)
    st.session_state.last_file = uploaded_file.name
    st.session_state.chat_history = []

temp_path, columns, df = st.session_state.processed_data

# ─── Tabs ────────────────────────────────────────────────────────────────────
tab1, tab2, tab3 = st.tabs(["🗂️ Dataset Overview", "📈 Visualizations", "🤖 AI Chatbot"])

# ══════════════════════════════════════════════════════════════════════════════
# TAB 1 – Dataset Overview
# ══════════════════════════════════════════════════════════════════════════════
with tab1:
    show_overview(df)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 2 – Visualizations (pandas-profiling style)
# ══════════════════════════════════════════════════════════════════════════════
with tab2:
    st.markdown("### 📊 Full Data Profiling & Visualizations")
    st.caption("Comprehensive visual exploration of your dataset — auto-generated from your data.")
    build_visualizations(df)

# ══════════════════════════════════════════════════════════════════════════════
# TAB 3 – AI Chatbot  (tool-free: LLM writes SQL → local duckdb → LLM explains)
# ══════════════════════════════════════════════════════════════════════════════

# Build dataset schema string once
_schema_lines = []
for c in df.columns:
    _schema_lines.append(f"  {c} ({df[c].dtype})")
_schema = "\n".join(_schema_lines)
_sample = df.head(3).to_string(index=False)
# _SYSTEM = (
#     "You are an expert data analyst. A DuckDB table called 'uploaded_data' "
#     "holds the user's dataset.\n\n"
#     f"Schema:\n{_schema}\n\nSample rows:\n{_sample}\n\n"
#     "Rules:\n"
#     "1. To answer a question that needs data, FIRST output a DuckDB SQL query "
#     "inside a ```sql ... ``` code block — nothing else on that turn.\n"
#     "2. If you already have query results (provided in the message), interpret "
#     "them in plain English. Be concise, friendly and format numbers nicely.\n"
#     "3. If the question is purely conversational (no data needed), just answer directly."
# )
_SYSTEM = (
    "You are an expert data analyst. A DuckDB table called 'uploaded_data' "
    "holds the user's dataset.\n\n"
    f"Schema:\n{_schema}\n\nSample rows:\n{_sample}\n\n"
    "Rules:\n"
    "1. To answer a question that needs data, FIRST output a DuckDB SQL query "
    "inside a ```sql ... ``` code block — nothing else on that turn.\n"
    "2. If you already have query results (provided in the message), interpret "
    "them in plain English. Be concise, friendly and format numbers nicely.\n"
    "3. If the question is purely conversational (no data needed), just answer directly.\n"
    "4. IMPORTANT DuckDB syntax rules:\n"
    "   - For counting missing/null values per column, prefer this pattern:\n"
    "     SELECT 'col1' AS column_name, SUM(CASE WHEN col1 IS NULL THEN 1 ELSE 0 END) AS missing_count FROM uploaded_data\n"
    "     UNION ALL SELECT 'col2', SUM(CASE WHEN col2 IS NULL THEN 1 ELSE 0 END) FROM uploaded_data ...\n"
    "   - Do NOT use UNPIVOT with 'EXCLUDE NULLS' — this is invalid syntax.\n"
    "5. Some numeric-looking columns (e.g. budget, revenue, popularity, runtime, "
    "vote_average, vote_count) may be stored as VARCHAR/TEXT due to messy source data. "
    "ALWAYS wrap numeric aggregate functions (AVG, SUM, MIN, MAX) around these columns "
    "with TRY_CAST(...AS DOUBLE), e.g.: AVG(TRY_CAST(budget AS DOUBLE)). "
    "TRY_CAST returns NULL for values that can't convert instead of raising an error, "
    "so use it defensively on any column that might not be purely numeric."
)

def _extract_sql(text: str):
    """Pull the first ```sql ... ``` block from LLM output."""
    m = re.search(r"```sql\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if m:
        return m.group(1).strip()
    # fallback: bare SELECT
    m2 = re.search(r"(SELECT\s.+)", text, re.DOTALL | re.IGNORECASE)
    return m2.group(1).strip() if m2 else None

# def _run_sql(sql: str, csv_path: str):
#     """Execute SQL against the CSV via DuckDB and return (result_df, error)."""
#     try:
#         con = duckdb.connect()
#         con.execute(
#             f"CREATE OR REPLACE TABLE uploaded_data AS "
#             f"SELECT * FROM read_csv_auto('{csv_path}')"
#         )
#         result = con.execute(sql).df()
#         con.close()
#         return result, None
#     except Exception as e:
#         return None, str(e)

def _run_sql(sql: str, csv_path: str):
    """Execute SQL against the CSV via DuckDB and return (result_df, error)."""
    try:
        con = duckdb.connect()
        con.execute(
            f"CREATE OR REPLACE TABLE uploaded_data AS "
            f"SELECT * FROM read_csv('{csv_path}', ignore_errors=true, "
            f"types={{'popularity': 'VARCHAR', 'budget': 'VARCHAR', 'revenue': 'VARCHAR'}})"
        )
        result = con.execute(sql).df()
        con.close()
        return result, None
    except Exception as e:
        return None, str(e)

# def _chat_with_hf(messages: list) -> str:
#     """Call HuggingFace InferenceClient chat completion."""
#     client = InferenceClient(api_key=HF_API_KEY)
#     resp = client.chat.completions.create(
#         model="meta-llama/Meta-Llama-3-8B-Instruct",
#         messages=messages,
#         max_tokens=1024,
#         temperature=0.3,
#     )
#     return resp.choices[0].message.content.strip()

from groq import Groq
import os

def _chat_with_hf(messages: list) -> str:
    """Call Groq chat completion."""
    client = Groq(api_key=os.getenv("GROQ_API_KEY"))
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=1024,
        temperature=0.3,
    )
    return resp.choices[0].message.content

def answer_question(user_q: str, csv_path: str) -> str:
    """Full pipeline: ask LLM → maybe run SQL → ask LLM to explain."""
    messages = [
        {"role": "system", "content": _SYSTEM},
        {"role": "user",   "content": user_q},
    ]
    first_reply = _chat_with_hf(messages)
    sql = _extract_sql(first_reply)
    if not sql:
        return first_reply  # pure conversational answer

    result_df, err = _run_sql(sql, csv_path)
    if err:
        return f"I tried this SQL:\n```sql\n{sql}\n```\n\nBut got an error: `{err}`"

    result_str = result_df.to_string(index=False)
    messages += [
        {"role": "assistant", "content": first_reply},
        {"role": "user",      "content": f"Query results:\n{result_str}\n\nPlease explain these results clearly."},
    ]
    explanation = _chat_with_hf(messages)
    # return f"{explanation}\n\n---\n*SQL used:*\n```sql\n{sql}\n```"
    return explanation



# with tab3:
#     st.markdown("### 🤖 Ask Anything About Your Data")
#     st.caption("Powered by Meta-Llama-3-8B via HuggingFace Inference API")
with tab3:
    st.markdown("### 🤖 Ask Anything About Your Data")
    st.caption("Powered by Llama-3.3-70B via Groq Inference API")

    if "chat_history" not in st.session_state or st.session_state.get("chat_file") != uploaded_file.name:
        st.session_state.chat_history = []
        st.session_state.chat_file = uploaded_file.name

    # Display history
    # for msg in st.session_state.chat_history:
    #     if msg["role"] == "user":
    #         st.markdown(f"""
    #         <div class="chat-label" style="text-align:right">You</div>
    #         <div class="chat-user">{msg["content"]}</div>
    #         """, unsafe_allow_html=True)
    #     else:
    #         st.markdown(f"""
    #         <div class="chat-label">🤖 AI Analyst</div>
    #         <div class="chat-assistant">{msg["content"]}</div>
    #         """, unsafe_allow_html=True)
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(
                '<div class="chat-label" style="text-align:right">You</div>',
                unsafe_allow_html=True
            )
            st.markdown(
                f'<div class="chat-user">{msg["content"]}</div>',
                unsafe_allow_html=True
            )
        else:
            st.markdown(
                '<div class="chat-label">🤖 AI Analyst</div>',
                unsafe_allow_html=True
            )
            st.markdown(msg["content"])  # normal markdown, no raw div wrapper — renders code blocks properly

    # Suggested starter questions
    if not st.session_state.chat_history:
        st.markdown("**💡 Try asking:**")
        nc0 = df.select_dtypes(include=np.number).columns
        suggestions = [
            f"What are the top 5 values in {columns[0]}?",
            "Give me a summary of this dataset.",
            "Which column has the most missing values?",
            f"What is the average of {nc0[0] if len(nc0) else columns[0]}?",
        ]
        s_cols = st.columns(2)
        for i, s in enumerate(suggestions):
            with s_cols[i % 2]:
                if st.button(s, key=f"sug_{i}"):
                    st.session_state.pending_query = s
                    st.rerun()

    # Handle suggestion button clicks
    if "pending_query" in st.session_state:
        q = st.session_state.pop("pending_query")
        st.session_state.chat_history.append({"role": "user", "content": q})
        with st.spinner("Thinking…"):
            ans = answer_question(q, temp_path)
        st.session_state.chat_history.append({"role": "assistant", "content": ans})
        st.rerun()

    # Chat input form
    with st.form("chat_form", clear_on_submit=True):
        col_inp, col_btn = st.columns([5, 1])
        with col_inp:
            user_query = st.text_input(
                "Ask a question…",
                placeholder="e.g. What is the average sales by category?",
                label_visibility="collapsed",
            )
        with col_btn:
            submitted = st.form_submit_button("Send")

    if submitted and user_query.strip():
        st.session_state.chat_history.append({"role": "user", "content": user_query})
        with st.spinner("Thinking…"):
            ans = answer_question(user_query, temp_path)
        st.session_state.chat_history.append({"role": "assistant", "content": ans})
        st.rerun()

    if st.session_state.chat_history and st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()