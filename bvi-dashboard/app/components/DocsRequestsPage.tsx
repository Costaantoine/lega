'use client';
import { useState, useEffect } from 'react';

const SITE_API   = process.env.NEXT_PUBLIC_SITE_API_URL  || 'http://76.13.141.221:8003/api/site';
const ADMIN_KEY  = process.env.NEXT_PUBLIC_SITE_ADMIN_KEY || 'lega-client-jwt-';
const adminH = () => ({ 'X-Admin-Key': ADMIN_KEY });

const STATUS_COLORS: Record<string, string> = {
  pending: '#fb923c', approved: '#4ade80', rejected: '#f87171',
};

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

const selectStyle: React.CSSProperties = {
  padding: '8px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, cursor: 'pointer',
};

const btnStyle = (color: string): React.CSSProperties => ({
  padding: '5px 14px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontWeight: 600, fontSize: 12, background: color + '22', color, transition: 'opacity .15s',
});

export default function DocsRequestsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [filter, setFilter]     = useState('pending');
  const [loading, setLoading]   = useState(true);
  const [msg, setMsg]           = useState('');

  const fetchRequests = async () => {
    setLoading(true);
    try {
      const url = filter ? `${SITE_API}/docs/requests?status=${filter}` : `${SITE_API}/docs/requests`;
      const res = await fetch(url, { headers: adminH() });
      const data = await res.json();
      setRequests(Array.isArray(data) ? data : []);
    } catch {
      setMsg('Erreur de chargement');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { fetchRequests(); }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

  useEffect(() => {
    const iv = setInterval(fetchRequests, 30000);
    return () => clearInterval(iv);
  }, [filter]); // eslint-disable-line react-hooks/exhaustive-deps

  const approve = async (rid: number) => {
    setMsg('');
    try {
      const res = await fetch(`${SITE_API}/docs/requests/${rid}/approve`, { method: 'POST', headers: adminH() });
      const data = await res.json();
      if (res.ok) {
        setMsg(`✅ Approuvé — lien envoyé par email (valable 24h)`);
        fetchRequests();
      } else {
        setMsg(`❌ ${data.detail || 'Erreur'}`);
      }
    } catch {
      setMsg('❌ Erreur réseau');
    }
  };

  const reject = async (rid: number) => {
    setMsg('');
    try {
      const res = await fetch(`${SITE_API}/docs/requests/${rid}/reject`, { method: 'POST', headers: adminH() });
      if (res.ok) {
        setMsg('🚫 Demande rejetée');
        fetchRequests();
      } else {
        setMsg('❌ Erreur lors du rejet');
      }
    } catch {
      setMsg('❌ Erreur réseau');
    }
  };

  const pendingCount = requests.filter(r => r.status === 'pending').length;

  return (
    <div style={{ padding: 24, color: '#e2e8f0', maxWidth: 900 }}>
      <div style={{ display: 'flex', alignItems: 'center', gap: 14, marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 20, fontWeight: 700 }}>📄 Demandes de Documentation</h2>
        {pendingCount > 0 && (
          <span style={{ ...badge('#fb923c'), fontSize: 13 }}>{pendingCount} en attente</span>
        )}
        <select value={filter} onChange={e => setFilter(e.target.value)} style={{ ...selectStyle, marginLeft: 'auto' }}>
          <option value="pending">En attente</option>
          <option value="approved">Approuvées</option>
          <option value="rejected">Rejetées</option>
          <option value="">Toutes</option>
        </select>
        <button onClick={fetchRequests} style={{ ...btnStyle('#60a5fa'), padding: '7px 14px' }}>↻ Actualiser</button>
      </div>

      {msg && (
        <div style={{ padding: '10px 14px', borderRadius: 8, background: '#1e293b',
          border: '1px solid #334155', marginBottom: 16, fontSize: 13 }}>
          {msg}
        </div>
      )}

      {loading ? (
        <div style={{ color: '#64748b', fontSize: 14 }}>Chargement…</div>
      ) : requests.length === 0 ? (
        <div style={{ color: '#64748b', fontSize: 14, padding: '40px 0', textAlign: 'center' }}>
          Aucune demande {filter === 'pending' ? 'en attente' : filter === 'approved' ? 'approuvée' : filter === 'rejected' ? 'rejetée' : ''}
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {requests.map(r => {
            const color = STATUS_COLORS[r.status] || '#94a3b8';
            return (
              <div key={r.id} style={{
                background: '#1e293b', border: '1px solid #334155',
                borderRadius: 10, padding: '14px 18px',
              }}>
                <div style={{ display: 'flex', alignItems: 'flex-start', gap: 12, flexWrap: 'wrap' }}>
                  <div style={{ flex: 1, minWidth: 200 }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 6 }}>
                      <span style={{ fontWeight: 700, fontSize: 14 }}>#{r.id}</span>
                      <span style={badge(color)}>{r.status}</span>
                      <span style={{ color: '#64748b', fontSize: 11, marginLeft: 'auto' }}>
                        {new Date(r.created_at).toLocaleString('fr-FR')}
                      </span>
                    </div>
                    <div style={{ fontSize: 13, marginBottom: 4 }}>
                      <b>{r.client_name}</b>
                      {r.client_company && <span style={{ color: '#94a3b8' }}> · {r.client_company}</span>}
                    </div>
                    <div style={{ fontSize: 12, color: '#60a5fa', marginBottom: 4 }}>{r.client_email}</div>
                    <div style={{ fontSize: 12, color: '#94a3b8', marginBottom: 4 }}>
                      📁 <code style={{ background: '#0f172a', padding: '1px 6px', borderRadius: 4 }}>{r.doc_path}</code>
                    </div>
                    {r.motif && (
                      <div style={{ fontSize: 12, color: '#cbd5e1', marginTop: 6, fontStyle: 'italic' }}>
                        « {r.motif} »
                      </div>
                    )}
                    {r.status === 'approved' && r.download_token && (
                      <div style={{ fontSize: 11, color: '#4ade80', marginTop: 6 }}>
                        🔗 Lien envoyé · expire {r.token_expires_at ? new Date(r.token_expires_at).toLocaleString('fr-FR') : '?'}
                      </div>
                    )}
                  </div>

                  {r.status === 'pending' && (
                    <div style={{ display: 'flex', gap: 8, alignItems: 'center', paddingTop: 4 }}>
                      <button onClick={() => approve(r.id)} style={btnStyle('#4ade80')}>
                        ✅ Approuver
                      </button>
                      <button onClick={() => reject(r.id)} style={btnStyle('#f87171')}>
                        🚫 Rejeter
                      </button>
                    </div>
                  )}
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
