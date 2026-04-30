'use client';
import { useState, useEffect } from 'react';

const API_BASE = (process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api').replace('/api', '');
const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const STATUS_COLORS: any = { pending: '#fb923c', active: '#4ade80', rejected: '#f87171', expired: '#94a3b8' };

const AGENT_LABELS: Record<string, string> = {
  max_search:    'Max Search — Recherche machines',
  sam_comms:     'Sam Comms — Emails B2B',
  visa_vision:   'Visa Vision — Analyse photos',
  lea_extract:   'Lea Extract — Extraction specs',
  logistique:    'Logistique — Transport FR↔PT',
  comptable:     'Comptable — Devis & factures',
  traducteur:    'Traducteur — Traduction FR/PT/EN',
  demandes_prix: 'Demandes Prix — Négociation',
  documentation: 'Documentation — RAG',
};

const ALL_AGENTS = Object.keys(AGENT_LABELS);

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

const inputStyle: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box',
};

const selectStyle: React.CSSProperties = {
  padding: '8px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, cursor: 'pointer',
};

const agentChip = (selected: boolean, color = '#3b82f6'): React.CSSProperties => ({
  padding: '4px 10px', borderRadius: 20, fontSize: 11, fontWeight: 600, cursor: 'pointer',
  border: `1px solid ${selected ? color : '#334155'}`,
  background: selected ? color + '22' : '#0f172a',
  color: selected ? color : '#64748b',
  userSelect: 'none' as any,
});

