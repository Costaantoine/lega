"use client";
import { useState, useEffect, useRef } from "react";

const stripEmoji = (s: string) =>
  s.replace(/[\u{1F600}-\u{1F64F}\u{1F300}-\u{1F5FF}\u{1F680}-\u{1F6FF}\u{1F700}-\u{1F77F}\u{1F780}-\u{1F7FF}\u{1F800}-\u{1F8FF}\u{1F900}-\u{1F9FF}\u{1FA00}-\u{1FA6F}\u{1FA70}-\u{1FAFF}\u{2600}-\u{26FF}\u{2700}-\u{27BF}\u{FE00}-\u{FE0F}\u{1F1E0}-\u{1F1FF}]/gu, "")
   .replace(/\s{2,}/g, " ").trim();

const API = process.env.NEXT_PUBLIC_API_URL || "http://76.13.141.221:8002/api";
const WS_URL = process.env.NEXT_PUBLIC_WS_URL || "ws://76.13.141.221:8002/ws";
const API_BASE = API.replace("/api", "");

// ── Types ─────────────────────────────────────────────────────────────────────

type Msg = { role: "user" | "agent"; text: string; time?: string; uploading?: boolean; streaming?: boolean };
type Product = { id: number; title: string; price: number; currency: string; status: string; images?: any; category: string; description?: string };
type Tab = "chat" | "catalogue" | "upload";
type StdLang = "fr" | "pt" | "en";

const STD_GREET: Record<StdLang, string> = {
  fr: "Bonjour, LEGA — Léa à votre service. En quoi puis-je vous aider ?",
  pt: "Bom dia, LEGA — Léa ao seu serviço. Em que posso ajudar?",
  en: "Good day, LEGA — Lea speaking. How may I help you?",
};

const TONY_WELCOME: Record<string, string> = {
  fr: "Bonjour ! Je suis Tony, votre responsable de bureau LEGA.\nJe coordonne votre équipe d'agents IA. Que puis-je faire pour vous ?",
  pt: "Olá! Sou o Tony, o seu responsável de bureau LEGA.\nCoordenо a sua equipa de agentes IA. Em que posso ajudar?",
  en: "Hello! I'm Tony, your LEGA office manager.\nI coordinate your AI agent team. How can I help you?",
};

const WAITING_TEXT: Record<string, string> = {
  fr: "Tony reçoit votre message...",
  pt: "Tony recebe a sua mensagem...",
  en: "Tony is receiving your message...",
};

const T: any = {
  fr: {
    title: "🚜 LEGA", subtitle: "Assistant Travaux Publics",
    placeholder: "Votre question...", send: "Envoyer",
    tabs: { chat: "💬 Chat", catalogue: "📦 Catalogue", upload: "📸 Photo" },
    connecting: "Connexion...", connected: "En ligne", disconnected: "Hors ligne",
    lang: "🇫🇷 FR",
    noProducts: "Aucun produit disponible", loading: "Chargement...",
    uploadTitle: "Analyser une photo", uploadDesc: "Prenez une photo de machine ou sélectionnez-en une depuis votre galerie. Léa l'analysera pour vous.",
    uploadBtn: "Choisir / Prendre une photo", analyzeBtn: "Analyser",
    analyzing: "Analyse en cours...",
  },
  pt: {
    title: "🚜 LEGA", subtitle: "Assistente Obras Públicas",
    placeholder: "A sua pergunta...", send: "Enviar",
    tabs: { chat: "💬 Chat", catalogue: "📦 Catálogo", upload: "📸 Foto" },
    connecting: "A ligar...", connected: "Online", disconnected: "Offline",
    lang: "🇵🇹 PT",
    noProducts: "Nenhum produto disponível", loading: "A carregar...",
    uploadTitle: "Analisar uma foto", uploadDesc: "Tire uma foto de uma máquina ou selecione uma da sua galeria. Léa analisá-la-á.",
    uploadBtn: "Escolher / Tirar foto", analyzeBtn: "Analisar",
    analyzing: "A analisar...",
  },
};

