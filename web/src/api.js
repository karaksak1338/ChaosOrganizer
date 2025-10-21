export const API_BASE = import.meta.env.VITE_API_BASE || "https://chaosorganizer-production.up.railway.app";

export async function listDocuments() {
  const res = await fetch(`${API_BASE}/api/documents`);
  if (!res.ok) throw new Error(`GET /api/documents -> ${res.status}`);
  return await res.json();
}

export async function uploadDocument(file) {
  const form = new FormData();
  form.append("file", file);
  const res = await fetch(`${API_BASE}/api/upload`, { method: "POST", body: form });
  if (!res.ok) throw new Error(await res.text());
  return await res.json();
}

export async function deleteDocument(id) {
  const res = await fetch(`${API_BASE}/api/documents/${id}`, { method: "DELETE" });
  if (!res.ok) throw new Error(`DELETE failed: ${res.status}`);
  return await res.json();
}