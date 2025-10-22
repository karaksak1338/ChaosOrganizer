const API_BASE = import.meta.env.VITE_API_BASE || "https://chaosorganizer-production.up.railway.app";
 
export async function uploadDocument(file) {

  const formData = new FormData();

  formData.append("file", file);
 
  const res = await fetch(`${API_BASE}/api/upload`, {

    method: "POST",

    body: formData

  });

  if (!res.ok) throw new Error(`Upload failed: ${res.statusText}`);

  return await res.json();

}
 
export async function getDocuments() {

  const res = await fetch(`${API_BASE}/api/documents`);

  if (!res.ok) throw new Error("Failed to fetch documents");

  return await res.json();

}

 