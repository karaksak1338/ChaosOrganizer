# ChaosOrganizer 📄

A private document manager with AI-powered categorization and Supabase storage.

## 🧱 Architecture
- **Backend:** FastAPI (Python)
- **Storage & DB:** Supabase
- **Frontend:** iOS (SwiftUI) + optional Web UI (React)
- **Auth:** Supabase JWT (planned for v0.3)

## 🚀 Local Setup
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # then fill values
uvicorn main:app --reload --port 8000
