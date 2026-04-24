# 📊 AI Data Analysis Agent

> An intelligent, no-code data analysis platform powered by **Qwen2.5-72B** via HuggingFace Inference API — upload any CSV/Excel dataset and instantly get interactive visualizations, statistical profiling, and an AI chatbot that can answer natural language questions about your data.

---

## ✨ Features

### 🗂️ Tab 1 — Dataset Overview
- **Key metrics** at a glance: rows, columns, numeric/categorical count, missing values %, duplicate rows
- **Interactive data preview** (first 50 rows)
- **Descriptive statistics** — mean, std, min, max, quartiles for all columns
- **Column info table** — data type, null count, null %, unique values, sample value per column

### 📈 Tab 2 — Full Visualizations
Auto-generated charts powered by **Plotly**:

| Chart Type | Description |
|---|---|
| Missing Values Bar | Percentage of nulls per column |
| Histograms + Box | Distribution of every numeric column |
| Box Plots | Side-by-side for all numeric columns |
| Correlation Heatmap | Pearson correlation matrix |
| Scatter Matrix | Pairplot of first 5 numeric columns |
| Violin Plots | Distribution shape + outliers |
| Bar Charts | Top-20 value counts for categorical columns |
| Pie Charts | Proportion view for low-cardinality columns |
| Time Series | Auto-detected date columns plotted over time |

### 🤖 Tab 3 — AI Chatbot
- Ask **natural language questions** about your dataset
- Powered by **Qwen/Qwen2.5-72B-Instruct** via HuggingFace Inference API
- Uses **DuckDB** under the hood — the AI writes SQL and runs it against your data
- Suggested starter questions auto-generated from column names
- Full **chat history** within the session
- Clear chat button to start fresh

---

## 🛠️ Tech Stack

| Layer | Technology |
|---|---|
| UI Framework | [Streamlit](https://streamlit.io/) |
| AI Agent | [Agno](https://github.com/agno-agi/agno) |
| LLM | Qwen/Qwen2.5-72B-Instruct via HuggingFace Inference API |
| Query Engine | [DuckDB](https://duckdb.org/) |
| Visualization | [Plotly](https://plotly.com/python/) |
| Data | [Pandas](https://pandas.pydata.org/) + NumPy |
| Secrets | [python-dotenv](https://pypi.org/project/python-dotenv/) |

---

## 🚀 Getting Started

### 1. Clone the repository

```bash
git clone https://github.com/roylaxmikanta/AI-Data-Analysis-Agent.git
cd AI-Data-Analysis-Agent
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Set up your HuggingFace API key

Create a `.env` file in the project root:

```bash
# .env
HF_API_KEY=your_huggingface_api_key_here
```

> 🔑 Get your free API key from [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)  
> ✅ The `.env` file is already listed in `.gitignore` — your key will **never** be committed to Git.

### 4. Run the app

```bash
streamlit run ai_data_analyst.py
```

Open your browser at **http://localhost:8501**

---

## 📁 Project Structure

```
AI-Data-Analysis-Agent/
│
├── ai_data_analyst.py     # Main Streamlit application
├── requirements.txt       # Python dependencies
├── .env                   # 🔒 Your API key (NOT committed to Git)
├── .gitignore             # Ignores .env and other sensitive files
└── README.md              # This file
```

---

## 🔐 Security

- Your HuggingFace API key lives **only** in `.env` on your local machine
- `.env` is excluded from version control via `.gitignore`
- No API key input is shown in the app UI — zero exposure

---

## 📦 Dependencies

```
streamlit>=1.41.1
duckdb>=1.4.1
pandas
numpy==1.26.4
agno>=2.2.10
python-dotenv>=1.0.0
plotly>=5.0.0
ydata-profiling
streamlit-pandas-profiling
huggingface-hub>=1.0.0
```

---

## 🤖 Why Qwen2.5-72B-Instruct?

The HuggingFace free Inference API requires a model that supports **function/tool calling** (needed for DuckDB tool use). After testing:

| Model | Tool Calling | Result |
|---|---|---|
| `meta-llama/Meta-Llama-3-8B-Instruct` | ❌ | Bad request error with tools |
| `Qwen/Qwen2.5-72B-Instruct` | ✅ | Works perfectly |

---

## 🎯 Usage Example

1. **Upload** a CSV or Excel file from the sidebar
2. Go to **🗂️ Dataset Overview** to see stats, data types, and missing values
3. Go to **📈 Visualizations** to explore all auto-generated charts
4. Go to **🤖 AI Chatbot** and ask questions like:
   - *"What are the top 5 categories by revenue?"*
   - *"Which rows have missing values?"*
   - *"Show me the average salary by department."*
   - *"How many unique customers are there?"*

---

## 📸 Screenshots

> Upload your dataset and explore instantly — dark-themed, glassmorphism UI with interactive Plotly charts.

---

## 🤝 Contributing

Pull requests are welcome! For major changes, please open an issue first to discuss what you'd like to change.

---

## 📄 License

[MIT](LICENSE)

---

<p align="center">Made with ❤️ using Streamlit + HuggingFace + DuckDB</p>
