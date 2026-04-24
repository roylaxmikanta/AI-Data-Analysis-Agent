<div align="center">

# 📊 AI Data Analysis Agent

### Upload any dataset. Get instant insights, beautiful visualizations, and AI-powered answers — all for free.

[![Python](https://img.shields.io/badge/Python-3.10%2B-3776AB?style=for-the-badge&logo=python&logoColor=white)](https://python.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.41%2B-FF4B4B?style=for-the-badge&logo=streamlit&logoColor=white)](https://streamlit.io)
[![HuggingFace](https://img.shields.io/badge/HuggingFace-LLaMA--3--8B-FFD21E?style=for-the-badge&logo=huggingface&logoColor=black)](https://huggingface.co)
[![DuckDB](https://img.shields.io/badge/DuckDB-1.4%2B-FFF000?style=for-the-badge&logo=duckdb&logoColor=black)](https://duckdb.org)
[![Plotly](https://img.shields.io/badge/Plotly-Interactive-3F4F75?style=for-the-badge&logo=plotly&logoColor=white)](https://plotly.com)
[![License: MIT](https://img.shields.io/badge/License-MIT-22C55E?style=for-the-badge)](LICENSE)

<br/>

> **No paid API. No coding required. Just upload and explore.**

</div>

---

## 🌟 What Is This?

**AI Data Analysis Agent** is a fully local, free-to-use data exploration platform built with Streamlit. Upload a CSV or Excel file and get:

- 📋 **Instant dataset overview** with smart statistics
- 📈 **15+ interactive charts** auto-generated from your data
- 🤖 **An AI chatbot** that understands your data and answers questions in plain English — powered by Meta LLaMA 3 via HuggingFace

No OpenAI key. No monthly bill. Just drop in your HuggingFace free API key and go.

---

## 🖥️ Demo

<div align="center">

| Tab 1 — Dataset Overview | Tab 2 — Visualizations | Tab 3 — AI Chatbot |
|:---:|:---:|:---:|
| Metrics, data preview, column info, descriptive stats | 15+ interactive Plotly charts | Natural language Q&A over your data |

</div>

---

## ✨ Features

### 🗂️ Tab 1 · Dataset Overview
| Feature | Description |
|---|---|
| **Key Metric Cards** | Rows, columns, numeric count, missing %, duplicate rows |
| **Data Preview** | First 50 rows in an interactive sortable table |
| **Descriptive Statistics** | Mean, std, min, max, quartiles for all columns |
| **Column Info Table** | Data type, null count, null%, unique values, sample value |

### 📈 Tab 2 · Visualizations (15 Chart Types)
| # | Chart | When shown |
|---|---|---|
| 1 | **Missing Values Bar** | Always |
| 2 | **Histograms + Marginal Box** | Numeric columns |
| 3 | **Box Plots** | Numeric columns |
| 4 | **Correlation Heatmap** | ≥ 2 numeric cols |
| 5 | **Scatter Matrix (Pairplot)** | ≥ 2 numeric cols |
| 6 | **Violin Plots** | Numeric columns |
| 7 | **Value Count Bar Charts** | Categorical columns |
| 8 | **Pie Charts** | Low-cardinality categoricals (≤10 unique) |
| 9 | **Time Series Line Charts** | Date-type columns |
| 10 | **ECDF (Cumulative Distribution)** | Numeric columns |
| 11 | **Bubble Chart** | ≥ 3 numeric cols |
| 12 | **Treemap** | Cat + numeric columns |
| 13 | **Sunburst Chart** | ≥ 2 categorical cols |
| 14 | **Funnel Chart** | Categorical columns |
| 15 | **Grouped Bar Chart** | Cat + ≥ 2 numeric cols |
| 16 | **Pivot Heatmap** | Cat + numeric columns |

### 🤖 Tab 3 · AI Chatbot
- Ask questions in **plain English** — e.g. *"What is the average revenue by region?"*
- The AI writes **DuckDB SQL**, runs it locally, then explains the results in friendly language
- Shows the **SQL query used** for full transparency
- **Suggested starter questions** based on your columns
- Persistent **chat history** within a session with a clear button
- Works 100% on **HuggingFace free tier** — no paid API needed

---

## 🛠️ Tech Stack

| Layer | Technology | Purpose |
|---|---|---|
| **UI** | [Streamlit](https://streamlit.io) | Web interface & interactivity |
| **AI / LLM** | [Meta LLaMA 3 8B Instruct](https://huggingface.co/meta-llama/Meta-Llama-3-8B-Instruct) | Natural language understanding & SQL generation |
| **AI Client** | [huggingface-hub InferenceClient](https://huggingface.co/docs/huggingface_hub) | Free serverless LLM inference |
| **Query Engine** | [DuckDB](https://duckdb.org) | In-process SQL execution on CSV data |
| **Visualization** | [Plotly](https://plotly.com/python) | 15+ interactive chart types |
| **Data** | [Pandas](https://pandas.pydata.org) + [NumPy](https://numpy.org) | Data loading & processing |
| **Secrets** | [python-dotenv](https://pypi.org/project/python-dotenv) | Secure `.env`-based API key loading |

---

## 🚀 Getting Started

### Prerequisites
- Python 3.10 or higher
- A free [HuggingFace account](https://huggingface.co/join)

### 1 · Clone the repository

```bash
git clone https://github.com/roylaxmikanta/AI-Data-Analysis-Agent.git
cd AI-Data-Analysis-Agent
```

### 2 · Install dependencies

```bash
pip install -r requirements.txt
```

### 3 · Create your `.env` file

In the project root, create a file named `.env`:

```env
HF_API_KEY=your_huggingface_api_key_here
```

> 🔑 **Get a free key →** [huggingface.co/settings/tokens](https://huggingface.co/settings/tokens)  
> Select **"Read"** access — that's all you need.

> ✅ `.env` is already in `.gitignore`. Your key will **never** be committed to Git.

### 4 · Run the app

```bash
streamlit run ai_data_analyst.py
```

Open your browser at **[http://localhost:8501](http://localhost:8501)** 🎉

---

## 📁 Project Structure

```
AI-Data-Analysis-Agent/
│
├── 📄 ai_data_analyst.py    ← Main Streamlit application (all logic)
├── 📄 requirements.txt      ← Python dependencies
├── 🔒 .env                  ← Your API key (NOT committed to Git)
├── 📄 .gitignore            ← Excludes .env and other sensitive files
└── 📄 README.md             ← You are here
```

---

## 🔐 Security & Privacy

| Concern | How it's handled |
|---|---|
| **API Key exposure** | Loaded from `.env` at runtime, never shown in UI |
| **Git safety** | `.env` excluded from version control via `.gitignore` |
| **Data privacy** | Your uploaded file stays **100% local** — saved to a temp file, never sent to any server |
| **LLM calls** | Only the column schema + sample rows are sent to HuggingFace for context |

---

## 💡 How the AI Chatbot Works

The chatbot uses a **tool-free 3-step pipeline** that works on HuggingFace's free tier:

```
┌─────────────────────────────────────────────────────────┐
│  User asks a question in natural language               │
│         ↓                                               │
│  LLaMA-3-8B generates a DuckDB SQL query                │
│         ↓                                               │
│  SQL runs locally on your data via DuckDB (0 ms)        │
│         ↓                                               │
│  LLaMA-3-8B explains the result in plain English        │
│         ↓                                               │
│  User sees: explanation + SQL used for transparency     │
└─────────────────────────────────────────────────────────┘
```

> No tool-calling API is needed. The LLM just writes SQL as text, which we parse and execute ourselves.

---

## 📦 Dependencies

```
streamlit>=1.41.1        # Web UI framework
duckdb>=1.4.1            # In-process SQL engine
pandas                   # Data loading and manipulation
numpy==1.26.4            # Numerical computing
plotly>=5.0.0            # Interactive visualizations
python-dotenv>=1.0.0     # .env file loading
huggingface-hub>=1.0.0   # HuggingFace Inference API client
ydata-profiling          # Advanced profiling utilities
streamlit-pandas-profiling  # Streamlit integration
```

---

## 🎯 Example Questions to Ask the Chatbot

```
"What are the top 5 products by sales?"
"How many rows have missing values?"
"What is the average age grouped by gender?"
"Show me the minimum and maximum salary."
"Which category appears most frequently?"
"How many unique customers are there?"
"What is the total revenue by region?"
```

---

## 🤝 Contributing

Contributions are welcome! Here's how:

1. **Fork** the repository
2. **Create** a feature branch: `git checkout -b feature/your-feature`
3. **Commit** your changes: `git commit -m 'feat: add something awesome'`
4. **Push** to the branch: `git push origin feature/your-feature`
5. **Open** a Pull Request

Please open an issue first for major changes to discuss the approach.

---

## 📄 License

This project is licensed under the [MIT License](LICENSE) — free to use, modify and distribute.

---

## 👨‍💻 Author

**Laxmikanta Roy**  
[![GitHub](https://img.shields.io/badge/GitHub-roylaxmikanta-181717?style=flat-square&logo=github)](https://github.com/roylaxmikanta)

---

<div align="center">

**⭐ Star this repo if you found it useful!**

*Built with ❤️ using Streamlit · HuggingFace · DuckDB · Plotly*

</div>
