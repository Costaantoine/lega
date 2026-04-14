'use client';
import { useState } from 'react';

export default function AddSource() {
  const [url, setUrl] = useState('');
  const [category, setCategory] = useState('plateforme');
  const [region, setRegion] = useState('europe');
  const [status, setStatus] = useState<'idle'|'loading'|'success'|'error'>('idle');
  const [message, setMessage] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setStatus('loading');
    try {
      const res = await fetch('http://76.13.141.221:8002/api/sources/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ url, category, region, added_by: 'dashboard' })
      });
      const data = await res.json();
      if (data.status === 'ok') {
        setStatus('success');
        setMessage('✅ Source ajoutée : ' + data.url);
        setUrl('');
      } else {
        setStatus('error');
        setMessage('⚠️ ' + (data.message || 'Erreur inconnue'));
      }
    } catch (err: any) {
      setStatus('error');
      setMessage('❌ Erreur réseau : ' + (err?.message || err));
    }
  };

  return (
    <div style={{ padding: 16, border: '1px solid #334155', borderRadius: 8, background: '#0f172a' }}>
      <h3 style={{ margin: '0 0 12px', fontWeight: 700, fontSize: 15, color: '#f8fafc' }}>Ajouter une source</h3>
      <form onSubmit={handleSubmit} style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
        <input
          type="url"
          placeholder="https://exemple.com"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          required
          style={{ width: '100%', padding: '8px 10px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#f8fafc', fontSize: 14, boxSizing: 'border-box', outline: 'none' }}
        />
        <div style={{ display: 'flex', gap: 8 }}>
          <select
            value={category}
            onChange={(e) => setCategory(e.target.value)}
            style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#f8fafc', fontSize: 14 }}
          >
            <option value="constructeur">Constructeur</option>
            <option value="loueur">Loueur</option>
            <option value="plateforme">Plateforme</option>
          </select>
          <select
            value={region}
            onChange={(e) => setRegion(e.target.value)}
            style={{ padding: '7px 10px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#f8fafc', fontSize: 14 }}
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
          {status === 'loading' ? '...' : 'Ajouter'}
        </button>
      </form>
      {message && (
        <p style={{ marginTop: 8, fontSize: 13, color: status === 'error' ? '#f87171' : '#4ade80' }}>{message}</p>
      )}
    </div>
  );
}
