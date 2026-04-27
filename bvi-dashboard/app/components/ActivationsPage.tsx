'use client';
import { useState, useEffect } from 'react';

const API = process.env.NEXT_PUBLIC_API_URL || 'http://76.13.141.221:8002/api';

const STATUS_COLORS: any = { pending: '#fb923c', approved: '#4ade80', rejected: '#f87171' };

const AGENT_LABELS: any = {
  max_search:    'Max Search — Recherche machines',
  sam_comms:     'Sam Comms — Emails B2B',
  visa_vision:   'Visa Vision — Analyse photos',
  lea_extract:   'Léa Extract — Extraction specs',
  logistique:    'Logistique — Transport FR↔PT',
  comptable:     'Comptable — Devis & factures',
  traducteur:    'Traducteur — FR/PT/EN/ES/DE/IT',
  demandes_prix: 'Demandes Prix — Fournisseurs',
  documentation: 'Documentation — RAG technique',
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

export default function ActivationsPage() {
  // ── Activation directe ────────────────────────────────────────────────────
  const [showPanel, setShowPanel]   = useState(false);
  const [actSession, setActSession] = useState('');
  const [actCode, setActCode]       = useState('');
  const [actMode, setActMode]       = useState<'client' | 'premium'>('client');
  const [actAgents, setActAgents]   = useState<string[]>([]);
  const [actAll, setActAll]         = useState(true);
  const [actLoading, setActLoading] = useState(false);
  const [actMsg, setActMsg]         = useState('');

  // ── Demandes en attente ────────────────────────────────────────────────────
  const [requests, setRequests]     = useState<any[]>([]);
  const [filter, setFilter]         = useState('pending');
  const [notes, setNotes]           = useState<{ [id: number]: string }>({});
  const [loading, setLoading]       = useState(true);
  const [msg, setMsg]               = useState('');

  // ── Activation rapide depuis une demande ──────────────────────────────────
  const [quickCode, setQuickCode]       = useState<{ [id: number]: string }>({});
  const [quickMode, setQuickMode]       = useState<{ [id: number]: 'client' | 'premium' }>({});
  const [showActModal, setShowActModal] = useState<{ [id: number]: boolean }>({});

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

  const flash = (setter: (v: string) => void, msg: string) => {
    setter(msg);
    setTimeout(() => setter(''), 4000);
  };

  // Activation directe via code 191070
  const activateClient = async () => {
    if (!actSession.trim()) { flash(setActMsg, '⚠️ Entrez un session_id'); return; }
    if (actCode !== '191070') { flash(setActMsg, '❌ Code invalide'); return; }
    const tok = localStorage.getItem('bvi_token') || '';
    setActLoading(true);
    try {
      const res = await fetch(`${API}/admin/activate-client`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({
          session_id: actSession.trim(),
          code: actCode,
          mode: actMode,
          agents: actAll ? ['all'] : actAgents,
        }),
      });
      const d = await res.json();
      if (d.status === 'ok') {
        flash(setActMsg, `✅ ${d.activated.length} agent(s) activé(s) — mode ${d.mode}`);
        setActSession(''); setActCode('');
        fetchRequests();
      } else {
        flash(setActMsg, '❌ ' + (d.detail || d.message || 'Erreur'));
      }
    } catch { flash(setActMsg, '❌ Erreur réseau'); }
    setActLoading(false);
  };

  // Activation rapide depuis une demande pending (session_id connu)
  const activateFromRequest = async (r: any) => {
    const code = quickCode[r.id] || '';
    if (code !== '191070') { flash(setMsg, '❌ Code invalide pour la demande #' + r.id); return; }
    const mode = quickMode[r.id] || 'client';
    const tok = localStorage.getItem('bvi_token') || '';
    try {
      const res = await fetch(`${API}/admin/activate-client`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json', Authorization: `Bearer ${tok}` },
        body: JSON.stringify({ session_id: r.session_id, code, mode, agents: ['all'] }),
      });
      const d = await res.json();
      if (d.status === 'ok') {
        flash(setMsg, `✅ Session activée (${mode}) — ${d.activated.length} agents`);
        fetchRequests();
      } else {
        flash(setMsg, '❌ ' + (d.detail || d.message || 'Erreur'));
      }
    } catch { flash(setMsg, '❌ Erreur réseau'); }
  };

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
        flash(setMsg, status === 'approved' ? '✅ Approuvé' : '❌ Rejeté');
        fetchRequests();
      }
    } catch { flash(setMsg, '❌ Erreur réseau'); }
  };

  const fmt = (iso: string) => iso
    ? new Date(iso).toLocaleString('fr-FR', { day: '2-digit', month: '2-digit', hour: '2-digit', minute: '2-digit' })
    : '—';

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 24 }}>

      {/* ── Panneau Activation directe ─────────────────────────────────── */}
      <div style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 14, overflow: 'hidden' }}>
        <button
          onClick={() => setShowPanel(p => !p)}
          style={{ width: '100%', padding: '14px 20px', background: 'none', border: 'none', cursor: 'pointer',
            display: 'flex', alignItems: 'center', gap: 10, color: '#e2e8f0', fontSize: 15, fontWeight: 700 }}
        >
          <span style={{ fontSize: 20 }}>🔑</span>
          Activation client (code 191070)
          <span style={{ marginLeft: 'auto', color: '#64748b', fontSize: 12 }}>{showPanel ? '▲ Masquer' : '▼ Ouvrir'}</span>
        </button>

        {showPanel && (
          <div style={{ padding: '0 20px 20px', borderTop: '1px solid #334155' }}>
            <p style={{ fontSize: 12, color: '#64748b', margin: '12px 0' }}>
              Copiez le <b>session_id</b> depuis une demande ci-dessous, entrez le code, choisissez le mode et activez.
            </p>

            <div style={{ display: 'grid', gridTemplateColumns: '1fr 130px', gap: 10, marginBottom: 10 }}>
              <div>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Session ID client</div>
                <input style={inputStyle} placeholder="xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx"
                  value={actSession} onChange={e => setActSession(e.target.value)} />
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Code admin</div>
                <input style={{ ...inputStyle, letterSpacing: 3 }} type="password" placeholder="••••••"
                  value={actCode} onChange={e => setActCode(e.target.value)} />
              </div>
            </div>

            <div style={{ display: 'flex', gap: 10, alignItems: 'flex-end', flexWrap: 'wrap', marginBottom: 10 }}>
              <div>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Mode</div>
                <select style={selectStyle} value={actMode} onChange={e => setActMode(e.target.value as any)}>
                  <option value="client">Client (30 jours)</option>
                  <option value="premium">Premium (permanent)</option>
                </select>
              </div>
              <div>
                <div style={{ fontSize: 11, color: '#64748b', marginBottom: 4 }}>Agents</div>
                <select style={selectStyle} value={actAll ? 'all' : 'custom'} onChange={e => setActAll(e.target.value === 'all')}>
                  <option value="all">Tous les agents</option>
                  <option value="custom">Sélection manuelle</option>
                </select>
              </div>
            </div>

            {!actAll && (
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8, marginBottom: 12 }}>
                {ALL_AGENTS.map(a => (
                  <label key={a} style={{ display: 'flex', alignItems: 'center', gap: 5, fontSize: 12, color: '#94a3b8', cursor: 'pointer' }}>
                    <input type="checkbox" checked={actAgents.includes(a)}
                      onChange={e => setActAgents(prev => e.target.checked ? [...prev, a] : prev.filter(x => x !== a))} />
                    {AGENT_LABELS[a] || a}
                  </label>
                ))}
              </div>
            )}

            {actMsg && (
              <div style={{ marginBottom: 10, padding: '7px 12px', background: '#0f172a', borderRadius: 7,
                color: actMsg.startsWith('✅') ? '#4ade80' : '#f87171', fontSize: 13 }}>{actMsg}</div>
            )}

            <button
              onClick={activateClient}
              disabled={actLoading}
              style={{ padding: '9px 22px', borderRadius: 8, border: 'none', cursor: 'pointer',
                background: '#3b82f6', color: '#fff', fontWeight: 700, fontSize: 14,
                opacity: actLoading ? 0.6 : 1 }}
            >
              {actLoading ? 'Activation...' : '⚡ Activer'}
            </button>
          </div>
        )}
      </div>

      {/* ── Demandes en attente ────────────────────────────────────────── */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16, flexWrap: 'wrap', gap: 10 }}>
          <h2 style={{ margin: 0, fontSize: 20 }}>📋 Demandes d'activation</h2>
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

        {msg && <div style={{ marginBottom: 14, padding: '8px 14px', background: '#1e293b', borderRadius: 8,
          color: msg.startsWith('✅') ? '#4ade80' : '#f87171', fontSize: 13 }}>{msg}</div>}

        {loading ? <p style={{ color: '#64748b' }}>Chargement...</p> : requests.length === 0 ? (
          <div style={{ textAlign: 'center', padding: 60, color: '#475569' }}>
            <div style={{ fontSize: 36, marginBottom: 12 }}>📋</div>
            <div>Aucune demande {filter !== 'all' ? filter : ''}</div>
          </div>
        ) : (
          <div style={{ display: 'flex', flexDirection: 'column', gap: 12 }}>
            {requests.map(r => (
              <div key={r.id} style={{ background: '#1e293b', border: `1px solid ${r.status === 'pending' ? '#fb923c44' : '#334155'}`, borderRadius: 12, padding: '14px 18px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: 10, marginBottom: 8 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, flexWrap: 'wrap' }}>
                    <span style={badge(STATUS_COLORS[r.status] || '#64748b')}>{r.status}</span>
                    <span style={{ fontWeight: 600, color: '#60a5fa', fontSize: 13 }}>{AGENT_LABELS[r.agent_name] || r.agent_name}</span>
                    <span style={{ fontSize: 11, color: '#64748b' }}>{fmt(r.created_at)}</span>
                  </div>
                  {r.user_email && <span style={{ fontSize: 12, color: '#94a3b8' }}>📧 {r.user_email}</span>}
                </div>

                {/* Session ID copiable */}
                {r.session_id && (
                  <div style={{ fontSize: 11, color: '#475569', marginBottom: 6, fontFamily: 'monospace',
                    background: '#0f172a', borderRadius: 5, padding: '3px 8px', display: 'inline-block', cursor: 'pointer' }}
                    title="Cliquer pour copier"
                    onClick={() => { navigator.clipboard.writeText(r.session_id); flash(setMsg, '📋 session_id copié'); }}
                  >
                    {r.session_id}
                  </div>
                )}

                {r.user_message && (
                  <div style={{ background: '#0f172a', borderRadius: 8, padding: '7px 12px', fontSize: 13, color: '#e2e8f0', marginBottom: 10, borderLeft: '3px solid #3b82f6' }}>
                    "{r.user_message}"
                  </div>
                )}

                {r.admin_notes && (
                  <div style={{ fontSize: 12, color: '#64748b', marginBottom: 8 }}>Note : {r.admin_notes}</div>
                )}

                {r.status === 'pending' && (
                  <div style={{ marginTop: 8 }}>
                    {/* Ligne : Note + boutons */}
                    <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                      <div style={{ flex: 1, minWidth: 160 }}>
                        <div style={{ fontSize: 11, color: '#64748b', marginBottom: 3 }}>Note :</div>
                        <input style={{ ...inputStyle, padding: '6px 10px' }} placeholder="Note interne optionnelle"
                          value={notes[r.id] || ''} onChange={e => setNotes(p => ({ ...p, [r.id]: e.target.value }))} />
                      </div>
                      <button
                        onClick={() => setShowActModal(p => ({ ...p, [r.id]: !p[r.id] }))}
                        style={{ padding: '6px 14px', borderRadius: 7, border: 'none',
                          background: showActModal[r.id] ? '#1e293b' : '#3b82f633',
                          color: showActModal[r.id] ? '#64748b' : '#60a5fa',
                          cursor: 'pointer', fontWeight: 700, fontSize: 13, whiteSpace: 'nowrap' }}>
                        {showActModal[r.id] ? '▲ Annuler' : '⚡ Activer'}
                      </button>
                      <button onClick={() => review(r.id, 'rejected')}
                        style={{ padding: '6px 14px', borderRadius: 7, border: 'none', background: '#f8717122', color: '#f87171', cursor: 'pointer', fontWeight: 700, fontSize: 13 }}>
                        ✕ Rejeter
                      </button>
                    </div>
                    {/* Slide-down mini-modale */}
                    {showActModal[r.id] && (
                      <div style={{ marginTop: 10, padding: '14px 16px', background: '#0f172a',
                        borderRadius: 10, border: '1px solid #3b82f644' }}>
                        <div style={{ fontSize: 12, fontWeight: 600, color: '#60a5fa', marginBottom: 10 }}>
                          🔑 Confirmer l'activation — demande #{r.id}
                        </div>
                        <div style={{ display: 'flex', gap: 8, alignItems: 'flex-end', flexWrap: 'wrap' }}>
                          <div>
                            <div style={{ fontSize: 11, color: '#64748b', marginBottom: 3 }}>Code admin</div>
                            <input
                              autoFocus
                              type="password"
                              placeholder="191070"
                              value={quickCode[r.id] || ''}
                              onChange={e => setQuickCode(p => ({ ...p, [r.id]: e.target.value }))}
                              onKeyDown={e => { if (e.key === 'Enter') { activateFromRequest(r); setShowActModal(p => ({ ...p, [r.id]: false })); } }}
                              style={{ ...inputStyle, width: 110, padding: '6px 10px', letterSpacing: 3 }}
                            />
                          </div>
                          <div>
                            <div style={{ fontSize: 11, color: '#64748b', marginBottom: 3 }}>Mode</div>
                            <select
                              value={quickMode[r.id] || 'client'}
                              onChange={e => setQuickMode(p => ({ ...p, [r.id]: e.target.value as any }))}
                              style={{ ...selectStyle, padding: '6px 8px', fontSize: 12 }}>
                              <option value="client">Client (30j)</option>
                              <option value="premium">Premium</option>
                            </select>
                          </div>
                          <button
                            onClick={() => { activateFromRequest(r); setShowActModal(p => ({ ...p, [r.id]: false })); }}
                            style={{ padding: '7px 18px', borderRadius: 7, border: 'none',
                              background: '#3b82f6', color: '#fff', fontWeight: 700, fontSize: 13, cursor: 'pointer' }}>
                            ✓ Confirmer
                          </button>
                          <button
                            onClick={() => setShowActModal(p => ({ ...p, [r.id]: false }))}
                            style={{ padding: '7px 12px', borderRadius: 7, border: '1px solid #334155',
                              background: 'none', color: '#64748b', fontSize: 13, cursor: 'pointer' }}>
                            Annuler
                          </button>
                        </div>
                      </div>
                    )}
                  </div>
                )}

                {r.status !== 'pending' && r.reviewed_at && (
                  <div style={{ fontSize: 11, color: '#475569', marginTop: 6 }}>Traité le {fmt(r.reviewed_at)}</div>
                )}
              </div>
            ))}
          </div>
        )}
      </div>
    </div>
  );
}
