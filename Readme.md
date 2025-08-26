# a WISE Website Audit App — Streamlit + Gemini 2.5 Pro

A simple Streamlit app that turns your audit **prompt** into a working tool using **google-generativeai** (Gemini 2.5 Pro). It collects inputs (URL, brand, audience, competitors), sends a structured prompt to Gemini, renders a Markdown audit report, and lets you **download the output as a PDF**.

## Features
- Streamlit UI for quick audits
- Uses **Gemini 2.5 Pro** via `google-generativeai`
- Displays results as Markdown
- **Download PDF** of the audit
- Uses **pandas** to present a compact input/metadata summary


## Tech
- Python 3.10+
- [Streamlit](https://streamlit.io)
- [google-generativeai](https://pypi.org/project/google-generativeai/)
- [pandas](https://pypi.org/project/pandas/)
- [fpdf2](https://pypi.org/project/fpdf2/) (for PDF creation)


## Quickstart


```bash
# 1) Clone and enter the repo
git clone <your-repo-url>.git
cd <your-repo-folder>


# 2) Create and activate a venv (recommended)
python -m venv .venv
# Windows
. .venv/Scripts/activate
# macOS/Linux
source .venv/bin/activate


# 3) Install dependencies
pip install -r requirements.txt


# 4) Add your Google API key (Gemini)
# Option A: Environment variable
# (Windows PowerShell)
$env:GOOGLE_API_KEY="YOUR_API_KEY"
# (macOS/Linux)
export GOOGLE_API_KEY="YOUR_API_KEY"


# Option B: Streamlit secrets
# Create .streamlit/secrets.toml with:
# GOOGLE_API_KEY = "YOUR_API_KEY"


# 5) Run the app
streamlit run app.py
