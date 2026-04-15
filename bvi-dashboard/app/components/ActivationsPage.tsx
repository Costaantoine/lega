'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const STATUS_COLORS: any = { pending: '#fb923c', approved: '#4ade80', rejected: '#f87171' };
const AGENT_LABELS: any = { max_search: 'Max Search (Recherche machines)', sam_comms: 'Sam Comms (Emails)', visa_vision: 'Visa Vision (Photos)' };

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

const input: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box',
};

export default function ActivationsPage() {
  const [requests, setRequests] = useState<any[]>([]);
  const [filter, setFilter] = useState('pending');
  const [notes, setNotes] = useState<{ [id: number]: string }>({});
  const [loading, setLoading] = useState(true);
  const [msg, setMsg] = useState('');

  const fetchRequests = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    setLoading(true);
    try {
      const url = filter === 'all' ? `${API}/activations` : `${API}/activations?status=${filter}`;
      const res = await fetch(url, { headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      if (Array.isArray(data)) setRequests(data);
    } catch { }
    setLoading(false);
  };

  useEffect(() => { fetchRequests(); }, [filter]);

  const review = async (id: number, status: 'approved' | 'rejected') => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const res = await fetch(`${API}/activations/${id}`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ status, admin_notes: notes[id] || '' }),
      });
      const d = await res.json();
      if (d.status === 'ok') {
        setMsg(status === 'approved' ? '✅ Trial activé — notification envoyée au client' : '❌ Demande rejetée');
        fetchRequests();
      }
    } catch { setMsg('❌ Erreur réseau'); }
    setTimeout(() => setMsg(''), 4000);
  };

  const fmt = (iso: string) => iso ? new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>🎁 Demandes d'activation Trial</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          {['pending', 'approved', 'rejected', 'all'].map(s => (
            <button key={s} onClick={() => setFilter(s)}
              style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                borderColor: filter === s ? (STATUS_COLORS[s] || '#60a5fa') : '#334155',
                background: filter === s ? ((STATUS_COLORS[s] || '#60a5fa') + '22') : '#1e293b',
                color: filter === s ? (STATUS_COLORS[s] || '#60a5fa') : '#94a3b8' }}>
              {s === 'all' ? 'Tout' : s}
            </button>
          ))}
          <button onClick={fetchRequests} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: 12 }}>🔄</button>
        </div>
      </div>

      {msg && <div style={{ marginBottom: 14, padding: '8px 14px', background: '#1e293b', borderRadius: 8, color: '#4ade80', fontSize: 13 }}>{msg}</div>}

      {loading ? <p style={{ color: '#64748b' }}>Chargement...</p> : requests.length === 0 ? (
        <div style={{ textAlign: 'center', padding: 60, color: '#475569' }}>
          <div style={{ fontSize: 36, marginBottom: 12 }}>🎁</div>
          <div>Aucune demande {filter !== 'all' ? filter : ''}</div>
        </div>
      ) : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
          {requests.map(r => (
            <div key={r.id} style={{ background: '#1e293b', border: `1px solid ${r.status === 'pending' ? '#fb923c44' : '#334155'}`, borderRadius: 12, padding: '14px 18px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10, marginBottom: 10 }}>
                <div>
                  <span style={badge(STATUS_COLORS[r.status] || '#64748b')}>{r.status}</span>
                  <span style={{ marginLeft: 10, fontWeight: 600, color: '#60a5fa' }}>{AGENT_LABELS[r.agent_name] || r.agent_name}</span>
                  <span style={{ marginLeft: 10, fontSize: 12, color: '#64748b' }}>{fmt(r.created_at)}</span>
                </div>
                {r.user_email && <span style={{ fontSize: 12, color: '#94a3b8' }}>📧 {r.user_email}</span>}
              </div>
              {r.user_message && (
                <div style={{ background: '#0f172a', borderRadius: 8, padding: '8px 12px', fontSize: 13, color: '#e2e8f0', marginBottom: 10, borderLeft: '3px solid #3b82f6' }}>
                  "{r.user_message}"
                </div>
              )}
              {r.admin_notes && (
                <div style={{ fontSize: 12, color: '#64748b', marginBottom: 10 }}>Note : {r.admin_notes}</div>
              )}
              {r.status === 'pending' && (
                <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Note (optionnel) :</div>
                    <input style={input} placeholder="Message pour l'admin ou historique..."
                      value={notes[r.id] || ''} onChange={e => setNotes(p => ({ ...p, [r.id]: e.target.value }))} />
                  </div>
                  <button onClick={() => review(r.id, 'approved')} style={{ padding: '8px 16px', borderRadius: 7, border: 'none', background: '#4ade8033', color: '#4ade80', cursor: 'pointer', fontWeight: 700, fontSize: 14, whiteSpace: 'nowrap' }}>
                    ✅ Approuver
                  </button>
                  <button onClick={() => review(r.id, 'rejected')} style={{ padding: '8px 16px', borderRadius: 7, border: 'none', background: '#f8717133', color: '#f87171', cursor: 'pointer', fontWeight: 700, fontSize: 14, whiteSpace: 'nowrap' }}>
                    ❌ Rejeter
                  </button>
                </div>
              )}
              {r.status !== 'pending' && r.reviewed_at && (
                <div style={{ fontSize: 12, color: '#475569' }}>Traité le {fmt(r.reviewed_at)}</div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
