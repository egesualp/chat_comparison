# Chat Comparison

This simple web app lets you test a prompt against multiple OpenAI chat models and compare the responses side‑by‑side.

## Setup

1. Install dependencies
   ```bash
   pip install -r requirements.txt
   ```
2. Set your OpenAI API key
   ```bash
   export OPENAI_API_KEY=YOUR_KEY
   ```
3. Start the server
   ```bash
   python -m app
   ```
4. Open `frontend/index.html` in your browser.

Runs are stored in the local SQLite database `runs.db`.
