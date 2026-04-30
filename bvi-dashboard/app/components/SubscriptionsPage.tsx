'use client';
import { useState, useEffect, useCallback } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const STATUS_COLOR: Record<string, string> = {
  active: '#4ade80', trial: '#60a5fa', expired: '#f87171', pending: '#fb923c',
};

const badge = (status: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 9px', borderRadius: 20, fontSize: 11,
  fontWeight: 700, background: (STATUS_COLOR[status] || '#94a3b8') + '22',
  color: STATUS_COLOR[status] || '#94a3b8', border: `1px solid ${(STATUS_COLOR[status] || '#94a3b8')}44`,
});

const btn = (color: string, small = false): React.CSSProperties => ({
  padding: small ? '3px 10px' : '6px 16px', borderRadius: 6, border: 'none', cursor: 'pointer',
  fontWeight: 600, fontSize: small ? 11 : 12, background: color + '22', color, transition: 'opacity .15s',
});

const sel: React.CSSProperties = {
  padding: '7px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, cursor: 'pointer',
};

const AGENTS = ['all', 'max_search', 'sam_comms', 'lea_extract', 'visa_vision', 'logistique', 'comptable', 'traducteur', 'demandes_prix', 'documentation'];

export default function SubscriptionsPage() {
  const [rows, setRows]         = useState<any[]>([]);
  const [loading, setLoading]   = useState(true);
  const [statusF, setStatusF]   = useState('all');
  const [agentF, setAgentF]     = useState('all');
  const [msg, setMsg]           = useState('');
  const [extending, setExtending] = useState<number | null>(null);

  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 3000); };

  const load = useCallback(async () => {
    setLoading(true);
    const tok = localStorage.getItem('bvi_token') || '';
    const params = new URLSearchParams();
    if (statusF !== 'all') params.set('status', statusF);
    if (agentF !== 'all')  params.set('agent', agentF);
    try {
      const res = await fetch(`${API}/subscriptions?${params}`, { headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      setRows(Array.isArray(data) ? data : []);
    } catch { flash('Erreur de chargement'); }
    finally { setLoading(false); }
  }, [statusF, agentF]);

  useEffect(() => { load(); }, [load]);

  const extend = async (id: number, days: number) => {
    setExtending(id);
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const res = await fetch(`${API}/subscriptions/${id}/extend`, {
        method: 'POST', headers: { Authorization: `Bearer ${tok}`, 'Content-Type': 'application/json' },
        body: JSON.stringify({ days }),
      });
      if (res.ok) { flash(`✅ +${days}j accordés`); load(); }
      else flash('Erreur lors de l\'extension');
    } finally { setExtending(null); }
  };

  const cancel = async (id: number) => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      await fetch(`${API}/subscriptions/${id}`, { method: 'DELETE', headers: { Authorization: `Bearer ${tok}` } });
      flash('Abonnement désactivé');
      load();
    } catch { flash('Erreur'); }
  };

  // Stats locales
  const stats = {
    active:  rows.filter(r => r.status === 'active').length,
    trial:   rows.filter(r => r.status === 'trial').length,
    expired: rows.filter(r => r.status === 'expired').length,
  };

  const fmtDate = (d: string | null) => d
    ? new Date(d).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', year: '2-digit', hour: '2-digit', minute: '2-digit' })
    : '—';

  const isExpiringSoon = (r: any) =>
    r.trial_expires_at && ['active', 'trial'].includes(r.status) &&
    new Date(r.trial_expires_at).getTime() - Date.now() < 24 * 3600 * 1000;

  return (
    <div style={{ fontFamily: 'system-ui, sans-serif' }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 20, color: '#f8fafc' }}>🔑 Abonnements</h2>
        <button onClick={load} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: 12 }}>🔄 Actualiser</button>
      </div>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 14, marginBottom: 24, flexWrap: 'wrap' }}>
        {[
          { label: 'Actifs', value: stats.active, color: '#4ade80' },
          { label: 'Trials', value: stats.trial,  color: '#60a5fa' },
          { label: 'Expirés', value: stats.expired, color: '#f87171' },
          { label: 'Total',  value: rows.length,  color: '#94a3b8' },
        ].map(s => (
          <div key={s.label} style={{ background: '#1e293b', borderRadius: 10, padding: '14px 22px', minWidth: 110 }}>
            <div style={{ fontSize: 24, fontWeight: 700, color: s.color }}>{s.value}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 2 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Filtres */}
      <div style={{ display: 'flex', gap: 10, marginBottom: 18, flexWrap: 'wrap', alignItems: 'center' }}>
        <select value={statusF} onChange={e => setStatusF(e.target.value)} style={sel}>
          {['all', 'active', 'trial', 'expired'].map(s => (
            <option key={s} value={s}>{s === 'all' ? 'Tous les statuts' : s}</option>
          ))}
        </select>
        <select value={agentF} onChange={e => setAgentF(e.target.value)} style={sel}>
          {AGENTS.map(a => (
            <option key={a} value={a}>{a === 'all' ? 'Tous les agents' : a}</option>
          ))}
        </select>
        {msg && <span style={{ color: msg.startsWith('✅') ? '#4ade80' : '#f87171', fontSize: 13, fontWeight: 600 }}>{msg}</span>}
      </div>

      {/* Table */}
      {loading ? (
        <div style={{ color: '#475569', fontSize: 14 }}>Chargement…</div>
      ) : rows.length === 0 ? (
        <div style={{ color: '#475569', fontSize: 14 }}>Aucun abonnement trouvé.</div>
      ) : (
        <div style={{ background: '#1e293b', borderRadius: 12, overflow: 'hidden', border: '1px solid #334155' }}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ background: '#0f172a', color: '#64748b', textAlign: 'left' }}>
                {['#', 'Utilisateur', 'Agent', 'Statut', 'Activé le', 'Expire le', 'Actions'].map(h => (
                  <th key={h} style={{ padding: '10px 14px', fontWeight: 600, fontSize: 11, textTransform: 'uppercase', letterSpacing: '.04em' }}>{h}</th>
                ))}
              </tr>
            </thead>
            <tbody>
              {rows.map((r, i) => (
                <tr key={r.id}
                  style={{ borderTop: '1px solid #1e293b', background: i % 2 === 0 ? '#0f172a' : '#0a1628',
                    outline: isExpiringSoon(r) ? '1px solid #fb923c44' : 'none' }}>
                  <td style={{ padding: '10px 14px', color: '#475569' }}>{r.id}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ color: '#e2e8f0' }}>{r.email || r.session_id?.slice(0, 8) + '…'}</div>
                    {r.company_name && <div style={{ color: '#64748b', fontSize: 11 }}>{r.company_name}</div>}
                    <div style={{ color: '#475569', fontSize: 11 }}>{r.preferred_language?.toUpperCase()}</div>
                  </td>
                  <td style={{ padding: '10px 14px', color: '#93c5fd', fontFamily: 'monospace', fontSize: 12 }}>{r.agent_name}</td>
                  <td style={{ padding: '10px 14px' }}>
                    <span style={badge(r.status)}>{r.status}</span>
                    {isExpiringSoon(r) && <span style={{ marginLeft: 6, fontSize: 10, color: '#fb923c' }}>⚠️ bientôt</span>}
                  </td>
                  <td style={{ padding: '10px 14px', color: '#94a3b8' }}>{fmtDate(r.activated_at)}</td>
                  <td style={{ padding: '10px 14px', color: '#94a3b8' }}>
                    {r.trial_expires_at ? (
                      <span style={{ color: r.status === 'expired' ? '#f87171' : '#94a3b8' }}>{fmtDate(r.trial_expires_at)}</span>
                    ) : '∞'}
                  </td>
                  <td style={{ padding: '10px 14px' }}>
                    <div style={{ display: 'flex', gap: 6, flexWrap: 'wrap' }}>
                      <button onClick={() => extend(r.id, 30)} disabled={extending === r.id}
                        style={btn('#4ade80', true)} title="+30 jours">+30j</button>
                      <button onClick={() => extend(r.id, 7)} disabled={extending === r.id}
                        style={btn('#60a5fa', true)} title="+7 jours">+7j</button>
                      {r.status !== 'expired' && (
                        <button onClick={() => cancel(r.id)}
                          style={btn('#f87171', true)} title="Désactiver">✕</button>
                      )}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}
