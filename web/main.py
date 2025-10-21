from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from supabase import create_client, Client
from datetime import datetime
from uuid import UUID
import os
 
# === FastAPI app setup ===
app = FastAPI(title="ChaosOrganizer API", version="2.3")
 
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all for now
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
 
# === Environment variables ===
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_ROLE = os.getenv("SUPABASE_SERVICE_ROLE")
DOCS_BUCKET = os.getenv("DOCS_BUCKET", "documents")
DEV_USER_ID = os.getenv("DEV_USER_ID", "00000000-0000-0000-0000-000000000001")
 
if not SUPABASE_URL or not SUPABASE_SERVICE_ROLE:
    raise RuntimeError("Missing SUPABASE_URL or SUPABASE_SERVICE_ROLE. Check Railway variables.")
 
# === Supabase client ===
supabase: Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_ROLE)
 
 
# === Health ===# Upload document
@app.post("/api/upload")
async def upload_document(file: UploadFile = File(...)):
    try:
        timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
        filename = f"{timestamp}_{file.filename}"
        file_bytes = await file.read()

        # ✅ Always store inside user folder
        path_in_bucket = f"{DEV_USER_ID}/{filename}"

        # Upload file to Supabase Storage
        upload_result = supabase.storage.from_(DOCS_BUCKET).upload(path_in_bucket, file_bytes)

        # Check for error response
        if isinstance(upload_result, dict) and "error" in upload_result and upload_result["error"]:
            raise HTTPException(status_code=500, detail=upload_result["error"]["message"])

        # Get public URL
        public_url = supabase.storage.from_(DOCS_BUCKET).get_public_url(path_in_bucket)

        # Insert into documents table
        supabase.table("documents").insert({
            "user_id": DEV_USER_ID,
            "file_name": file.filename,
            "file_url": public_url,
            "uploaded_at": datetime.utcnow().isoformat()
        }).execute()

        return {"detail": f"Uploaded {file.filename}", "url": public_url}

    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

 
 
# === List documents ===
@app.get("/api/documents")
def list_documents():
    try:
        res = supabase.table("documents").select("*").execute()
        if hasattr(res, "data"):
            return res.data
        else:
            return []
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
 
 
# === Delete document ===
@app.delete("/api/documents/{doc_id}")
def delete_document(doc_id: UUID):
    try:
        # Get record
        doc = supabase.table("documents").select("*").eq("id", str(doc_id)).single().execute()
        if not doc.data:
            raise HTTPException(status_code=404, detail="Document not found")
 
        # Extract filename
        file_url = doc.data.get("file_url")
        filename = file_url.split(f"{DOCS_BUCKET}/")[-1]
 
        # Delete file from storage
        supabase.storage.from_(DOCS_BUCKET).remove([filename])
 
        # Delete record
        supabase.table("documents").delete().eq("id", str(doc_id)).execute()
 
        return {"detail": f"Deleted document {doc_id}"}
 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
