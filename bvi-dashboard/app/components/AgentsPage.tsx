'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '3px 10px', borderRadius: 20, fontSize: 12,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

const STATUS_COLORS: any = { active: '#4ade80', maintenance: '#fb923c', overloaded: '#f87171' };
const PREMIUM_COLOR = '#a78bfa';
const FREE_COLOR = '#22d3ee';
const ALWAYS_FREE = new Set(['tony_interface', 'lea', 'agenda']);

const inputStyle: React.CSSProperties = {
  padding: '7px 11px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13,
};

const selectStyle: React.CSSProperties = {
  padding: '7px 11px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, cursor: 'pointer',
};

export default function AgentsPage() {
  const [agents, setAgents]     = useState<any[]>([]);
  const [loading, setLoading]   = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [msg, setMsg]           = useState('');

  // ── Panneau activation client ─────────────────────────────────────────────
  const [showAct, setShowAct]     = useState(false);
  const [actSession, setActSession] = useState('');
  const [actCode, setActCode]     = useState('');
  const [actMode, setActMode]     = useState<'client' | 'premium'>('client');
  const [actLoading, setActLoading] = useState(false);
  const [actMsg, setActMsg]       = useState('');

  const fetchAgents = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const res = await fetch(`${API}/agents/registry`, { headers: { Authorization: `Bearer ${tok}` } });
      const data = await res.json();
      if (Array.isArray(data)) setAgents(data);
    } catch { }
    setLoading(false);
  };

  useEffect(() => { fetchAgents(); }, []);

  const flash = (setter: (v: string) => void, text: string) => {
    setter(text); setTimeout(() => setter(''), 4000);
  };

  const toggleStatus = async (name: string, current: string) => {
    const next = current === 'active' ? 'maintenance' : 'active';
    const tok = localStorage.getItem('bvi_token') || '';
    setUpdating(name);
    try {
      const res = await fetch(`${API}/agents/${name}/status`, {
        method: 'PUT',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ status: next }),
      });
      const d = await res.json();
      if (d.status === 'ok') { flash(setMsg, `✅ ${name} → ${next}`); fetchAgents(); }
      else flash(setMsg, '⚠️ ' + (d.message || 'Erreur'));
    } catch { flash(setMsg, '❌ Erreur réseau'); }
    setUpdating(null);
  };

  const activateClient = async () => {
    if (!actSession.trim()) { flash(setActMsg, '⚠️ Entrez un session_id'); return; }
    if (actCode !== '191070') { flash(setActMsg, '❌ Code invalide'); return; }
    const tok = localStorage.getItem('bvi_token') || '';
    setActLoading(true);
    try {
      const res = await fetch(`${API}/admin/activate-client`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ session_id: actSession.trim(), code: actCode, mode: actMode, agents: ['all'] }),
      });
      const d = await res.json();
      if (d.status === 'ok') {
        flash(setActMsg, `✅ ${d.activated.length} agents activés — mode ${d.mode}`);
        setActSession(''); setActCode('');
      } else {
        flash(setActMsg, '❌ ' + (d.detail || d.message || 'Erreur'));
      }
    } catch { flash(setActMsg, '❌ Erreur réseau'); }
    setActLoading(false);
  };

  const capColor = (cap: string) => {
    if (cap.includes('recherche')) return '#60a5fa';
    if (cap.includes('email') || cap.includes('comms')) return '#fb923c';
    if (cap.includes('vision') || cap.includes('screenshot')) return '#a78bfa';
    if (cap.includes('extract')) return '#4ade80';
    return '#64748b';
  };

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 16 }}>

      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>🤖 Registry des Agents</h2>
        <div style={{ display: 'flex', gap: 8 }}>
          <button
            onClick={() => setShowAct(p => !p)}
            style={{ padding: '6px 14px', background: showAct ? '#3b82f633' : '#1e293b',
              border: '1px solid ' + (showAct ? '#3b82f6' : '#334155'),
              borderRadius: 6, color: showAct ? '#60a5fa' : '#e2e8f0', cursor: 'pointer', fontSize: 13, fontWeight: 600 }}
          >
            🔑 Activer client
          </button>
          <button onClick={fetchAgents}
            style={{ padding: '6px 14px', background: '#1e293b', border: '1px solid #334155', borderRadius: 6, color: '#e2e8f0', cursor: 'pointer', fontSize: 13 }}>
            🔄 Rafraîchir
          </button>
        </div>
      </div>

      {/* Panneau activation */}
      {showAct && (
        <div style={{ background: '#1e293b', border: '1px solid #3b82f644', borderRadius: 12, padding: '16px 20px' }}>
          <div style={{ fontSize: 13, fontWeight: 600, color: '#60a5fa', marginBottom: 12 }}>
            🔑 Activation client — tous les agents premium
          </div>
          <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap', alignItems: 'flex-end' }}>
            <div>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Session ID</div>
              <input
                style={{ ...inputStyle, width: 290 }}
                placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                value={actSession} onChange={e => setActSession(e.target.value)}
              />
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Code admin</div>
              <input
                style={{ ...inputStyle, width: 90, letterSpacing: 3 }}
                type="password" placeholder="••••••"
                value={actCode} onChange={e => setActCode(e.target.value)}
              />
            </div>
            <div>
              <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Mode</div>
              <select style={selectStyle} value={actMode} onChange={e => setActMode(e.target.value as any)}>
                <option value="client">Client — 30 jours</option>
                <option value="premium">Premium — permanent</option>
              </select>
            </div>
            <button
              onClick={activateClient} disabled={actLoading}
              style={{ padding: '7px 20px', borderRadius: 7, border: 'none', cursor: 'pointer',
                background: '#3b82f6', color: '#fff', fontWeight: 700, fontSize: 13,
                opacity: actLoading ? 0.6 : 1, whiteSpace: 'nowrap' }}
            >
              {actLoading ? '...' : '⚡ Activer'}
            </button>
          </div>
          {actMsg && (
            <div style={{ marginTop: 10, padding: '6px 12px', borderRadius: 6, background: '#0f172a',
              color: actMsg.startsWith('✅') ? '#4ade80' : '#f87171', fontSize: 13 }}>{actMsg}</div>
          )}
          <div style={{ marginTop: 8, fontSize: 11, color: '#475569' }}>
            Le session_id se trouve dans la page <b>Activations</b> quand le client a demandé un accès.
            Tony, Léa et Agenda sont toujours gratuits et n'ont pas besoin d'activation.
          </div>
        </div>
      )}

      {msg && <div style={{ padding: '8px 14px', background: '#1e293b', borderRadius: 8, color: '#4ade80', fontSize: 13 }}>{msg}</div>}

      {/* Liste agents */}
      {loading ? <p style={{ color: '#64748b' }}>Chargement...</p> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {agents.map(agent => (
            <div key={agent.name} style={{
              background: '#1e293b',
              border: `1px solid ${ALWAYS_FREE.has(agent.name) ? '#22d3ee22' : agent.is_premium ? '#a78bfa22' : '#334155'}`,
              borderRadius: 12, padding: '14px 18px',
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 5, flexWrap: 'wrap' }}>
                    <span style={{ fontWeight: 700, fontSize: 14 }}>{agent.display_name}</span>
                    <span style={badge(STATUS_COLORS[agent.status] || '#64748b')}>{agent.status}</span>
                    {ALWAYS_FREE.has(agent.name)
                      ? <span style={badge(FREE_COLOR)}>✓ Gratuit</span>
                      : agent.is_premium
                        ? <span style={badge(PREMIUM_COLOR)}>🔒 Premium</span>
                        : null}
                    {agent.price_monthly_eur > 0 && (
                      <span style={{ fontSize: 11, color: '#64748b' }}>{agent.price_monthly_eur}€/mois</span>
                    )}
                  </div>
                  <div style={{ fontSize: 11, color: '#64748b', marginBottom: 7 }}>
                    <code style={{ color: '#60a5fa' }}>{agent.name}</code>
                    {' · '}
                    <span style={{ color: '#a78bfa' }}>model: {agent.model}</span>
                    {agent.ram_cost_mb && <span>{' · '}{agent.ram_cost_mb >= 1000 ? `${(agent.ram_cost_mb / 1024).toFixed(1)} Go` : `${agent.ram_cost_mb} Mo`} RAM</span>}
                    {agent.avg_latency_sec && <span>{' · '}~{agent.avg_latency_sec}s</span>}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 5 }}>
                    {(agent.capabilities || []).map((cap: string) => (
                      <span key={cap} style={{ ...badge(capColor(cap)), fontSize: 10 }}>{cap}</span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => toggleStatus(agent.name, agent.status)}
                  disabled={updating === agent.name}
                  style={{
                    padding: '5px 12px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 11, fontWeight: 600,
                    background: agent.status === 'active' ? '#fb923c22' : '#4ade8022',
                    color: agent.status === 'active' ? '#fb923c' : '#4ade80',
                    opacity: updating === agent.name ? 0.5 : 1, whiteSpace: 'nowrap',
                  }}
                >
                  {updating === agent.name ? '...' : agent.status === 'active' ? '⏸ Maintenance' : '▶ Activer'}
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