// ── Helpers ───────────────────────────────────────────────────────────────────

const now = () => new Date().toLocaleTimeString("fr-FR", { hour: "2-digit", minute: "2-digit" });

// ── Component ─────────────────────────────────────────────────────────────────

export default function ClientApp() {
  const [lang, setLang] = useState<"fr" | "pt">("fr");
  const [tab, setTab] = useState<Tab>("chat");
  const [msgs, setMsgs] = useState<Msg[]>([]);
  const [input, setInput] = useState("");
  const [wsStatus, setWsStatus] = useState<"connecting" | "connected" | "disconnected">("connecting");
  const [products, setProducts] = useState<Product[]>([]);
  const [prodLoading, setProdLoading] = useState(false);
  const [selectedProduct, setSelectedProduct] = useState<Product | null>(null);
  const [photoFile, setPhotoFile] = useState<File | null>(null);
  const [photoPreview, setPhotoPreview] = useState<string | null>(null);
  const [analyzing, setAnalyzing] = useState(false);
  const [thinkingStatus, setThinkingStatus] = useState<"waiting" | "thinking" | "done" | null>(null);
  const [thinkingText, setThinkingText] = useState("Tony reçoit votre message...");
  const [agentBadge, setAgentBadge] = useState<string | null>(null);

  // Standardiste widget
  const [stdOpen, setStdOpen] = useState(false);
  const [stdLang, setStdLang] = useState<StdLang>("fr");
  const [stdMsgs, setStdMsgs] = useState<Msg[]>([]);
  const [stdInput, setStdInput] = useState("");
  const [stdLoading, setStdLoading] = useState(false);
  const [ttsEnabled, setTtsEnabled] = useState(false);
  const ttsEnabledRef = useRef(false);
  const audioCtxRef = useRef<AudioContext | null>(null);
  const audioQueueRef = useRef<AudioBuffer[]>([]);
  const audioPlayingRef = useRef(false);
  const stdEnd = useRef<HTMLDivElement>(null);

  const ws = useRef<WebSocket | null>(null);
  const reconnect = useRef(0);
  const messagesEnd = useRef<HTMLDivElement>(null);
  const fileInput = useRef<HTMLInputElement>(null);
  const t = T[lang];

  // Afficher accueil Tony dans la bonne langue (remplace le 1er message si c'est un welcome)
  useEffect(() => {
    setMsgs(prev => {
      if (prev.length === 0) return [{ role: "agent", text: TONY_WELCOME[lang] || TONY_WELCOME.fr, time: now() }];
      // Mettre à jour le welcome si c'est le seul message (changement de langue)
      if (prev.length === 1 && prev[0].role === "agent") {
        const isWelcome = Object.values(TONY_WELCOME).some(w => prev[0].text === w);
        if (isWelcome) return [{ role: "agent", text: TONY_WELCOME[lang] || TONY_WELCOME.fr, time: now() }];
      }
      return prev;
    });
  }, [lang]);

  // Standardiste — greeting on open / lang change
  useEffect(() => {
    if (stdOpen) {
      setStdMsgs([{ role: "agent", text: STD_GREET[stdLang], time: now() }]);
    }
  }, [stdOpen, stdLang]);

  // Sync TTS ref
  useEffect(() => { ttsEnabledRef.current = ttsEnabled; }, [ttsEnabled]);

  // Standardiste — scroll to bottom
  useEffect(() => {
    stdEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [stdMsgs]);

  // Standardiste — send message via shared WS with preferred_agent
  const stdSend = () => {
    if (!stdInput.trim() || stdLoading) return;
    const text = stdInput.trim();
    setStdInput("");
    setStdMsgs(p => [...p, { role: "user", text, time: now() }]);
    setStdLoading(true);
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "user_message", payload: text, lang: stdLang, preferred_agent: "standardiste" }));
    } else {
      setStdMsgs(p => [...p, { role: "agent", text: stdLang === "fr" ? "⚠️ Reconnexion..." : stdLang === "pt" ? "⚠️ A reconectar..." : "⚠️ Reconnecting...", time: now() }]);
      setStdLoading(false);
      connectWS();
    }
  };

  // Scroll to bottom
  useEffect(() => {
    messagesEnd.current?.scrollIntoView({ behavior: "smooth" });
  }, [msgs]);

  // WebSocket
  const connectWS = () => {
    if (ws.current?.readyState === WebSocket.OPEN) return;
    setWsStatus("connecting");
    const socket = new WebSocket(`${WS_URL}/stream`);
    socket.onopen = () => { setWsStatus("connected"); reconnect.current = 0; };
    const playNext = (ctx: AudioContext) => {
      if (audioPlayingRef.current || audioQueueRef.current.length === 0) return;
      audioPlayingRef.current = true;
      const buf = audioQueueRef.current.shift()!;
      const src = ctx.createBufferSource();
      src.buffer = buf; src.connect(ctx.destination);
      src.onended = () => { audioPlayingRef.current = false; playNext(ctx); };
      src.start(0);
    };

    socket.onmessage = (e) => {
      try {
        const d = JSON.parse(e.data);

        if (d.type === "welcome") {
          const texts = d.metadata?.texts || {};
          const welcomeText = texts[lang] || texts.fr || d.payload || "";
          if (welcomeText) {
            setMsgs(prev => {
              if (prev.length === 0) return [{ role: "agent", text: welcomeText, time: now() }];
              if (prev.length === 1 && prev[0].role === "agent") {
                const isWelcome = Object.values(TONY_WELCOME).some(w => prev[0].text === w);
                if (isWelcome) return [{ role: "agent", text: welcomeText, time: now() }];
              }
              return prev;
            });
          }
          return;
        }

        if (d.type === "audio_chunk" && ttsEnabledRef.current) {
          if (!audioCtxRef.current) audioCtxRef.current = new AudioContext();
          const ctx = audioCtxRef.current;
          const bytes = Uint8Array.from(atob(d.payload), c => c.charCodeAt(0));
          ctx.decodeAudioData(bytes.buffer.slice(0), buf => {
            audioQueueRef.current.push(buf); playNext(ctx);
          });
          return;
        }

        if (d.type === "thinking") {
          setThinkingStatus("thinking");
          setThinkingText(d.payload || "Tony traite votre demande...");
          setAgentBadge(d.metadata?.agent || null);
          return;
        }

        if (d.type === "text_chunk") {
          const chunk = stripEmoji(d.payload || "");
          if (!chunk) return;
          setStdMsgs(p => {
            const last = p[p.length - 1];
            if (last?.streaming) return [...p.slice(0, -1), { ...last, text: last.text + chunk }];
            return [...p, { role: "agent", text: chunk, streaming: true, time: now() }];
          });
          return;
        }

        if (d.type === "agent_response_enriched") {
          const text = stripEmoji(d.payload || "");
          if (text) setMsgs(p => [...p, { role: "agent", text, time: now() }]);
          return;
        }

        if (d.type === "agent_response" || d.type === "task_result") {
          setThinkingStatus("done");
          setTimeout(() => setThinkingStatus(null), 300);
          const text = stripEmoji(d.payload || "");
          if (d.metadata?.agent === "standardiste") {
            setStdMsgs(p => {
              const last = p[p.length - 1];
              if (last?.streaming) return [...p.slice(0, -1), { ...last, streaming: false }];
              if (!text) return p;
              return [...p, { role: "agent", text, time: now() }];
            });
            setStdLoading(false);
          } else {
            if (text) setMsgs(p => [...p, { role: "agent", text, time: now() }]);
          }
        }
      } catch { }
    };
    socket.onclose = () => {
      setWsStatus("disconnected");
      if (reconnect.current < 5) {
        reconnect.current++;
        setTimeout(connectWS, 2000 * reconnect.current);
      }
    };
    socket.onerror = () => socket.close();
    ws.current = socket;
  };

  useEffect(() => {
    connectWS();
    const hb = setInterval(() => {
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: "ping", payload: "alive" }));
      }
    }, 30000);
    return () => { clearInterval(hb); ws.current?.close(); };
  }, []);

  // Send message
  const send = () => {
    if (!input.trim()) return;
    const text = input.trim();
    setInput("");
    setMsgs(p => [...p, { role: "user", text, time: now() }]);
    setThinkingStatus("waiting");
    setThinkingText(WAITING_TEXT[lang] || WAITING_TEXT.fr);
    setAgentBadge(null);
    if (ws.current?.readyState === WebSocket.OPEN) {
      ws.current.send(JSON.stringify({ type: "user_message", payload: text, lang }));
    } else {
      connectWS();
      setThinkingStatus(null);
      setMsgs(p => [...p, { role: "agent", text: lang === "fr" ? "⚠️ Reconnexion en cours..." : "⚠️ A reconectar...", time: now() }]);
    }
  };

  // Load products
  const loadProducts = async () => {
    setProdLoading(true);
    try {
      const res = await fetch(`${API}/products?status=published&limit=50`);
      const data = await res.json();
      if (Array.isArray(data)) setProducts(data);
    } catch { }
    setProdLoading(false);
  };

  useEffect(() => {
    if (tab === "catalogue") loadProducts();
  }, [tab]);

  // Photo selection
  const onPhotoChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    setPhotoFile(file);
    const reader = new FileReader();
    reader.onload = (ev) => setPhotoPreview(ev.target?.result as string);
    reader.readAsDataURL(file);
  };

  // Analyze photo via Tony chat
  const analyzePhoto = async () => {
    if (!photoFile) return;
    setAnalyzing(true);
    setMsgs(p => [...p, { role: "user", text: lang === "fr" ? "📸 [Photo envoyée pour analyse]" : "📸 [Foto enviada para análise]", time: now() }]);
    setTab("chat");
    try {
      // Upload photo to a temp product or direct analysis endpoint
      const fd = new FormData();
      fd.append("file", photoFile);
      // Use Tony via websocket with image description prompt
      const prompt = lang === "fr"
        ? `Analyse cette photo de machine TP et donne-moi : le type de machine, la marque si visible, l'état apparent, et une estimation de valeur.`
        : `Analisa esta foto de máquina TP e dá-me: o tipo de máquina, a marca se visível, o estado aparente e uma estimativa de valor.`;
      if (ws.current?.readyState === WebSocket.OPEN) {
        ws.current.send(JSON.stringify({ type: "user_message", payload: prompt, lang }));
      }
    } catch { }
    setAnalyzing(false);
    setPhotoFile(null);
    setPhotoPreview(null);
  };

  const statusColor = wsStatus === "connected" ? "#4ade80" : wsStatus === "connecting" ? "#fb923c" : "#f87171";
  const statusText = t[wsStatus] || wsStatus;

  return (
    <div style={{ height: "100dvh", display: "flex", flexDirection: "column", maxWidth: 560, margin: "0 auto", position: "relative" }}>
      <style>{`
        @keyframes tonyPulse { 0%,80%,100%{opacity:0} 40%{opacity:1} }
        .tony-dot { display:inline-block; animation:tonyPulse 1.4s infinite; font-size:14px; }
        .tony-dot:nth-child(2) { animation-delay:0.2s; }
        .tony-dot:nth-child(3) { animation-delay:0.4s; }
        .tony-thinking { transition: opacity 0.3s ease; }
        .tony-thinking.fade-out { opacity:0; }
      `}</style>

      {/* Header */}
      <div style={{ background: "#0a1628", borderBottom: "1px solid #1e293b", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 }}>
        <div>
          <div style={{ fontWeight: 700, fontSize: 17 }}>{t.title}</div>
          <div style={{ fontSize: 11, color: "#64748b" }}>{t.subtitle}</div>
        </div>
        <div style={{ display: "flex", gap: 10, alignItems: "center" }}>
          <div style={{ display: "flex", alignItems: "center", gap: 5 }}>
            <span style={{ width: 7, height: 7, borderRadius: "50%", background: statusColor, display: "inline-block" }} />
            <span style={{ fontSize: 11, color: statusColor }}>{statusText}</span>
          </div>
          <button onClick={() => setLang(l => l === "fr" ? "pt" : "fr")}
            style={{ padding: "4px 10px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#e2e8f0", cursor: "pointer", fontSize: 12, fontWeight: 600 }}>
            {t.lang}
          </button>
        </div>
      </div>

      {/* Tab content */}
      <div style={{ flex: 1, overflow: "hidden", display: "flex", flexDirection: "column" }}>

        {/* CHAT TAB */}
        {tab === "chat" && (
          <>
            <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
              {msgs.map((m, i) => (
                <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: m.role === "user" ? "flex-end" : "flex-start" }}>
                  <div style={{
                    maxWidth: "82%", padding: "10px 14px", borderRadius: m.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                    background: m.role === "user" ? "#2563eb" : "#1e293b", color: "#fff",
                    fontSize: 14, lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word",
                  }}>
                    {m.text}
                  </div>
                  {m.time && <span style={{ fontSize: 10, color: "#475569", marginTop: 2, paddingInline: 4 }}>{m.time}</span>}
                </div>
              ))}
              {thinkingStatus && (
                <div className={`tony-thinking${thinkingStatus === "done" ? " fade-out" : ""}`} style={{ display: "flex", flexDirection: "column", alignItems: "flex-start" }}>
                  <div style={{
                    background: "#f0f2f5", borderRadius: 12, padding: "8px 14px",
                    fontSize: 13, color: "#555", margin: "4px 0",
                    display: "flex", alignItems: "center", gap: 6, maxWidth: "85%",
                  }}>
                    <span style={{ whiteSpace: "pre-wrap" }}>{thinkingText}</span>
                    {agentBadge && (
                      <span style={{ fontSize: 10, background: "#3b82f6", color: "#fff", padding: "1px 7px", borderRadius: 8, flexShrink: 0 }}>
                        {agentBadge}
                      </span>
                    )}
                    <span style={{ flexShrink: 0 }}>
                      <span className="tony-dot">●</span>
                      <span className="tony-dot">●</span>
                      <span className="tony-dot">●</span>
                    </span>
                  </div>
                </div>
              )}
              <div ref={messagesEnd} />
            </div>
            <div style={{ padding: "10px 12px", borderTop: "1px solid #1e293b", background: "#0f172a", display: "flex", gap: 8 }}>
              <input
                value={input}
                onChange={e => setInput(e.target.value)}
                onKeyDown={e => e.key === "Enter" && !e.shiftKey && send()}
                placeholder={t.placeholder}
                style={{ flex: 1, padding: "11px 14px", borderRadius: 24, border: "1px solid #334155", background: "#1e293b", color: "#f8fafc", fontSize: 15, outline: "none" }}
              />
              <button onClick={send} disabled={!input.trim()}
                style={{ width: 46, height: 46, borderRadius: "50%", border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer", fontSize: 20, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, opacity: input.trim() ? 1 : 0.4 }}>
                ➤
              </button>
            </div>
          </>
        )}

        {/* CATALOGUE TAB */}
        {tab === "catalogue" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "12px 16px" }}>
            <div style={{ display: "flex", justifyContent: "space-between", marginBottom: 14 }}>
              <span style={{ fontWeight: 600, fontSize: 15 }}>📦 Machines disponibles</span>
              <button onClick={loadProducts} style={{ padding: "4px 10px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#94a3b8", cursor: "pointer", fontSize: 12 }}>🔄</button>
            </div>
            {prodLoading ? (
              <div style={{ textAlign: "center", padding: 40, color: "#475569" }}>{t.loading}</div>
            ) : products.length === 0 ? (
              <div style={{ textAlign: "center", padding: 60, color: "#475569" }}>
                <div style={{ fontSize: 40, marginBottom: 12 }}>🚜</div>
                <div>{t.noProducts}</div>
              </div>
            ) : selectedProduct ? (
              // Product detail
              <div>
                <button onClick={() => setSelectedProduct(null)} style={{ marginBottom: 14, padding: "6px 12px", borderRadius: 6, border: "1px solid #334155", background: "#1e293b", color: "#94a3b8", cursor: "pointer", fontSize: 13 }}>← Retour</button>
                {(() => {
                  const imgs: string[] = typeof selectedProduct.images === "string" ? JSON.parse(selectedProduct.images || "[]") : (selectedProduct.images || []);
                  return imgs[0] ? <img src={`${API_BASE}${imgs[0]}`} style={{ width: "100%", maxHeight: 240, objectFit: "cover", borderRadius: 10, marginBottom: 14 }} alt="" /> : null;
                })()}
                <h3 style={{ margin: "0 0 8px", fontSize: 18 }}>{selectedProduct.title}</h3>
                <div style={{ fontSize: 22, fontWeight: 700, color: "#4ade80", marginBottom: 10 }}>{selectedProduct.price?.toLocaleString()} {selectedProduct.currency}</div>
                {selectedProduct.description && <p style={{ color: "#94a3b8", fontSize: 14, lineHeight: 1.6, margin: "0 0 16px" }}>{selectedProduct.description}</p>}
                <button onClick={() => {
                  setInput(lang === "fr" ? `Je suis intéressé par "${selectedProduct.title}" à ${selectedProduct.price}${selectedProduct.currency}, pouvez-vous m'en dire plus ?` : `Tenho interesse na "${selectedProduct.title}" a ${selectedProduct.price}${selectedProduct.currency}, pode dar-me mais informações?`);
                  setTab("chat");
                }} style={{ width: "100%", padding: "12px", borderRadius: 10, border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer", fontSize: 15, fontWeight: 600 }}>
                  {lang === "fr" ? "En savoir plus" : "Saber mais"}
                </button>
              </div>
            ) : (
              // Product grid
              <div style={{ display: "grid", gridTemplateColumns: "repeat(2, 1fr)", gap: 12 }}>
                {products.map(p => {
                  const imgs: string[] = typeof p.images === "string" ? JSON.parse(p.images || "[]") : (p.images || []);
                  return (
                    <div key={p.id} onClick={() => setSelectedProduct(p)} style={{ background: "#1e293b", borderRadius: 10, border: "1px solid #334155", overflow: "hidden", cursor: "pointer" }}>
                      {imgs[0] ? (
                        <img src={`${API_BASE}${imgs[0]}`} style={{ width: "100%", height: 110, objectFit: "cover" }} alt="" />
                      ) : (
                        <div style={{ width: "100%", height: 110, background: "#0f172a", display: "flex", alignItems: "center", justifyContent: "center", fontSize: 32, color: "#475569" }}>🚜</div>
                      )}
                      <div style={{ padding: "10px 12px" }}>
                        <div style={{ fontWeight: 600, fontSize: 13, overflow: "hidden", textOverflow: "ellipsis", whiteSpace: "nowrap", marginBottom: 4 }}>{p.title}</div>
                        <div style={{ fontSize: 15, fontWeight: 700, color: "#4ade80" }}>{p.price?.toLocaleString()} {p.currency}</div>
                      </div>
                    </div>
                  );
                })}
              </div>
            )}
          </div>
        )}

        {/* UPLOAD TAB */}
        {tab === "upload" && (
          <div style={{ flex: 1, overflowY: "auto", padding: "20px 16px", display: "flex", flexDirection: "column", alignItems: "center" }}>
            <div style={{ maxWidth: 380, width: "100%" }}>
              <h3 style={{ margin: "0 0 8px", fontSize: 18 }}>{t.uploadTitle}</h3>
              <p style={{ color: "#64748b", fontSize: 14, lineHeight: 1.5, margin: "0 0 20px" }}>{t.uploadDesc}</p>
              <input ref={fileInput} type="file" accept="image/*" capture="environment" onChange={onPhotoChange} style={{ display: "none" }} />
              <button onClick={() => fileInput.current?.click()} style={{ width: "100%", padding: "14px", borderRadius: 10, border: "2px dashed #334155", background: "#1e293b", color: "#94a3b8", cursor: "pointer", fontSize: 15, marginBottom: 16 }}>
                📷 {t.uploadBtn}
              </button>
              {photoPreview && (
                <div style={{ marginBottom: 16 }}>
                  <img src={photoPreview} style={{ width: "100%", maxHeight: 280, objectFit: "cover", borderRadius: 10, marginBottom: 12 }} alt="preview" />
                  <div style={{ fontSize: 13, color: "#64748b", marginBottom: 10 }}>📎 {photoFile?.name}</div>
                  <button onClick={analyzePhoto} disabled={analyzing}
                    style={{ width: "100%", padding: 14, borderRadius: 10, border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer", fontSize: 15, fontWeight: 600, opacity: analyzing ? 0.6 : 1 }}>
                    {analyzing ? t.analyzing : t.analyzeBtn}
                  </button>
                </div>
              )}
              <div style={{ marginTop: 20, padding: "12px 14px", background: "#1e293b", borderRadius: 10, fontSize: 13, color: "#64748b" }}>
                {lang === "fr"
                  ? "Après analyse, Léa vous donnera le type de machine, son état apparent et une estimation de valeur."
                  : "Após a análise, Léa indicará o tipo de máquina, o estado aparente e uma estimativa de valor."}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* ── Standardiste floating widget ─────────────────────────────────── */}
      {/* Floating button */}
      {!stdOpen && (
        <button onClick={() => setStdOpen(true)} style={{
          position: "fixed", bottom: 80, right: 16, zIndex: 100,
          width: 54, height: 54, borderRadius: "50%", border: "2px solid #334155",
          background: "#0f172a", color: "#60a5fa", fontSize: 24, cursor: "pointer",
          display: "flex", alignItems: "center", justifyContent: "center",
          boxShadow: "0 4px 20px rgba(0,0,0,0.5)",
        }} title="Standardiste LEGA">
          📞
        </button>
      )}

      {/* Standardiste panel */}
      {stdOpen && (
        <div style={{
          position: "fixed", inset: 0, zIndex: 200,
          background: "#0a1628", display: "flex", flexDirection: "column",
        }}>
          {/* Header */}
          <div style={{ background: "#0f172a", borderBottom: "1px solid #1e293b", padding: "12px 16px", display: "flex", justifyContent: "space-between", alignItems: "center", flexShrink: 0 }}>
            <div>
              <div style={{ fontWeight: 700, fontSize: 16 }}>📞 Standardiste LEGA</div>
              <div style={{ fontSize: 11, color: "#64748b" }}>
                {stdLang === "fr" ? "Léa — Réception multilingue" : stdLang === "pt" ? "Léa — Receção multilingue" : "Lea — Multilingual reception"}
              </div>
            </div>
            <div style={{ display: "flex", gap: 8, alignItems: "center" }}>
              {(["fr", "pt", "en"] as StdLang[]).map(l => (
                <button key={l} onClick={() => setStdLang(l)} style={{
                  padding: "3px 8px", borderRadius: 5, fontSize: 11, fontWeight: 600, cursor: "pointer",
                  border: "1px solid #334155",
                  background: stdLang === l ? "#3b82f6" : "#1e293b",
                  color: stdLang === l ? "#fff" : "#94a3b8",
                }}>{l.toUpperCase()}</button>
              ))}
              <button onClick={() => {
                if (!audioCtxRef.current) audioCtxRef.current = new AudioContext();
                setTtsEnabled(v => !v);
              }} title={ttsEnabled ? "Couper le son" : "Activer le son"} style={{
                width: 30, height: 30, borderRadius: "50%", border: "1px solid #334155",
                background: ttsEnabled ? "#3b82f6" : "#1e293b", color: "#fff", cursor: "pointer", fontSize: 14,
              }}>{ttsEnabled ? "🔊" : "🔇"}</button>
              <button onClick={() => setStdOpen(false)} style={{
                width: 30, height: 30, borderRadius: "50%", border: "1px solid #334155",
                background: "#1e293b", color: "#94a3b8", cursor: "pointer", fontSize: 16,
              }}>✕</button>
            </div>
          </div>

          {/* Messages */}
          <div style={{ flex: 1, overflowY: "auto", padding: "14px 16px", display: "flex", flexDirection: "column", gap: 10 }}>
            {stdMsgs.map((m, i) => (
              <div key={i} style={{ display: "flex", flexDirection: "column", alignItems: m.role === "user" ? "flex-end" : "flex-start" }}>
                {m.role === "agent" && (
                  <div style={{ fontSize: 11, color: "#475569", marginBottom: 3, paddingLeft: 4 }}>👩‍💼 Léa</div>
                )}
                <div style={{
                  maxWidth: "85%", padding: "10px 14px",
                  borderRadius: m.role === "user" ? "14px 14px 4px 14px" : "14px 14px 14px 4px",
                  background: m.role === "user" ? "#2563eb" : "#1e293b",
                  color: "#fff", fontSize: 14, lineHeight: 1.55, whiteSpace: "pre-wrap", wordBreak: "break-word",
                }}>
                  {m.text}
                </div>
                {m.time && <span style={{ fontSize: 10, color: "#475569", marginTop: 2, paddingInline: 4 }}>{m.time}</span>}
              </div>
            ))}
            {stdLoading && (
              <div style={{ display: "flex", alignItems: "flex-start", gap: 8 }}>
                <div style={{ padding: "10px 14px", background: "#1e293b", borderRadius: "14px 14px 14px 4px", color: "#64748b", fontSize: 14 }}>
                  {stdLang === "fr" ? "Léa réfléchit..." : stdLang === "pt" ? "Léa a pensar..." : "Lea is thinking..."}
                </div>
              </div>
            )}
            <div ref={stdEnd} />
          </div>

          {/* Input */}
          <div style={{ padding: "10px 12px", borderTop: "1px solid #1e293b", background: "#0f172a", display: "flex", gap: 8 }}>
            <input
              value={stdInput}
              onChange={e => setStdInput(e.target.value)}
              onKeyDown={e => e.key === "Enter" && !e.shiftKey && stdSend()}
              placeholder={stdLang === "fr" ? "Votre message à Léa..." : stdLang === "pt" ? "A sua mensagem para Léa..." : "Your message to Lea..."}
              autoFocus
              style={{ flex: 1, padding: "11px 14px", borderRadius: 24, border: "1px solid #334155", background: "#1e293b", color: "#f8fafc", fontSize: 15, outline: "none" }}
            />
            <button onClick={stdSend} disabled={!stdInput.trim() || stdLoading}
              style={{ width: 46, height: 46, borderRadius: "50%", border: "none", background: "#3b82f6", color: "#fff", cursor: "pointer", fontSize: 20, display: "flex", alignItems: "center", justifyContent: "center", flexShrink: 0, opacity: stdInput.trim() && !stdLoading ? 1 : 0.4 }}>
              ➤
            </button>
          </div>
        </div>
      )}

      {/* Bottom tab bar */}
      <div style={{ display: "flex", borderTop: "1px solid #1e293b", background: "#0a1628", flexShrink: 0 }}>
        {(["chat", "catalogue", "upload"] as Tab[]).map(id => (
          <button key={id} onClick={() => setTab(id)}
            style={{ flex: 1, padding: "12px 0 10px", border: "none", background: "transparent", cursor: "pointer", display: "flex", flexDirection: "column", alignItems: "center", gap: 3,
              color: tab === id ? "#60a5fa" : "#64748b", borderTop: tab === id ? "2px solid #3b82f6" : "2px solid transparent" }}>
            <span style={{ fontSize: 20 }}>{t.tabs[id].split(" ")[0]}</span>
            <span style={{ fontSize: 10, fontWeight: tab === id ? 600 : 400 }}>{t.tabs[id].split(" ").slice(1).join(" ")}</span>
          </button>
        ))}
      </div>
    </div>
  );
}
