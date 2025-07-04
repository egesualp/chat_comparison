# Chat Comparison

This web app lets you test a prompt against multiple OpenAI chat models and compare their responses side by side.

## Setup

1. Install dependencies (includes `greenlet` required by SQLAlchemy)
   ```bash
   pip install -r requirements.txt
   ```
2. Run the app
   ```bash
   streamlit run app/streamlit_app.py
   ```
3. Enter your OpenAI API key in the UI when prompted.

Runs are stored in the local SQLite database `runs.db`.
