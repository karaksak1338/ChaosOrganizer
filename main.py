
import os, uuid, datetime
from typing import Optional, List
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from supabase import create_client, Client

# --- Environment setup ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "documents")
DEV_USER_ID = os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE. See .env.example.")

supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# --- App setup ---
app = FastAPI(title="ChaosOrganizer API (v0.2 Supabase)", version="0.2")
allow_origins = os.getenv("API_CORS_ORIGINS", "*").split(",")

app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Models ---
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

# --- Helpers ---
def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def get_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or DEV_USER_ID

# --- Endpoints ---
@app.get("/health")
def health():
    return {"status": "ok", "time": now_iso()}

@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...), x_user_id: Optional[str] = Header(default=None, convert_underscores=False)):
    user_id = get_user_id(x_user_id)
    file_ext = os.path.splitext(file.filename)[1]
    unique_name = f"{uuid.uuid4()}{file_ext}"
    path = f"{user_id}/{unique_name}"
    data = await file.read()

    try:
        up = supabase.storage.from_(DOCS_BUCKET).upload(
            path,
            data,
            {
                "content-type": file.content_type or "application/octet-stream",
                "x-upsert": "false"
            }
        )

        if not up or getattr(up, "error", None):
            raise HTTPException(status_code=500, detail=f"Upload failed: {getattr(up.error, 'message', 'unknown error')}")

        public_url = supabase.storage.from_(DOCS_BUCKET).get_public_url(path)
        meta = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "file_name": file.filename,
            "file_url": public_url,
            "created_at": now_iso(),
        }

        res = supabase.table("documents").insert(meta).execute()
        if getattr(res, "error", None):
            raise HTTPException(status_code=500, detail=f"DB insert failed: {getattr(res.error, 'message', 'unknown error')}")

        return {"id": meta["id"], "file_name": file.filename, "file_url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/documents", response_model=List[Document])
def list_documents():
    res = supabase.table("documents").select("*").eq("deleted_at", None).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {getattr(res.error, 'message', 'unknown error')}")
    return res.data or []

@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    res = supabase.table("documents").update({"deleted_at": now_iso()}).eq("id", doc_id).execute()
    if getattr(res, "error", None):
        raise HTTPException(status_code=500, detail=f"Error updating DB: {getattr(res.error, 'message', 'unknown error')}")
    return {"status": "deleted", "id": doc_id}
