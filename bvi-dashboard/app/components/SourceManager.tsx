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
    setLoadingList(true);
    try {
      const res = await fetch('http://76.13.141.221:8002/api/sources');
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
      const res = await fetch('http://76.13.141.221:8002/api/sources/add', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({ ...form, added_by: 'dashboard' })
      });
      const data = await res.json();
      if (data.status === 'ok' || data.status === 'warning') {
        setStatus('success');
        setMessage('✅ Source ajoutée');
        setForm({ url: '', category: 'plateforme', region: 'europe' });
        fetchSources(); // Refresh list
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
      const res = await fetch(`http://76.13.141.221:8002/api/sources/${id}`, { method: 'DELETE' });
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
    <div className="p-4 border rounded-lg bg-white dark:bg-gray-800 space-y-4">
      <h3 className="font-bold text-lg">Gestion des sources</h3>
      
      {/* Formulaire d'ajout */}
      <form onSubmit={handleSubmit} className="space-y-3 p-3 bg-gray-50 dark:bg-gray-700 rounded">
        <input type="url" placeholder="https://exemple.com" value={form.url} 
          onChange={(e) => setForm({...form, url: e.target.value})} required
          className="w-full p-2 border rounded dark:bg-gray-600"/>
        <div className="flex gap-2">
          <select value={form.category} onChange={(e) => setForm({...form, category: e.target.value})}
            className="p-2 border rounded dark:bg-gray-600">
            <option value="constructeur">Constructeur</option>
            <option value="loueur">Loueur</option>
            <option value="plateforme">Plateforme</option>
          </select>
          <select value={form.region} onChange={(e) => setForm({...form, region: e.target.value})}
            className="p-2 border rounded dark:bg-gray-600">
            <option value="bordeaux">Bordeaux</option>
            <option value="pt">Portugal</option>
            <option value="europe">Europe</option>
          </select>
        </div>
        <button type="submit" disabled={status==='loading'}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
          {status==='loading' ? '...' : '+ Ajouter'}
        </button>
      </form>
      {message && <p className={`text-sm ${status==='error'?'text-red-500':'text-green-600'}`}>{message}</p>}

      {/* Liste des sources */}
      <div>
        <h4 className="font-semibold mb-2">Sources actives ({sources.length})</h4>
        {loadingList ? <p className="text-gray-500">Chargement...</p> : (
          <ul className="space-y-2 max-h-60 overflow-y-auto">
            {sources.map(s => (
              <li key={s.id} className="flex items-center justify-between p-2 bg-gray-50 dark:bg-gray-700 rounded text-sm">
                <div className="flex-1 min-w-0">
                  <a href={s.url} target="_blank" rel="noopener" className="text-blue-600 hover:underline truncate block">
                    {s.url}
                  </a>
                  <span className="text-xs text-gray-500">{s.category} • {s.region} • {s.added_by}</span>
                </div>
                <button onClick={() => handleDelete(s.id, s.url)}
                  className="ml-2 px-2 py-1 bg-red-100 text-red-700 rounded hover:bg-red-200 text-xs">
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
