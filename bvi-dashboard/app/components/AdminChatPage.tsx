'use client';
import { useState, useEffect, useRef } from 'react';

const API_WS = process.env.NEXT_PUBLIC_API_URL?.replace('/api', '').replace('http', 'ws') || 'ws://76.13.141.221:8002';

interface Msg { role: 'user' | 'assistant'; text: string; meta?: string }

const card: React.CSSProperties = {
  background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 16,
};

export default function AdminChatPage() {
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState('');
  const [ws, setWs] = useState<WebSocket | null>(null);
  const [connected, setConnected] = useState(false);
  const [lang, setLang] = useState<'fr' | 'pt' | 'en'>('fr');
  const bottomRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    const token = localStorage.getItem('bvi_token') || '';
    const url = `${API_WS}/ws/stream?token=${encodeURIComponent(token)}`;
    const socket = new WebSocket(url);

    socket.onopen = () => {
      setConnected(true);
      setMsgs([{ role: 'assistant', text: '🔑 Session admin connectée. Vous pouvez modifier le site vitrine en langage naturel.', meta: 'system' }]);
    };

    socket.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);
        const text = d.payload || d.direct_response || d.message || JSON.stringify(d);
        const meta = d.metadata ? `${d.metadata.intent || ''} ${d.metadata.agent || ''} ${d.metadata.status || ''}`.trim() : '';
        setMsgs(prev => [...prev, { role: 'assistant', text, meta }]);
      } catch {}
    };

    socket.onclose = () => setConnected(false);
    socket.onerror = () => setConnected(false);

    setWs(socket);
    return () => socket.close();
  }, []);

  useEffect(() => {
    bottomRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [msgs]);

  const send = () => {
    if (!input.trim() || !ws || ws.readyState !== WebSocket.OPEN) return;
    setMsgs(prev => [...prev, { role: 'user', text: input }]);
    ws.send(JSON.stringify({ payload: input, lang }));
    setInput('');
    inputRef.current?.focus();
  };

  const EXAMPLES = [
    'Change le slogan FR par "Votre partenaire machines TP en Europe"',
    'Mets le téléphone à +351 912 000 001',
    'Désactive la section ai_banner',
    'Change la couleur primaire en #2563eb',
  ];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>💬 Chat Admin — Gestion site par commande</h2>
        <div style={{ display: 'flex', alignItems: 'center', gap: 12 }}>
          <span style={{ fontSize: 12, color: connected ? '#4ade80' : '#f87171' }}>
            {connected ? '● Connecté (admin)' : '○ Déconnecté'}
          </span>
          <select value={lang} onChange={e => setLang(e.target.value as 'fr' | 'pt' | 'en')}
            style={{ padding: '4px 8px', borderRadius: 6, border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: 13 }}>
            <option value="fr">FR</option>
            <option value="pt">PT</option>
            <option value="en">EN</option>
          </select>
        </div>
      </div>

      {/* Exemples rapides */}
      <div style={{ marginBottom: 16, display: 'flex', flexWrap: 'wrap', gap: 8 }}>
        {EXAMPLES.map((ex, i) => (
          <button key={i} onClick={() => { setInput(ex); inputRef.current?.focus(); }}
            style={{ padding: '4px 12px', fontSize: 12, borderRadius: 20, border: '1px solid #334155', background: '#1e293b', color: '#94a3b8', cursor: 'pointer' }}>
            {ex.length > 45 ? ex.slice(0, 45) + '…' : ex}
          </button>
        ))}
      </div>

      {/* Zone messages */}
      <div style={{ ...card, minHeight: 400, maxHeight: 520, overflowY: 'auto', marginBottom: 12, display: 'flex', flexDirection: 'column', gap: 10 }}>
        {msgs.map((m, i) => (
          <div key={i} style={{ display: 'flex', flexDirection: 'column', alignItems: m.role === 'user' ? 'flex-end' : 'flex-start' }}>
            <div style={{
              maxWidth: '80%', padding: '10px 14px', borderRadius: 10, fontSize: 13, lineHeight: 1.5,
              background: m.role === 'user' ? '#1d4ed8' : m.meta === 'system' ? '#0f2a50' : '#0f172a',
              color: m.role === 'user' ? '#fff' : '#e2e8f0',
              border: m.role === 'assistant' ? '1px solid #1e293b' : 'none',
            }}>
              {m.text}
            </div>
            {m.meta && m.meta !== 'system' && (
              <div style={{ fontSize: 10, color: '#475569', marginTop: 3, paddingInline: 4 }}>{m.meta}</div>
            )}
          </div>
        ))}
        <div ref={bottomRef} />
      </div>

      {/* Input */}
      <div style={{ display: 'flex', gap: 8 }}>
        <input
          ref={inputRef}
          value={input}
          onChange={e => setInput(e.target.value)}
          onKeyDown={e => e.key === 'Enter' && send()}
          placeholder="Ex: Change le slogan FR par… / Désactive la section stats…"
          style={{ flex: 1, padding: '10px 14px', borderRadius: 8, border: '1px solid #334155', background: '#0f172a', color: '#e2e8f0', fontSize: 14 }}
          disabled={!connected}
        />
        <button onClick={send} disabled={!connected || !input.trim()}
          style={{ padding: '10px 20px', background: connected ? '#3b82f6' : '#334155', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: connected ? 'pointer' : 'not-allowed', fontSize: 14 }}>
          ➤
        </button>
      </div>

      <p style={{ fontSize: 11, color: '#475569', marginTop: 10 }}>
        💡 Commandes possibles : changer slogan / couleur / téléphone / adresse / activer-désactiver sections du site vitrine.
        Les modifications sont appliquées immédiatement sur <a href="http://76.13.141.221:3002" target="_blank" rel="noopener" style={{ color: '#60a5fa' }}>port 3002 ↗</a>
      </p>
    </div>
  );
}
