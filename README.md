# ChaosOrganizer 📄

A private document manager with AI-powered categorization and Supabase storage.

## 🧱 Architecture
- **Backend:** FastAPI (Python)
- **Storage & DB:** Supabase
- **Frontend:** iOS (SwiftUI) + optional Web UI (React)
- **Auth:** Supabase JWT (planned for v0.3)

## 🚀 Local Setup
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env  # fill with your Supabase keys
uvicorn main:app --reload --port 8000
```

## 🌍 Deployment (Railway)
```bash
railway init
railway variables set SUPABASE_URL=... SUPABASE_SERVICE_ROLE=... ...
railway up
```

## 🧩 API Endpoints
- `GET /health` — check status
- `POST /api/upload` — upload document
- `GET /api/documents` — list active documents
- `DELETE /api/documents/{id}` — soft delete

## 📦 Future Features
- AI document parsing (OCR + classification)
- Tag-based search
- Multi-user mode
- Web dashboard
