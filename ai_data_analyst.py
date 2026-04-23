import os
import tempfile
import csv
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
from dotenv import load_dotenv
from agno.agent import Agent
from agno.models.huggingface import HuggingFace
from agno.tools.duckdb import DuckDbTools

# ─── Load environment variables ──────────────────────────────────────────────
load_dotenv()
HF_API_KEY = os.getenv("HF_API_KEY")

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
    if HF_API_KEY:
        st.success("✅ HuggingFace API connected")
    else:
        st.error("❌ HF_API_KEY not found in .env")
    st.markdown("---")
    st.markdown("**Model:** meta-llama/Meta-Llama-3-8B-Instruct")
    st.markdown("**Powered by:** HuggingFace Inference API")


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
# TAB 3 – AI Chatbot
# ══════════════════════════════════════════════════════════════════════════════
with tab3:
    st.markdown("### 🤖 Ask Anything About Your Data")
    st.caption("Powered by Meta-Llama-3-8B via HuggingFace Inference API")

    # Initialise DuckDB agent once per file
    if "agent" not in st.session_state or st.session_state.get("agent_file") != uploaded_file.name:
        with st.spinner("Initialising AI agent…"):
            try:
                duckdb_tools = DuckDbTools()
                duckdb_tools.load_local_csv_to_table(
                    path=temp_path,
                    table="uploaded_data",
                )
                dataset_context = (
                    f"Dataset has {df.shape[0]} rows and {df.shape[1]} columns.\n"
                    f"Columns: {', '.join(df.columns.tolist())}\n"
                    f"Numeric columns: {', '.join(df.select_dtypes(include=np.number).columns.tolist())}\n"
                    f"Categorical columns: {', '.join(df.select_dtypes(include=['object']).columns.tolist())}\n"
                    f"Sample head:\n{df.head(3).to_string(index=False)}"
                )
                agent = Agent(
                    model=HuggingFace(
                        id="meta-llama/Meta-Llama-3-8B-Instruct",
                        api_key=HF_API_KEY,
                        max_tokens=1024,
                        temperature=0.3,
                    ),
                    tools=[duckdb_tools],
                    system_message=(
                        "You are an expert data analyst. You have access to a DuckDB table called "
                        "'uploaded_data' which contains the user's dataset.\n\n"
                        f"Dataset info:\n{dataset_context}\n\n"
                        "When the user asks a question, use SQL via DuckDB tools to query the data "
                        "and provide clear, concise answers. Format numbers nicely. Be friendly."
                    ),
                    markdown=True,
                )
                st.session_state.agent = agent
                st.session_state.agent_file = uploaded_file.name
            except Exception as e:
                st.error(f"Failed to initialise agent: {e}")
                st.stop()

    # Chat history display
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    chat_container = st.container()
    with chat_container:
        for msg in st.session_state.chat_history:
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="chat-label" style="text-align:right">You</div>
                <div class="chat-user">{msg["content"]}</div>
                """, unsafe_allow_html=True)
            else:
                st.markdown(f"""
                <div class="chat-label">🤖 AI Analyst</div>
                <div class="chat-assistant">{msg["content"]}</div>
                """, unsafe_allow_html=True)

    # Suggested questions
    if not st.session_state.chat_history:
        st.markdown("**💡 Try asking:**")
        suggestions = [
            f"What are the top 5 values in {columns[0]}?",
            "Give me a summary of this dataset.",
            "Which column has the most missing values?",
            "What is the average of each numeric column?",
        ]
        s_cols = st.columns(2)
        for i, s in enumerate(suggestions):
            with s_cols[i % 2]:
                if st.button(s, key=f"sug_{i}"):
                    st.session_state.pending_query = s
                    st.rerun()

    # Handle pending suggestion clicks
    if "pending_query" in st.session_state:
        query = st.session_state.pop("pending_query")
        st.session_state.chat_history.append({"role": "user", "content": query})
        with st.spinner("Thinking…"):
            try:
                response = st.session_state.agent.run(query)
                answer = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                answer = f"⚠️ Error: {e}"
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    # Chat input
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
            try:
                response = st.session_state.agent.run(user_query)
                answer = response.content if hasattr(response, 'content') else str(response)
            except Exception as e:
                answer = f"⚠️ Error: {e}"
        st.session_state.chat_history.append({"role": "assistant", "content": answer})
        st.rerun()

    if st.session_state.chat_history and st.button("🗑️ Clear Chat"):
        st.session_state.chat_history = []
        st.rerun()