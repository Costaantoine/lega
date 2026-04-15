'use client';
import { useState, useEffect } from 'react';

type Source = { id: number; url: string; category: string; region: string; added_by: string; created_at: string };

export default function SourceManager() {
  const [sources, setSources] = useState<Source[]>([]);
  const [form, setForm] = useState({ url: '', category: 'plateforme', region: 'europe' });
  const [status, setStatus] = useState<'idle'|'loading'|'success'|'error'>('idle');
  const [message, setMessage] = useState('');
  const [loadingList, setLoadingList] = useState(true);

  const fetchSources = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    setLoadingList(true);
    try {
      const res = await fetch('http://76.13.141.221:8002/api/sources', { headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      if (Array.isArray(data)) setSources(data);
    } catch (e) { console.error('Fetch sources failed:', e); }
    setLoadingList(false);
  };

  useEffect(() => { fetchSources(); }, []);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    try {
      const tok = localStorage.getItem('bvi_token') || '';
      const res = await fetch('http://76.13.141.221:8002/api/sources/add', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ ...form, added_by: 'dashboard' })
      });
      const data = await res.json();
      if (data.status === 'ok' || data.status === 'warning') {
        setStatus('success');
        setMessage('✅ Source ajoutée');
        setForm({ url: '', category: 'plateforme', region: 'europe' });
        fetchSources();
      } else {
        setStatus('error');
        setMessage('⚠️ ' + (data.message || 'Erreur'));
      }
    } catch (err: any) {
      setStatus('error');
      setMessage('❌ ' + (err?.message || 'Erreur réseau'));
    }
  };

  const handleDelete = async (id: number, url: string) => {
    if (!confirm(`Supprimer cette source ?\n${url}`)) return;
    try {
      const tok = localStorage.getItem('bvi_token') || '';
      const res = await fetch(`http://76.13.141.221:8002/api/sources/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      if (data.status === 'ok') {
        setMessage('🗑️ Source supprimée');
        fetchSources();
      } else {
        setMessage('❌ Erreur: ' + data.message);
      }
    } catch (e: any) {
      setMessage('❌ ' + (e?.message || 'Erreur réseau'));
    }
  };

  return (
    <div style={{ padding: 16, border: '1px solid #334155', borderRadius: 8, background: '#0f172a', display: 'flex', flexDirection: 'column', gap: 16 }}>
      <h3 style={{ margin: 0, fontWeight: 700, fontSize: 16, color: '#f8fafc' }}>Gestion des sources</h3>

      {/* Formulaire d'ajout */}
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10, padding: 12, background: '#1e293b', borderRadius: 8 }}>
        <input
          type="url"
          placeholder="https://exemple.com"
          value={form.url}
          onChange={(e) => setForm({...form, url: e.target.value})}
          required
          style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #334155', background: '#0f172a', color: '#f8fafc', fontSize: 14, boxSizing: 'border-box', outline: 'none' }}
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <select
            value={form.category}
            onChange={(e) => setForm({...form, category: e.target.value})}
            style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid #334155', background: '#0f172a', color: '#f8fafc', fontSize: 14 }}
          >
            <option value="constructeur">Constructeur</option>
            <option value="loueur">Loueur</option>
            <option value="plateforme">Plateforme</option>
          </select>
          <select
            value={form.region}
            onChange={(e) => setForm({...form, region: e.target.value})}
            style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid #334155', background: '#0f172a', color: '#f8fafc', fontSize: 14 }}
          >
            <option value="bordeaux">Bordeaux</option>
            <option value="pt">Portugal</option>
            <option value="europe">Europe</option>
          </select>
        </div>
        <button
          type="submit"
          disabled={status === 'loading'}
          style={{ alignSelf: 'flex-start', padding: '8px 16px', borderRadius: 6, border: 'none', background: '#3b82f6', color: '#fff', cursor: status === 'loading' ? 'not-allowed' : 'pointer', fontSize: 14, fontWeight: 600, opacity: status === 'loading' ? 0.5 : 1 }}
        >
          {status === 'loading' ? '...' : '+ Ajouter'}
        </button>
      </form>

      {message && (
        <p style={{ margin: 0, fontSize: 13, color: status === 'error' ? '#f87171' : '#4ade80' }}>{message}</p>
      )}

      {/* Liste des sources */}
      <div>
        <h4 style={{ margin: '0 0 8px', fontWeight: 600, fontSize: 14, color: '#cbd5e1' }}>Sources actives ({sources.length})</h4>
        {loadingList ? (
          <p style={{ color: '#64748b', fontSize: 13 }}>Chargement...</p>
        ) : (
          <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'flex', flexDirection: 'column', gap: 6, maxHeight: 280, overflowY: 'auto' }}>
            {sources.map(s => (
              <li key={s.id} style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '8px 10px', background: '#1e293b', borderRadius: 6, fontSize: 13 }}>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <a href={s.url} target="_blank" rel="noopener" style={{ color: '#60a5fa', textDecoration: 'none', display: 'block', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                    {s.url}
                  </a>
                  <span style={{ fontSize: 11, color: '#64748b' }}>{s.category} • {s.region} • {s.added_by}</span>
                </div>
                <button
                  onClick={() => handleDelete(s.id, s.url)}
                  style={{ marginLeft: 10, padding: '4px 8px', background: '#450a0a', color: '#f87171', border: '1px solid #7f1d1d', borderRadius: 4, cursor: 'pointer', fontSize: 13, flexShrink: 0 }}
                >
                  🗑️
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  );
}
