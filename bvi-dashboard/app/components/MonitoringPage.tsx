'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const card = (bg = '#1e293b'): React.CSSProperties => ({
  background: bg, borderRadius: 10, padding: '16px 20px', border: '1px solid #334155',
});

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

export default function MonitoringPage() {
  const [data, setData] = useState<any>(null);
  const [error, setError] = useState('');
  const [lastUpdate, setLastUpdate] = useState('');

  const fetchMonitoring = async () => {
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const res = await fetch(`${API}/monitoring`, { headers: { Authorization: `Bearer ${tok}` } });
      const d = await res.json();
      setData(d);
      setLastUpdate(new Date().toLocaleTimeString('fr-FR'));
      setError('');
    } catch (e) {
      setError('Connexion API impossible');
    }
  };

  useEffect(() => {
    fetchMonitoring();
    const iv = setInterval(fetchMonitoring, 10000);
    return () => clearInterval(iv);
  }, []);

  if (error) return <div style={{ padding: 20, color: '#f87171' }}>⚠️ {error}</div>;
  if (!data) return <div style={{ padding: 20, color: '#94a3b8' }}>Chargement...</div>;

  const ram = data.ram || {};
  const ramPct = ram.pct || 0;
  const ramColor = ramPct > 85 ? '#f87171' : ramPct > 65 ? '#fb923c' : '#4ade80';

  const taskTotal = Object.values(data.tasks || {}).reduce((a: any, b: any) => a + Number(b), 0);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 20 }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>📊 Monitoring VPS</h2>
        <span style={{ fontSize: 12, color: '#64748b' }}>Mis à jour : {lastUpdate} (auto 10s)</span>
      </div>

      {/* RAM */}
      <div style={card()}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 10 }}>
          <strong>💾 RAM VPS</strong>
          <span style={{ color: ramColor, fontWeight: 700 }}>{ramPct}%</span>
        </div>
        <div style={{ background: '#0f172a', borderRadius: 6, height: 12, overflow: 'hidden' }}>
          <div style={{ width: `${ramPct}%`, height: '100%', background: ramColor, transition: 'width 0.5s' }} />
        </div>
        <div style={{ marginTop: 8, display: 'flex', gap: 20, fontSize: 13, color: '#94a3b8' }}>
          <span>Total: <b style={{ color: '#e2e8f0' }}>{ram.total_mb?.toLocaleString()} Mo</b></span>
          <span>Utilisé: <b style={{ color: '#e2e8f0' }}>{ram.used_mb?.toLocaleString()} Mo</b></span>
          <span>Libre: <b style={{ color: '#4ade80' }}>{ram.free_mb?.toLocaleString()} Mo</b></span>
        </div>
      </div>

      {/* Ollama */}
      <div style={card()}>
        <strong>🤖 Ollama — Modèles</strong>
        <div style={{ marginTop: 12, display: 'flex', gap: 8, flexWrap: 'wrap' }}>
          {(data.ollama?.models || []).map((m: string) => {
            const loaded = (data.ollama?.loaded || []).includes(m);
            return (
              <span key={m} style={badge(loaded ? '#4ade80' : '#64748b')}>
                {loaded ? '▶ ' : ''}{m}
              </span>
            );
          })}
          {!data.ollama?.models?.length && <span style={{ color: '#64748b', fontSize: 13 }}>Aucun modèle détecté</span>}
        </div>
        {data.ollama?.loaded?.length > 0 && (
          <div style={{ marginTop: 8, fontSize: 12, color: '#4ade80' }}>
            ▶ En mémoire: {data.ollama.loaded.join(', ')}
          </div>
        )}
      </div>

      {/* Tasks */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(130px, 1fr))', gap: 12 }}>
        {[
          { key: 'pending', label: '⏳ En attente', color: '#fb923c' },
          { key: 'running', label: '⚡ En cours', color: '#60a5fa' },
          { key: 'done', label: '✅ Terminées', color: '#4ade80' },
          { key: 'failed', label: '❌ Échouées', color: '#f87171' },
        ].map(({ key, label, color }) => (
          <div key={key} style={{ ...card(), textAlign: 'center' }}>
            <div style={{ fontSize: 28, fontWeight: 700, color }}>{data.tasks?.[key] || 0}</div>
            <div style={{ fontSize: 12, color: '#64748b', marginTop: 4 }}>{label}</div>
          </div>
        ))}
      </div>

      {/* WebSocket */}
      <div style={card()}>
        <div style={{ display: 'flex', gap: 30 }}>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#60a5fa' }}>{data.active_ws}</div>
            <div style={{ fontSize: 12, color: '#64748b' }}>WebSocket actifs</div>
          </div>
          <div>
            <div style={{ fontSize: 22, fontWeight: 700, color: '#a78bfa' }}>{taskTotal as number}</div>
            <div style={{ fontSize: 12, color: '#64748b' }}>Tâches total</div>
          </div>
        </div>
      </div>

      {/* Recent tasks */}
      {data.recent_tasks?.length > 0 && (
        <div style={card()}>
          <strong style={{ display: 'block', marginBottom: 12 }}>🕐 Tâches récentes</strong>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {data.recent_tasks.map((t: any) => {
              const statusColor: any = { pending: '#fb923c', running: '#60a5fa', done: '#4ade80', failed: '#f87171' };
              return (
                <div key={t.task_id} style={{ display: 'flex', gap: 10, alignItems: 'center', padding: '6px 0', borderBottom: '1px solid #1e293b', fontSize: 13 }}>
                  <span style={badge(statusColor[t.status] || '#64748b')}>{t.status}</span>
                  <span style={{ color: '#60a5fa', fontWeight: 500 }}>{t.agent_name}</span>
                  <span style={{ color: '#64748b', fontSize: 11 }}>{t.language?.toUpperCase()}</span>
                  <span style={{ color: '#475569', fontSize: 11, marginLeft: 'auto' }}>
                    {t.created_at ? new Date(t.created_at).toLocaleString('fr-FR', { hour: '2-digit', minute: '2-digit' }) : ''}
                  </span>
                </div>
              );
            })}
          </div>
        </div>
      )}
    </div>
  );
}
