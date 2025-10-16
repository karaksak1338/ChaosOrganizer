import os
import uuid
import datetime
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# === Environment Variables ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "documents")
DEV_USER_ID = os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE. See .env.example.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# === FastAPI App ===
app = FastAPI(title="ChaosOrganizer API (v2.1)", version="0.2")

allow_origins = os.getenv("API_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# === Models ===
class Document(BaseModel):
    id: str
    user_id: str
    file_name: str
    file_url: str
    category: Optional[str] = None
    doc_type: Optional[str] = None
    supplier: Optional[str] = None
    issue_date: Optional[str] = None
    amount: Optional[float] = None
    ai_confidence: Optional[float] = None
    text_content: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    deleted_at: Optional[str] = None

# === Helper ===
def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def get_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or DEV_USER_ID

# === Routes ===
@app.get("/health")
def health():
    return {"status": "ok", "time": now_iso()}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), x_user_id: Optional[str] = Header(default=None, convert_underscores=False)):
    try:
        user_id = get_user_id(x_user_id)
        filename = f"{uuid.uuid4()}_{file.filename}"
        data = await file.read()
        path = f"{user_id}/{filename}"

        # Upload file to Supabase storage
        up = supabase.storage.from_(DOCS_BUCKET).upload(
            path,
            data,
            {"content-type": file.content_type or "application/octet-stream", "x-upsert": "false"},
        )

        # Retrieve public URL
        public_url = supabase.storage.from_(DOCS_BUCKET).get_public_url(path)

        # Insert metadata
        doc = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "file_name": file.filename,
            "file_url": public_url,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "deleted_at": None,
        }
        supabase.table("documents").insert(doc).execute()

        return {"message": "Upload successful", "document": doc}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents", response_model=List[Document])
def list_documents():
    try:
        res = supabase.table("documents").select("*").is_("deleted_at", "null").execute()
        if getattr(res, "error", None):
            raise HTTPException(status_code=500, detail=f"Error fetching documents: {getattr(res.error, 'message', 'unknown error')}")
        return res.data or []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    try:
        now = datetime.datetime.utcnow().isoformat() + "Z"
        supabase.table("documents").update({"deleted_at": now}).eq("id", doc_id).execute()
        return {"message": f"Document {doc_id} marked as deleted"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
