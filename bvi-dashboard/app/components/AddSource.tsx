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
      const res = await fetch('http://localhost:8002/api/sources/add', {
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
    <div className="p-4 border rounded-lg bg-white dark:bg-gray-800">
      <h3 className="font-bold mb-3">Ajouter une source</h3>
      <form onSubmit={handleSubmit} className="space-y-3">
        <input type="url" placeholder="https://exemple.com" value={url} 
          onChange={(e) => setUrl(e.target.value)} required
          className="w-full p-2 border rounded dark:bg-gray-700"/>
        <div className="flex gap-2">
          <select value={category} onChange={(e) => setCategory(e.target.value)}
            className="p-2 border rounded dark:bg-gray-700">
            <option value="constructeur">Constructeur</option>
            <option value="loueur">Loueur</option>
            <option value="plateforme">Plateforme</option>
          </select>
          <select value={region} onChange={(e) => setRegion(e.target.value)}
            className="p-2 border rounded dark:bg-gray-700">
            <option value="bordeaux">Bordeaux</option>
            <option value="pt">Portugal</option>
            <option value="europe">Europe</option>
          </select>
        </div>
        <button type="submit" disabled={status==='loading'}
          className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700 disabled:opacity-50">
          {status==='loading' ? '...' : 'Ajouter'}
        </button>
      </form>
      {message && <p className={'mt-2 text-sm ' + (status==='error' ? 'text-red-500' : 'text-green-600')}>{message}</p>}
    </div>
  );
}
