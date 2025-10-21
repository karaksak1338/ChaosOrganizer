import React, { useEffect, useMemo, useState } from "react";
import { API_BASE, listDocuments, uploadDocument, deleteDocument } from "./api";

export default function App() {
  const [docs, setDocs] = useState([]);
  const [file, setFile] = useState(null);
  const [loading, setLoading] = useState(false);
  const [err, setErr] = useState("");

  const [q, setQ] = useState("");
  const [cat, setCat] = useState("");
  const [typ, setTyp] = useState("");
  const [from, setFrom] = useState("");
  const [to, setTo] = useState("");

  async function refresh() {
    setErr("");
    try {
      const data = await listDocuments();
      setDocs(Array.isArray(data) ? data : []);
    } catch (e) {
      setErr(String(e));
    }
  }

  useEffect(() => { refresh(); }, []);

  const categories = useMemo(() => {
    const set = new Set();
    docs.forEach(d => d.category && set.add(d.category));
    return Array.from(set).sort();
  }, [docs]);

  const types = useMemo(() => {
    const set = new Set();
    docs.forEach(d => d.doc_type && set.add(d.doc_type));
    return Array.from(set).sort();
  }, [docs]);

  const filtered = useMemo(() => {
    const fromTs = from ? Date.parse(from) : null;
    const toTs = to ? Date.parse(to) : null;
    return docs.filter(d => {
      const hay = `${(d.file_name||"")} ${(d.supplier||"")} ${(d.text_content||"")}`.toLowerCase();
      if (q && !hay.includes(q.toLowerCase())) return false;
      if (cat && d.category !== cat) return false;
      if (typ && d.doc_type !== typ) return false;
      const dateStr = d.issue_date || d.created_at || d.uploaded_at;
      const ts = dateStr ? Date.parse(dateStr) : null;
      if (fromTs && (!ts || ts < fromTs)) return false;
      if (toTs && (!ts || ts > (toTs + 24*60*60*1000 - 1))) return false;
      return true;
    });
  }, [docs, q, cat, typ, from, to]);

  async function onUpload(e) {
    e.preventDefault();
    if (!file) return;
    setLoading(true); setErr("");
    try {
      await uploadDocument(file);
      setFile(null);
      await refresh();
    } catch (e) {
      setErr(String(e));
    } finally {
      setLoading(false);
    }
  }

  async function onDelete(id) {
    if (!confirm("Delete this document?")) return;
    setErr("");
    try {
      await deleteDocument(id);
      await refresh();
    } catch (e) {
      setErr(String(e));
    }
  }

  return (
    <div className="page">
      <header className="topbar">
        <div className="brand">
          <svg viewBox="0 0 24 24" width="18" height="18" className="logo" aria-hidden="true">
            <path d="M3 12h18M12 3v18" stroke="currentColor" strokeWidth="2" fill="none" strokeLinecap="round"/>
          </svg>
          <span>ChaosOrganizer</span>
        </div>
        <div className="toolbar">
          <button className="icon-btn" title="Refresh" onClick={refresh}>↻</button>
          <a className="icon-btn" title="API docs" target="_blank" rel="noreferrer" href={`${API_BASE}/docs`}>API</a>
        </div>
      </header>

      <main className="container">
        <section className="panel upload">
          <h2>Upload</h2>
          <form onSubmit={onUpload} className="upload-form">
            <input type="file" onChange={(e)=>setFile(e.target.files?.[0]||null)} />
            <button type="submit" className="primary" disabled={loading || !file}>
              {loading ? "Uploading…" : "Upload"}
            </button>
            <span className="muted small">{API_BASE}</span>
          </form>
          {err && <div className="error">{err}</div>}
        </section>

        <section className="panel filters">
          <h2>Filters</h2>
          <div className="filters-grid">
            <div className="field">
              <label>Search</label>
              <input value={q} onChange={e=>setQ(e.target.value)} placeholder="Filename, supplier, text…" />
            </div>
            <div className="field">
              <label>Category</label>
              <select value={cat} onChange={e=>setCat(e.target.value)}>
                <option value="">All</option>
                {categories.map(c => <option key={c} value={c}>{c}</option>)}
              </select>
            </div>
            <div className="field">
              <label>Doc Type</label>
              <select value={typ} onChange={e=>setTyp(e.target.value)}>
                <option value="">All</option>
                {types.map(t => <option key={t} value={t}>{t}</option>)}
              </select>
            </div>
            <div className="field">
              <label>From</label>
              <input type="date" value={from} onChange={e=>setFrom(e.target.value)} />
            </div>
            <div className="field">
              <label>To</label>
              <input type="date" value={to} onChange={e=>setTo(e.target.value)} />
            </div>
            <div className="field">
              <label>&nbsp;</label>
              <button className="ghost" onClick={() => { setQ(""); setCat(""); setTyp(""); setFrom(""); setTo(""); }}>Clear</button>
            </div>
          </div>
        </section>

        <section className="panel">
          <div className="list-header">
            <h2>Documents ({filtered.length})</h2>
          </div>
          {filtered.length === 0 ? (
            <div className="empty muted">No documents found.</div>
          ) : (
            <ul className="doc-list">
              {filtered.map(d => (
                <li key={d.id} className="doc-item">
                  <div className="doc-main">
                    <a className="doc-name" href={d.file_url} target="_blank" rel="noreferrer">{d.file_name}</a>
                    <div className="doc-meta">
                      <span>{d.category || "—"}</span>
                      <span>•</span>
                      <span>{d.doc_type || "—"}</span>
                      <span>•</span>
                      <span>{(d.issue_date || d.created_at || d.uploaded_at || "").toString().slice(0,10)}</span>
                    </div>
                  </div>
                  <div className="doc-actions">
                    <button className="danger small" onClick={()=>onDelete(d.id)}>Delete</button>
                  </div>
                </li>
              ))}
            </ul>
          )}
        </section>
      </main>
    </div>
  );
}