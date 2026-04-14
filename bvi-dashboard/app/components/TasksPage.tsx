'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const STATUS_COLORS: any = { pending: '#fb923c', running: '#60a5fa', done: '#4ade80', failed: '#f87171', cancelled: '#64748b' };

const badge = (color: string): React.CSSProperties => ({
  display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11,
  fontWeight: 600, background: color + '22', color, border: `1px solid ${color}44`,
});

export default function TasksPage() {
  const [tasks, setTasks] = useState<any[]>([]);
  const [filter, setFilter] = useState('all');
  const [selected, setSelected] = useState<any>(null);
  const [loading, setLoading] = useState(true);

  const fetchTasks = async () => {
    try {
      const url = filter === 'all' ? `${API}/tasks?limit=50` : `${API}/tasks?status=${filter}&limit=50`;
      const res = await fetch(url);
      const data = await res.json();
      if (Array.isArray(data)) setTasks(data);
    } catch { }
    setLoading(false);
  };

  const fetchTaskDetail = async (task_id: string) => {
    try {
      const res = await fetch(`${API}/tasks/${task_id}`);
      const data = await res.json();
      setSelected(data);
    } catch { }
  };

  useEffect(() => { fetchTasks(); }, [filter]);

  const fmt = (iso: string) => iso ? new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' }) : '—';

  return (
    <div style={{ display: 'flex', gap: 20, height: '100%' }}>
      {/* List */}
      <div style={{ flex: 1, minWidth: 0 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>📋 File de tâches</h2>
          <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
            {['all', 'pending', 'running', 'done', 'failed'].map(s => (
              <button key={s} onClick={() => setFilter(s)}
                style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid', cursor: 'pointer', fontSize: 12, fontWeight: 600,
                  borderColor: filter === s ? STATUS_COLORS[s] || '#60a5fa' : '#334155',
                  background: filter === s ? (STATUS_COLORS[s] + '22' || '#60a5fa22') : '#1e293b',
                  color: filter === s ? (STATUS_COLORS[s] || '#60a5fa') : '#94a3b8' }}>
                {s === 'all' ? 'Tout' : s}
              </button>
            ))}
            <button onClick={fetchTasks} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid #334155', background: '#1e293b', color: '#e2e8f0', cursor: 'pointer', fontSize: 12 }}>🔄</button>
          </div>
        </div>

        {loading ? <p style={{ color: '#64748b' }}>Chargement...</p> : tasks.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 40, color: '#475569' }}>Aucune tâche</div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {tasks.map(t => (
              <div key={t.task_id} onClick={() => fetchTaskDetail(t.task_id)}
                style={{ background: selected?.task_id === t.task_id ? '#1e3a5f' : '#1e293b', border: `1px solid ${selected?.task_id === t.task_id ? '#3b82f6' : '#334155'}`, borderRadius: 8, padding: '10px 14px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
                <span style={badge(STATUS_COLORS[t.status] || '#64748b')}>{t.status}</span>
                <span style={{ color: '#60a5fa', fontWeight: 500, fontSize: 13 }}>{t.agent_name}</span>
                <span style={{ fontSize: 11, padding: '2px 6px', borderRadius: 4, background: '#0f172a', color: '#94a3b8' }}>{t.language?.toUpperCase()}</span>
                <span style={{ color: '#475569', fontSize: 12, marginLeft: 'auto' }}>{fmt(t.created_at)}</span>
                {t.actual_latency_sec && <span style={{ fontSize: 11, color: '#64748b' }}>{t.actual_latency_sec}s</span>}
              </div>
            ))}
          </div>
        )}
      </div>

      {/* Detail panel */}
      {selected && (
        <div style={{ width: 360, background: '#1e293b', border: '1px solid #334155', borderRadius: 12, padding: 16, flexShrink: 0, overflowY: 'auto', maxHeight: 'calc(100vh - 100px)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
            <strong>Détail tâche</strong>
            <button onClick={() => setSelected(null)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer', fontSize: 16 }}>✕</button>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10, fontSize: 13 }}>
            <div><span style={{ color: '#64748b' }}>ID :</span> <code style={{ fontSize: 11, color: '#94a3b8', wordBreak: 'break-all' }}>{selected.task_id}</code></div>
            <div><span style={{ color: '#64748b' }}>Agent :</span> <span style={{ color: '#60a5fa' }}>{selected.agent_name}</span></div>
            <div><span style={{ color: '#64748b' }}>Statut :</span> <span style={badge(STATUS_COLORS[selected.status] || '#64748b')}>{selected.status}</span></div>
            <div><span style={{ color: '#64748b' }}>Langue :</span> {selected.language?.toUpperCase()}</div>
            <div><span style={{ color: '#64748b' }}>Créé :</span> {fmt(selected.created_at)}</div>
            {selected.completed_at && <div><span style={{ color: '#64748b' }}>Terminé :</span> {fmt(selected.completed_at)}</div>}
            {selected.actual_latency_sec && <div><span style={{ color: '#64748b' }}>Durée :</span> {selected.actual_latency_sec}s</div>}
            {selected.payload && (
              <div>
                <div style={{ color: '#64748b', marginBottom: 4 }}>Payload :</div>
                <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', fontSize: 12, color: '#94a3b8', wordBreak: 'break-word' }}>
                  {JSON.parse(selected.payload || '{}').message || JSON.stringify(JSON.parse(selected.payload || '{}'))}
                </div>
              </div>
            )}
            {selected.result_json && (
              <div>
                <div style={{ color: '#64748b', marginBottom: 4 }}>Résultat :</div>
                <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', fontSize: 12, color: '#4ade80', whiteSpace: 'pre-wrap', wordBreak: 'break-word', maxHeight: 300, overflowY: 'auto' }}>
                  {JSON.parse(selected.result_json)?.text || JSON.stringify(JSON.parse(selected.result_json), null, 2)}
                </div>
              </div>
            )}
            {selected.error_message && (
              <div>
                <div style={{ color: '#f87171', marginBottom: 4 }}>Erreur :</div>
                <div style={{ background: '#0f172a', borderRadius: 6, padding: '8px 10px', fontSize: 12, color: '#f87171' }}>{selected.error_message}</div>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
