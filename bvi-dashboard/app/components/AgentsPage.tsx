'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '3px 10px', borderRadius: 20, fontSize: 12,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

const STATUS_COLORS: any = { active: '#4ade80', maintenance: '#fb923c', overloaded: '#f87171' };
const PREMIUM_COLOR = '#a78bfa';

export default function AgentsPage() {
  const [agents, setAgents] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);
  const [updating, setUpdating] = useState<string | null>(null);
  const [msg, setMsg] = useState('');

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
      if (d.status === 'ok') {
        setMsg(`✅ ${name} → ${next}`);
        fetchAgents();
      } else {
        setMsg('⚠️ ' + (d.message || 'Erreur'));
      }
    } catch { setMsg('❌ Erreur réseau'); }
    setUpdating(null);
    setTimeout(() => setMsg(''), 3000);
  };

  const capColor = (cap: string) => {
    if (cap.includes('recherche')) return '#60a5fa';
    if (cap.includes('email') || cap.includes('comms')) return '#fb923c';
    if (cap.includes('vision') || cap.includes('screenshot')) return '#a78bfa';
    if (cap.includes('extract')) return '#4ade80';
    return '#64748b';
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>🤖 Registry des Agents</h2>
        <button onClick={fetchAgents} style={{ padding: '6px 14px', background: '#1e293b', border: '1px solid #334155', borderRadius: 6, color: '#e2e8f0', cursor: 'pointer', fontSize: 13 }}>
          🔄 Rafraîchir
        </button>
      </div>

      {msg && <div style={{ marginBottom: 16, padding: '8px 14px', background: '#1e293b', borderRadius: 8, color: '#4ade80', fontSize: 13 }}>{msg}</div>}

      {loading ? <p style={{ color: '#64748b' }}>Chargement...</p> : (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
          {agents.map(agent => (
            <div key={agent.name} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: '16px 20px' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10 }}>
                <div>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 6 }}>
                    <span style={{ fontWeight: 700, fontSize: 15 }}>{agent.display_name}</span>
                    <span style={badge(STATUS_COLORS[agent.status] || '#64748b')}>{agent.status}</span>
                    {agent.is_premium && <span style={badge(PREMIUM_COLOR)}>★ Premium</span>}
                    {agent.price_monthly_eur > 0 && <span style={{ fontSize: 12, color: '#64748b' }}>{agent.price_monthly_eur}€/mois</span>}
                  </div>
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>
                    <code style={{ color: '#60a5fa' }}>{agent.name}</code>
                    {' · '}
                    <span style={{ color: '#a78bfa' }}>model: {agent.model}</span>
                    {agent.ram_cost_mb && <span>{' · '}{agent.ram_cost_mb >= 1000 ? `${(agent.ram_cost_mb / 1024).toFixed(1)} Go` : `${agent.ram_cost_mb} Mo`} RAM</span>}
                    {agent.avg_latency_sec && <span>{' · '}~{agent.avg_latency_sec}s</span>}
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: 6 }}>
                    {(agent.capabilities || []).map((cap: string) => (
                      <span key={cap} style={{ ...badge(capColor(cap)), fontSize: 11 }}>{cap}</span>
                    ))}
                  </div>
                </div>
                <button
                  onClick={() => toggleStatus(agent.name, agent.status)}
                  disabled={updating === agent.name}
                  style={{
                    padding: '6px 14px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                    background: agent.status === 'active' ? '#fb923c22' : '#4ade8022',
                    color: agent.status === 'active' ? '#fb923c' : '#4ade80',
                    opacity: updating === agent.name ? 0.5 : 1,
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
