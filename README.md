# PromptShield AI 🛡️
Cybersecurity final-year project starter built with **Python FastAPI + React + TypeScript**.

An **educational proof of concept**, not a production-ready security gateway.

## Features
- Explainable rule-based prompt-injection scanner
- Risk scoring: allow, review, block
- Offline protected-chat simulation
- React dashboard with scan history and statistics
- SQLite storage of redacted prompt previews
- Optional offline TF-IDF / Logistic Regression training script
- Python API tests

## Start backend
```bash
cd backend
python -m venv .venv
# Activate the virtual environment
pip install -r requirements.txt
uvicorn app.main:app --reload
```
The API runs at http://localhost:8000 and documentation at http://localhost:8000/docs.

## Start frontend
```bash
cd frontend
npm install
npm run dev
```
Open http://localhost:5173.

## Test
```bash
cd backend
pytest -q
```

## Notes
The MVP scanner is **rules-only** and its chat response is **offline demo text**. The optional ML script trains a baseline separately; it is not yet wired to the API. Never input real secrets. Do not deploy this without authentication, hardening, and comprehensive testing.

Project created for B.Tech CSE final-year educational demonstration.
