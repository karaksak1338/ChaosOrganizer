import os
import uuid
import datetime
from typing import Optional
from fastapi import FastAPI, UploadFile, File, HTTPException, Header
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client

# --- Environment Variables ---
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "documents")
DEV_USER_ID = os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001")

if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE. Check Railway Variables.")

# --- Supabase Client ---
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)

# --- App Init ---
app = FastAPI(title="ChaosOrganizer API (v2.3)", version="0.3")

# --- CORS ---
allow_origins = os.getenv("API_CORS_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allow_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Helpers ---
def now_iso():
    return datetime.datetime.utcnow().replace(microsecond=0).isoformat() + "Z"

def get_user_id(x_user_id: Optional[str]) -> str:
    return x_user_id or DEV_USER_ID


# --- Health Endpoint ---
@app.get("/health")
def health():
    return {"status": "ok", "time": now_iso(), "supabase_url": SUPABASE_URL}


# --- Upload Document ---
@app.post("/api/upload")
async def upload_document(
    file: UploadFile = File(...),
    x_user_id: Optional[str] = Header(default=None, convert_underscores=False)
):
    user_id = get_user_id(x_user_id)
    file_ext = file.filename.split(".")[-1]
    unique_name = f"{uuid.uuid4()}.{file_ext}"

    try:
        # Upload to Supabase Storage
        res = supabase.storage.from_(DOCS_BUCKET).upload(unique_name, file.file)
        if res.get("error"):
            raise Exception(res["error"]["message"])

        # Get public URL
        public_url = supabase.storage.from_(DOCS_BUCKET).get_public_url(unique_name)

        # Insert record into 'documents'
        record = {
            "id": str(uuid.uuid4()),
            "user_id": user_id,
            "file_name": file.filename,
            "file_url": public_url,
            "created_at": now_iso(),
        }
        supabase.table("documents").insert(record).execute()
        return {"message": "File uploaded successfully", "record": record}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


# --- List Documents ---
@app.get("/api/documents")
def list_documents():
    try:
        res = supabase.table("documents").select("*").execute()
        print("📄 [DEBUG] Supabase returned:", res.data)
        if not res.data:
            return {"message": "No documents found", "data": []}
        return res.data
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching documents: {e}")


# --- Delete Document ---
@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: str):
    try:
        res = supabase.table("documents").delete().eq("id", doc_id).execute()
        print(f"🗑️ [DEBUG] Deleted document: {doc_id}")
        return {"message": "Deleted successfully", "deleted_id": doc_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting document: {e}")