export default function ActivationsPage() {
  const [showPanel, setShowPanel]   = useState(false);
  const [actSession, setActSession] = useState('');
  const [actCode, setActCode]       = useState('');
  const [actMode, setActMode]       = useState<'client' | 'premium'>('client');
  const [actAgents, setActAgents]   = useState<string[]>([]);
  const [actAll, setActAll]         = useState(true);
  const [actLoading, setActLoading] = useState(false);
  const [actMsg, setActMsg]         = useState('');

  const [requests, setRequests]     = useState<any[]>([]);
  const [loading, setLoading]       = useState(true);
  const [msg, setMsg]               = useState('');

  const flash = (setter: (v: string) => void, m: string) => { setter(m); setTimeout(() => setter(''), 4000); };

  const fetchRequests = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    setLoading(true);
    try {
      const res = await fetch(`${API_BASE}/admin/license/pending`, { headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      if (Array.isArray(data)) setRequests(data);
    } catch { }
    setLoading(false);
  };

  useEffect(() => { fetchRequests(); }, []);

  const activateClient = async () => {
    if (!actSession.trim()) { flash(setActMsg, '⚠️ Entrez un session_id'); return; }
    if (actCode !== '191070') { flash(setActMsg, '❌ Code invalide'); return; }
    if (!actAll && actAgents.length === 0) { flash(setActMsg, '⚠️ Sélectionnez au moins un agent'); return; }
    const tok = localStorage.getItem('bvi_token') || '';
    setActLoading(true);
    try {
      const res = await fetch(`${API}/admin/activate-client`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ session_id: actSession.trim(), code: actCode, mode: actMode, agents: actAll ? ['all'] : actAgents }),
      });
      const d = await res.json();
      if (d.status === 'ok') { flash(setActMsg, `✅ ${d.activated.join(', ')} activé(s) — ${d.mode}`); setActSession(''); setActCode(''); setActAgents([]); }
      else flash(setActMsg, '❌ ' + (d.detail || d.message || 'Erreur'));
    } catch { flash(setActMsg, '❌ Erreur réseau'); }
    setActLoading(false);
  };

  const fmt = (iso: string) => iso ? new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 14, overflow: 'hidden' }}>
        <button onClick={() => setShowPanel(p => !p)}
          style={{ width: '100%', padding: '14px 20px', background: 'none', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 10, color: '#e2e8f0', fontSize: 15, fontWeight: 700 }}>
          <span style={{ fontSize: 20 }}>🔑</span> Activation client (code 191070)
          <span style={{ marginLeft: 'auto', color: '#64748b', fontSize: 12 }}>{showPanel ? '▲ Masquer' : '▼ Ouvrir'}</span>
        </button>
        {showPanel && (
          <div style={{ padding: '0 20px 20px', borderTop: '1px solid #334155' }}>
            <p style={{ fontSize: 12, color: '#64748b', margin: '12px 0' }}>Copiez le <b>session_id</b> depuis une demande ci-dessous et sélectionnez les agents à activer.</p>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 130px', gap: 10, marginBottom: 12 }}>
              <div><div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Session ID</div>
                <input style={inputStyle} placeholder="xxxxxxxx-…" value={actSession} onChange={e => setActSession(e.target.value)} /></div>
              <div><div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Code admin</div>
                <input style={{ ...inputStyle, letterSpacing: 3 }} type="password" placeholder="••••••" value={actCode} onChange={e => setActCode(e.target.value)} /></div>
            </div>
            <div style={{ marginBottom: 12 }}>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Mode</div>
              <select style={selectStyle} value={actMode} onChange={e => setActMode(e.target.value as any)}>
                <option value="client">Client (30 jours)</option>
                <option value="premium">Premium (permanent)</option>
              </select>
            </div>
            <div style={{ marginBottom: 14 }}>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 8 }}>Agents à activer :</div>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 7 }}>
                <span onClick={() => { setActAll(true); setActAgents([]); }} style={agentChip(actAll, '#a78bfa')}>✦ Tous</span>
                {ALL_AGENTS.map(a => (
                  <span key={a} title={AGENT_LABELS[a]}
                    onClick={() => { setActAll(false); setActAgents(prev => prev.includes(a) ? prev.filter(x => x !== a) : [...prev, a]); }}
                    style={agentChip(!actAll && actAgents.includes(a))}>{a}</span>
                ))}
              </div>
              {!actAll && actAgents.length > 0 && <div style={{ fontSize: 11, color: '#60a5fa', marginTop: 6 }}>Sélectionnés : {actAgents.join(', ')}</div>}
            </div>
            {actMsg && <div style={{ marginBottom: 10, padding: '7px 12px', background: '#0f172a', borderRadius: 7, color: actMsg.startsWith('✅') ? '#4ade80' : '#f87171', fontSize: 13 }}>{actMsg}</div>}
            <button onClick={activateClient} disabled={actLoading}
              style={{ padding: '9px 22px', borderRadius: 8, border: 'none', cursor: 'pointer', background: '#3b82f6', color: '#fff', fontWeight: 700, fontSize: 14, opacity: actLoading ? 0.6 : 1 }}>
              {actLoading ? 'Activation...' : `⚡ Activer ${actAll ? 'tous' : actAgents.length + ' agent(s)'}`}
            </button>
          </div>
        )}
      </div>

      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>🔐 Demandes de licence en attente</h2>
          <button onClick={fetchRequests} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: 12 }}>🔄</button>
        </div>
        <p style={{ fontSize: 12, color: '#64748b', margin: '0 0 16px' }}>
          Ces demandes sont traitées via Telegram (boutons ⚡ Activer / ✕ Rejeter).
        </p>
        {msg && <div style={{ marginBottom: 14, padding: '8px 14px', background: '#1e293b', borderRadius: 8, color: msg.startsWith('✅') ? '#4ade80' : '#f87171', fontSize: 13 }}>{msg}</div>}
        {loading ? <p style={{ color: '#64748b' }}>Chargement...</p> : requests.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#475569' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>✅</div>
            <div>Aucune demande de licence en attente</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {requests.map(r => (
              <div key={r.id} style={{ background: '#1e293b', border: '1px solid #fb923c44', borderRadius: 12, padding: '14px 18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10, marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={badge(STATUS_COLORS[r.status] || '#64748b')}>{r.status}</span>
                    <span style={{ fontWeight: 600, color: '#60a5fa', fontSize: 13 }}>{AGENT_LABELS[r.agent_name] || r.agent_name}</span>
                    <span style={{ fontSize: 11, color: '#64748b' }}>{fmt(r.requested_at)}</span>
                  </div>
                  <span style={{ fontFamily: 'monospace', fontSize: 11, color: '#475569' }}>{r.client_id?.slice(0, 12)}…</span>
                </div>
                {r.original_message && (
                  <div style={{ background: '#0f172a', borderRadius: 8, padding: '7px 12px', fontSize: 13, color: '#e2e8f0', borderLeft: '3px solid #3b82f6' }}>"{r.original_message}"</div>
                )}
                <div style={{ marginTop: 8, fontSize: 11, color: '#475569' }}>
                  Traitement via Telegram — boutons ⚡ Activer / ✕ Rejeter
                </div>
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
