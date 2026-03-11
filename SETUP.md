# MARS — First-Time Setup Guide
> Follow these steps in order to get the app running.

---

## Step 1 — Install Python 3.11+

1. Go to: https://www.python.org/downloads/
2. Download **Python 3.11** or newer (click "Download Python 3.x.x")
3. Run the installer — **check the box "Add Python to PATH"** before clicking Install
4. Verify: open a new terminal and run:
   ```
   python --version
   ```
   You should see: `Python 3.11.x`

---

## Step 2 — Open Terminal in This Folder

1. Open **Windows Explorer**
2. Navigate to: `Desktop > Project MK-1 > eve`
3. Click the address bar, type `powershell`, press Enter

---

## Step 3 — Create Virtual Environment

```powershell
python -m venv .venv
.venv\Scripts\activate
```

Your terminal should now show `(.venv)` at the start.

---

## Step 4 — Install Dependencies

```powershell
pip install -r requirements.txt
```

This takes 2–5 minutes. Then install Playwright browsers (for JS-heavy pages):
```powershell
playwright install chromium
```

---

## Step 5 — Add Your API Keys

1. Copy the example file:
   ```powershell
   copy .env.example .env
   ```
2. Open `.env` in Notepad or VS Code
3. Fill in your keys:
   - **GROQ_API_KEY** → Get free at: https://console.groq.com/
   - **TAVILY_API_KEY** → Get free at: https://app.tavily.com/ (1,000 calls/month free)
   - **LANGCHAIN_API_KEY** → Get free at: https://smith.langchain.com/ (for tracing, optional)

---

## Step 6 — Run the App

```powershell
streamlit run app.py
```

Open your browser at: **http://localhost:8501**

---

## Step 7 — Run Tests (optional)

```powershell
python tests/test_pipeline.py
```

---

## Deploying to Streamlit Cloud (free public URL)

1. Create a GitHub repo and push this folder
2. Go to: https://share.streamlit.io
3. Connect your GitHub repo → select `app.py`
4. Under **Secrets**, add: `GROQ_API_KEY`, `TAVILY_API_KEY`, `LANGCHAIN_API_KEY`
5. Click Deploy — your public URL appears in ~60 seconds

---

## Getting API Keys (All Free)

| Key | URL | Free Tier |
|---|---|---|
| GROQ_API_KEY | https://console.groq.com/ | 30 RPM, 14,400 req/day |
| TAVILY_API_KEY | https://app.tavily.com/ | 1,000 searches/month |
| LANGCHAIN_API_KEY | https://smith.langchain.com/ | Free tracing tier |
