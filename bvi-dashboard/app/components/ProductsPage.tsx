'use client';
import { useState, useEffect, useRef } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';
const API_BASE = API.replace('/api', '');

const STATUS_COLORS: any = { draft: '#64748b', pending: '#fb923c', published: '#4ade80', archived: '#374151' };
const STATUS_LABELS: any = { draft: 'Brouillon', pending: '⏳ En attente', published: '✅ Publié', archived: '🗄 Archivé' };

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

const input: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 14, boxSizing: 'border-box',
};

export default function ProductsPage() {
  const [products, setProducts] = useState<any[]>([]);
  const [filterStatus, setFilterStatus] = useState('all');
  const [selected, setSelected] = useState<any>(null);
  const [showNew, setShowNew] = useState(false);
  const [newForm, setNewForm] = useState({ title: '', description: '', price: '', currency: '€', category: 'tp', status: 'draft' });
  const [uploading, setUploading] = useState(false);
  const [msg, setMsg] = useState('');
  const fileRef = useRef<HTMLInputElement>(null);

  const fetchProducts = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const url = filterStatus === 'all' ? `${API}/products?limit=100` : `${API}/products?status=${filterStatus}&limit=100`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      if (Array.isArray(data)) setProducts(data);
    } catch { }
  };

  useEffect(() => { fetchProducts(); }, [filterStatus]);

  const setStatus = async (id: number, status: string) => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      await fetch(`${API}/products/${id}/status`, {
        method: 'PATCH',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ status }),
      });
      setMsg(`✅ Statut mis à jour → ${STATUS_LABELS[status]}`);
      fetchProducts();
      if (selected?.id === id) setSelected((p: any) => ({ ...p, status }));
    } catch { setMsg('❌ Erreur'); }
    setTimeout(() => setMsg(''), 3000);
  };

  const createProduct = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const res = await fetch(`${API}/products`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ ...newForm, price: parseFloat(newForm.price) || 0, attributes: {}, images: [] }),
      });
      const d = await res.json();
      if (d.status === 'ok') {
        setMsg(`✅ Produit créé (#${d.id})`);
        setShowNew(false);
        setNewForm({ title: '', description: '', price: '', currency: '€', category: 'tp', status: 'draft' });
        fetchProducts();
      }
    } catch { setMsg('❌ Erreur création'); }
    setTimeout(() => setMsg(''), 3000);
  };

  const uploadImage = async (productId: number) => {
    const file = fileRef.current?.files?.[0];
    if (!file) return;
    setUploading(true);
    const fd = new FormData();
    fd.append('file', file);
    try {
      const tok = localStorage.getItem('bvi_token') || '';
      const res = await fetch(`${API}/products/${productId}/upload`, { method: 'POST', body: fd, headers: { Authorization: `Bearer ${tok}` } });
      const d = await res.json();
      if (d.status === 'ok') {
        setMsg('📷 Image uploadée');
        fetchProducts();
      } else { setMsg('⚠️ ' + d.message); }
    } catch { setMsg('❌ Erreur upload'); }
    setUploading(false);
    setTimeout(() => setMsg(''), 3000);
  };

  const archiveProduct = async (id: number) => {
    if (!confirm('Archiver ce produit ?')) return;
    const tok = localStorage.getItem('bvi_token') || '';
    await fetch(`${API}/products/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${tok}` } });
    fetchProducts();
    if (selected?.id === id) setSelected(null);
  };

  const allStatuses = ['all', 'draft', 'pending', 'published', 'archived'];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>📦 Catalogue Produits</h2>
        <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {allStatuses.map(s => (
            <button key={s} onClick={() => setFilterStatus(s)}
              style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                borderColor: filterStatus === s ? (STATUS_COLORS[s] || '#60a5fa') : '#334155',
                background: filterStatus === s ? ((STATUS_COLORS[s] || '#60a5fa') + '22') : '#1e293b',
                color: filterStatus === s ? (STATUS_COLORS[s] || '#60a5fa') : '#94a3b8' }}>
              {s === 'all' ? 'Tout' : STATUS_LABELS[s]}
            </button>
          ))}
          <button onClick={() => setShowNew(true)} style={{ padding: '5px 14px', borderRadius: 6, border: 'none', background: '#3b82f6', color: '#fff', cursor: 'pointer', fontSize: 12, fontWeight: 600 }}>+ Nouveau</button>
          <button onClick={fetchProducts} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: 12 }}>🔄</button>
        </div>
      </div>

      {msg && <div style={{ marginBottom: 14, padding: '8px 14px', background: '#1e293b', borderRadius: 8, color: '#4ade80', fontSize: 13 }}>{msg}</div>}

      {/* New product form */}
      {showNew && (
        <div style={{ background: '#1e293b', border: '1px solid #3b82f6', borderRadius: 12, padding: 16, marginBottom: 16 }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <strong>+ Nouveau produit</strong>
            <button onClick={() => setShowNew(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 16 }}>✕</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            <input style={input} placeholder="Titre *" value={newForm.title} onChange={e => setNewForm(p => ({ ...p, title: e.target.value }))} />
            <textarea style={{ ...input, minHeight: 70, resize: 'vertical' }} placeholder="Description" value={newForm.description} onChange={e => setNewForm(p => ({ ...p, description: e.target.value }))} />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr 1fr', gap: 10 }}>
              <input style={input} type="number" placeholder="Prix" value={newForm.price} onChange={e => setNewForm(p => ({ ...p, price: e.target.value }))} />
              <select style={input} value={newForm.currency} onChange={e => setNewForm(p => ({ ...p, currency: e.target.value }))}>
                <option value="€">€</option>
              </select>
              <select style={input} value={newForm.category} onChange={e => setNewForm(p => ({ ...p, category: e.target.value }))}>
                <option value="tp">TP</option>
                <option value="autre">Autre</option>
              </select>
            </div>
            <div style={{ display: 'flex', gap: 10 }}>
              <select style={{ ...input, flex: 1 }} value={newForm.status} onChange={e => setNewForm(p => ({ ...p, status: e.target.value }))}>
                <option value="draft">Brouillon</option>
                <option value="pending">En attente validation</option>
                <option value="published">Publié</option>
              </select>
              <button onClick={createProduct} disabled={!newForm.title} style={{ padding: '8px 20px', borderRadius: 7, border: 'none', background: '#3b82f6', color: '#fff', cursor: 'pointer', fontWeight: 600 }}>Créer</button>
            </div>
          </div>
        </div>
      )}

      {/* Product list */}
      <div style={{ display: 'flex', gap: 16 }}>
        <div style={{ flex: 1 }}>
          {products.length === 0 ? (
            <div style={{ textAlign: 'center', padding: 40, color: '#475569' }}>Aucun produit</div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
              {products.map(p => {
                const images = typeof p.images === 'string' ? JSON.parse(p.images || '[]') : (p.images || []);
                return (
                  <div key={p.id} onClick={() => setSelected(p)}
                    style={{ background: selected?.id === p.id ? '#1e3a5f' : '#1e293b', border: `1px solid ${selected?.id === p.id ? '#3b82f6' : '#334155'}`, borderRadius: 8, padding: '10px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 12 }}>
                    {images[0] ? (
                      <img src={`${API_BASE}${images[0]}`} style={{ width: 48, height: 48, objectFit: 'cover', borderRadius: 6, flexShrink: 0 }} alt="" />
                    ) : (
                      <div style={{ width: 48, height: 48, borderRadius: 6, background: '#0f172a', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#475569', flexShrink: 0 }}>🚜</div>
                    )}
                    <div style={{ flex: 1, minWidth: 0 }}>
                      <div style={{ fontWeight: 600, fontSize: 14, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</div>
                      <div style={{ fontSize: 12, color: '#64748b' }}>{p.price ? `${p.price} ${p.currency}` : '—'} · {p.category?.toUpperCase()}</div>
                    </div>
                    <span style={badge(STATUS_COLORS[p.status] || '#64748b')}>{STATUS_LABELS[p.status] || p.status}</span>
                  </div>
                );
              })}
            </div>
          )}
        </div>

        {/* Detail panel */}
        {selected && (
          <div style={{ width: 340, background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 16, flexShrink: 0, overflowY: 'auto', maxHeight: 'calc(100vh - 100px)' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
              <strong style={{ fontSize: 14 }}>#{selected.id} · {selected.title}</strong>
              <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 16 }}>✕</button>
            </div>
            {/* Images */}
            {(() => {
              const imgs: string[] = typeof selected.images === 'string' ? JSON.parse(selected.images || '[]') : (selected.images || []);
              return imgs.length > 0 ? (
                <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: 6, marginBottom: 12 }}>
                  {imgs.map((url, i) => (
                    <img key={i} src={`${API_BASE}${url}`} style={{ width: '100%', aspectRatio: '1', objectFit: 'cover', borderRadius: 6 }} alt="" />
                  ))}
                </div>
              ) : null;
            })()}
            {/* Upload */}
            <div style={{ marginBottom: 12, padding: '10px 12px', background: '#0f172a', borderRadius: 8 }}>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 6 }}>📷 Ajouter une photo</div>
              <input ref={fileRef} type="file" accept="image/*" style={{ fontSize: 12, color: '#94a3b8', width: '100%' }} />
              <button onClick={() => uploadImage(selected.id)} disabled={uploading}
                style={{ marginTop: 6, padding: '5px 12px', borderRadius: 6, border: 'none', background: '#3b82f6', color: '#fff', cursor: 'pointer', fontSize: 12, opacity: uploading ? 0.5 : 1 }}>
                {uploading ? 'Upload...' : 'Uploader'}
              </button>
            </div>
            {/* Info */}
            <div style={{ display: 'flex', flexDirection: 'column', gap: 8, fontSize: 13 }}>
              <div><span style={{ color: '#64748b' }}>Prix :</span> <b>{selected.price} {selected.currency}</b></div>
              <div><span style={{ color: '#64748b' }}>Catégorie :</span> {selected.category}</div>
              <div><span style={{ color: '#64748b' }}>Statut :</span> <span style={badge(STATUS_COLORS[selected.status])}>{STATUS_LABELS[selected.status]}</span></div>
              {selected.description && <div style={{ color: '#94a3b8', fontSize: 12, lineHeight: 1.5 }}>{selected.description}</div>}
            </div>
            {/* Workflow actions */}
            <div style={{ marginTop: 14, display: 'flex', flexDirection: 'column', gap: 8 }}>
              <div style={{ fontSize: 12, color: '#64748b', marginBottom: 2 }}>Actions :</div>
              {selected.status === 'draft' && (
                <button onClick={() => setStatus(selected.id, 'pending')} style={{ padding: '7px', borderRadius: 7, border: 'none', background: '#fb923c22', color: '#fb923c', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
                  → Soumettre pour validation
                </button>
              )}
              {(selected.status === 'draft' || selected.status === 'pending') && (
                <button onClick={() => setStatus(selected.id, 'published')} style={{ padding: '7px', borderRadius: 7, border: 'none', background: '#4ade8022', color: '#4ade80', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}>
                  ✅ Publier directement
                </button>
              )}
              {selected.status === 'published' && (
                <button onClick={() => setStatus(selected.id, 'draft')} style={{ padding: '7px', borderRadius: 7, border: 'none', background: '#64748b22', color: '#94a3b8', cursor: 'pointer', fontSize: 13 }}>
                  ← Dépublier (retour brouillon)
                </button>
              )}
              {selected.status !== 'archived' && (
                <button onClick={() => archiveProduct(selected.id)} style={{ padding: '7px', borderRadius: 7, border: 'none', background: '#f8717122', color: '#f87171', cursor: 'pointer', fontSize: 13 }}>
                  🗄 Archiver
                </button>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
