'use client';
import { useState, useEffect, useRef } from 'react';

const SITE_API = process.env.NEXT_PUBLIC_SITE_API_URL || 'http://76.13.141.221:8003/api/site';
const tok = () => localStorage.getItem('bvi_token') || '';
const ah = () => ({ Authorization: `Bearer ${tok()}` });
const ahj = () => ({ ...ah(), 'Content-Type': 'application/json' });

const input: React.CSSProperties = {
  width: '100%', padding: '8px 12px', borderRadius: 7, border: '1px solid #334155',
  background: '#0f172a', color: '#e2e8f0', fontSize: 13, boxSizing: 'border-box',
};
const card: React.CSSProperties = { background: '#1e293b', border: '1px solid #334155', borderRadius: 10, padding: 16, marginBottom: 16 };
const badge = (c: string): React.CSSProperties => ({ display: 'inline-block', padding: '2px 8px', borderRadius: 20, fontSize: 11, fontWeight: 600, background: c + '22', color: c, border: `1px solid ${c}44` });

const STATUS_COLORS: Record<string, string> = { available: '#4ade80', sold: '#f87171', reserved: '#fb923c', new: '#60a5fa', archived: '#64748b' };

type Tab = 'config' | 'products' | 'sections' | 'translations' | 'import';

export default function SiteVitrinePage() {
  const [tab, setTab] = useState<Tab>('config');
  const [msg, setMsg] = useState('');
  const flash = (m: string) => { setMsg(m); setTimeout(() => setMsg(''), 4000); };

  // ── Config ─────────────────────────────────────────────────────────────────
  const [cfg, setCfg] = useState<Record<string, string>>({});
  const [cfgDirty, setCfgDirty] = useState<Record<string, string>>({});
  const logoRef = useRef<HTMLInputElement>(null);
  const heroRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    fetch(`${SITE_API}/config`, { headers: ah() })
      .then(r => r.json()).then((rows: any[]) => {
        const m: Record<string, string> = {};
        rows.forEach(r => { m[r.key] = r.value || ''; });
        setCfg(m); setCfgDirty(m);
      }).catch(() => {});
  }, []);

  const saveConfig = async () => {
    const changed: Record<string, string> = {};
    Object.entries(cfgDirty).forEach(([k, v]) => { if (v !== cfg[k]) changed[k] = v; });
    if (!Object.keys(changed).length) { flash('Aucune modification'); return; }
    await fetch(`${SITE_API}/config/bulk`, { method: 'POST', headers: ahj(), body: JSON.stringify(changed) });
    setCfg({ ...cfg, ...changed }); flash(`✅ ${Object.keys(changed).length} champ(s) sauvegardé(s)`);
  };

  const uploadAsset = async (type: 'logo' | 'hero', file: File) => {
    const fd = new FormData(); fd.append('file', file); fd.append('asset_type', type);
    const res = await fetch(`${SITE_API}/upload?asset_type=${type}`, { method: 'POST', headers: ah(), body: fd });
    const d = await res.json();
    if (d.url) { setCfg(p => ({ ...p, [type]: `http://76.13.141.221:8003${d.url}` })); flash(`✅ ${type} uploadé`); }
  };

  const cfgField = (key: string, label: string, type: 'text' | 'color' = 'text') => (
    <div style={{ marginBottom: 12 }}>
      <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 4, textTransform: 'uppercase', letterSpacing: '0.05em' }}>{label}</label>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        {type === 'color' && (
          <input type="color" value={cfgDirty[key] || '#000000'} onChange={e => setCfgDirty(p => ({ ...p, [key]: e.target.value }))}
            style={{ width: 40, height: 36, padding: 2, border: '1px solid #334155', borderRadius: 6, background: '#0f172a', cursor: 'pointer' }} />
        )}
        <input style={input} type="text" value={cfgDirty[key] || ''} onChange={e => setCfgDirty(p => ({ ...p, [key]: e.target.value }))} />
      </div>
    </div>
  );

  // ── Products ───────────────────────────────────────────────────────────────
  const [products, setProducts] = useState<any[]>([]);
  const [total, setTotal] = useState(0);
  const [pFilter, setPFilter] = useState('all');
  const [showForm, setShowForm] = useState(false);
  const [editProd, setEditProd] = useState<any>(null);
  const [form, setForm] = useState({ title: '', category: 'machines_tp', brand: '', model: '', year: '', hours: '', price: '', currency: 'EUR', location: '', description: '', status: 'available', source_url: '' });
  const imgRef = useRef<HTMLInputElement>(null);

  const loadProducts = () => {
    const url = pFilter === 'all' ? `${SITE_API}/products?limit=50` : `${SITE_API}/products?limit=50&status=${pFilter}`;
    fetch(url, { headers: ah() }).then(r => r.json()).then(d => { setProducts(d.items || []); setTotal(d.total || 0); }).catch(() => {});
  };
  useEffect(() => { if (tab === 'products') loadProducts(); }, [tab, pFilter]);

  const openNew = () => { setEditProd(null); setForm({ title: '', category: 'machines_tp', brand: '', model: '', year: '', hours: '', price: '', currency: 'EUR', location: '', description: '', status: 'available', source_url: '' }); setShowForm(true); };
  const openEdit = (p: any) => { setEditProd(p); setForm({ title: p.title, category: p.category || 'machines_tp', brand: p.brand || '', model: p.model || '', year: p.year || '', hours: p.hours || '', price: p.price || '', currency: p.currency || 'EUR', location: p.location || '', description: p.description || '', status: p.status || 'available', source_url: p.source_url || '' }); setShowForm(true); };

  const saveProduct = async () => {
    const body = { ...form, year: form.year ? parseInt(form.year as any) : null, hours: form.hours ? parseInt(form.hours as any) : null, price: form.price ? parseFloat(form.price as any) : null, specs: {}, images: editProd?.images ? (typeof editProd.images === 'string' ? JSON.parse(editProd.images) : editProd.images) : [] };
    if (editProd) {
      await fetch(`${SITE_API}/products/${editProd.id}`, { method: 'PUT', headers: ahj(), body: JSON.stringify(body) });
      flash('✅ Produit mis à jour');
    } else {
      await fetch(`${SITE_API}/products`, { method: 'POST', headers: ahj(), body: JSON.stringify(body) });
      flash('✅ Produit créé');
    }
    setShowForm(false); loadProducts();
  };

  const archiveProd = async (id: string) => {
    if (!confirm('Archiver ce produit ?')) return;
    await fetch(`${SITE_API}/products/${id}`, { method: 'DELETE', headers: ah() });
    flash('🗑️ Archivé'); loadProducts();
  };

  const uploadImg = async (productId: string) => {
    const file = imgRef.current?.files?.[0]; if (!file) return;
    const fd = new FormData(); fd.append('file', file);
    const res = await fetch(`${SITE_API}/products/${productId}/upload`, { method: 'POST', headers: ah(), body: fd });
    const d = await res.json(); if (d.url) { flash('📷 Image uploadée'); loadProducts(); }
  };

  // ── Sections ───────────────────────────────────────────────────────────────
  const [sections, setSections] = useState<any[]>([]);
  useEffect(() => { if (tab === 'sections') fetch(`${SITE_API}/sections`, { headers: ah() }).then(r => r.json()).then(setSections).catch(() => {}); }, [tab]);
  const toggleSection = async (name: string, enabled: boolean) => {
    await fetch(`${SITE_API}/sections/${name}`, { method: 'PATCH', headers: ahj(), body: JSON.stringify({ enabled }) });
    setSections(s => s.map(x => x.name === name ? { ...x, enabled } : x));
  };

  // ── Translations ───────────────────────────────────────────────────────────
  const LANGS = ['fr', 'pt', 'en', 'es', 'de', 'it', 'ar', 'nl', 'zh'];
  const [tlLang, setTlLang] = useState('fr');
  const [tlData, setTlData] = useState<Record<string, string>>({});
  const [tlDirty, setTlDirty] = useState<Record<string, string>>({});
  const [tlSaving, setTlSaving] = useState(false);

  useEffect(() => {
    if (tab !== 'translations') return;
    fetch(`${SITE_API}/translations/${tlLang}`, { headers: ah() })
      .then(r => r.json())
      .then((d: Record<string, string>) => { setTlData(d); setTlDirty(d); })
      .catch(() => {});
  }, [tab, tlLang]);

  const saveTl = async () => {
    const changed: Record<string, string> = {};
    Object.entries(tlDirty).forEach(([k, v]) => { if (v !== tlData[k]) changed[k] = v; });
    if (!Object.keys(changed).length) { flash('Aucune modification'); return; }
    setTlSaving(true);
    await fetch(`${SITE_API}/translations/bulk`, {
      method: 'PUT', headers: ahj(),
      body: JSON.stringify({ lang: tlLang, translations: changed }),
    });
    setTlData(p => ({ ...p, ...changed }));
    setTlSaving(false);
    flash(`✅ ${Object.keys(changed).length} clé(s) sauvegardée(s) [${tlLang}]`);
  };

  // ── Import ─────────────────────────────────────────────────────────────────
  const [importing, setImporting] = useState(false);
  const [importResult, setImportResult] = useState<any>(null);
  const [maxItems, setMaxItems] = useState('20');

  const runImport = async () => {
    setImporting(true); setImportResult(null);
    const res = await fetch(`${SITE_API}/import/tob`, { method: 'POST', headers: ahj(), body: JSON.stringify({ max_items: parseInt(maxItems) || 20 }) });
    const d = await res.json(); setImportResult(d); setImporting(false);
    if (d.inserted > 0) flash(`✅ ${d.inserted} annonce(s) importée(s)`);
    else if (d.ok) flash('ℹ️ Aucune nouvelle annonce (déjà importées)');
  };

  const TABS: { id: Tab; label: string }[] = [{ id: 'config', label: '⚙️ Config' }, { id: 'products', label: '📦 Produits' }, { id: 'sections', label: '🧩 Sections' }, { id: 'translations', label: '🌍 Traductions' }, { id: 'import', label: '🔄 Import tob.pt' }];

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 20 }}>
        <h2 style={{ margin: 0, fontSize: 20 }}>🌐 Site Vitrine</h2>
        <a href="http://76.13.141.221:3002" target="_blank" rel="noopener" style={{ fontSize: 12, color: '#60a5fa', textDecoration: 'none' }}>Voir le site ↗</a>
      </div>

      {/* Tabs */}
      <div style={{ display: 'flex', gap: 8, marginBottom: 20, borderBottom: '1px solid #1e293b', paddingBottom: 8 }}>
        {TABS.map(t => (
          <button key={t.id} onClick={() => setTab(t.id)} style={{ padding: '6px 14px', borderRadius: 6, border: 'none', cursor: 'pointer', fontSize: 13, fontWeight: tab === t.id ? 600 : 400, background: tab === t.id ? '#3b82f620' : 'transparent', color: tab === t.id ? '#60a5fa' : '#94a3b8' }}>
            {t.label}
          </button>
        ))}
      </div>

      {msg && <div style={{ marginBottom: 14, padding: '8px 14px', background: '#1e293b', borderRadius: 8, color: '#4ade80', fontSize: 13 }}>{msg}</div>}

      {/* ── CONFIG ── */}
      {tab === 'config' && (
        <div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 14, color: '#e2e8f0' }}>Identité</strong>
              {cfgField('site_name', 'Nom du site')}
              {cfgField('slogan_pt', 'Slogan PT')}
              {cfgField('slogan_fr', 'Slogan FR')}
              {cfgField('slogan_en', 'Slogan EN')}
            </div>
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 14, color: '#e2e8f0' }}>Coordonnées</strong>
              {cfgField('phone', 'Téléphone')}
              {cfgField('email', 'Email')}
              {cfgField('address', 'Adresse')}
            </div>
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 14, color: '#e2e8f0' }}>Apparence</strong>
              {cfgField('color_primary', 'Couleur primaire (bleu)', 'color')}
              {cfgField('color_secondary', 'Couleur secondaire (orange)', 'color')}
            </div>
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 14, color: '#e2e8f0' }}>Statistiques hero</strong>
              {cfgField('stat_machines', 'Nb machines')}
              {cfgField('stat_langues', 'Nb langues')}
              {cfgField('stat_pays', 'Nb pays')}
              {cfgField('stat_support', 'Support')}
            </div>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 16 }}>
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 12, color: '#e2e8f0' }}>Upload Logo</strong>
              {cfg.logo && <img src={cfg.logo} alt="logo" style={{ height: 50, marginBottom: 10, borderRadius: 4 }} />}
              <input ref={logoRef} type="file" accept=".jpg,.jpeg,.png,.webp,.svg" onChange={e => e.target.files?.[0] && uploadAsset('logo', e.target.files[0])} style={{ fontSize: 13, color: '#94a3b8' }} />
            </div>
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 12, color: '#e2e8f0' }}>Image Hero</strong>
              {cfg.hero && <img src={cfg.hero} alt="hero" style={{ width: '100%', height: 80, objectFit: 'cover', borderRadius: 6, marginBottom: 10 }} />}
              <input ref={heroRef} type="file" accept=".jpg,.jpeg,.png,.webp" onChange={e => e.target.files?.[0] && uploadAsset('hero', e.target.files[0])} style={{ fontSize: 13, color: '#94a3b8' }} />
            </div>
          </div>
          <button onClick={saveConfig} style={{ padding: '10px 28px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: 'pointer', fontSize: 14 }}>💾 Sauvegarder la config</button>
        </div>
      )}

      {/* ── PRODUCTS ── */}
      {tab === 'products' && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 14, flexWrap: 'wrap', gap: 10 }}>
            <div style={{ display: 'flex', gap: 8, flexWrap: 'wrap' }}>
              {['all', 'available', 'reserved', 'sold', 'archived'].map(s => (
                <button key={s} onClick={() => setPFilter(s)} style={{ padding: '5px 12px', borderRadius: 6, border: '1px solid', cursor: 'pointer', fontSize: 12, fontWeight: 600, borderColor: pFilter === s ? (STATUS_COLORS[s] || '#60a5fa') : '#334155', background: pFilter === s ? ((STATUS_COLORS[s] || '#60a5fa') + '22') : '#1e293b', color: pFilter === s ? (STATUS_COLORS[s] || '#60a5fa') : '#94a3b8' }}>
                  {s === 'all' ? 'Tout' : s} {pFilter === s && `(${total})`}
                </button>
              ))}
            </div>
            <button onClick={openNew} style={{ padding: '6px 16px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: 6, cursor: 'pointer', fontWeight: 600, fontSize: 13 }}>+ Nouveau</button>
          </div>

          {showForm && (
            <div style={{ ...card, border: '1px solid #3b82f6' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: 12 }}>
                <strong>{editProd ? 'Modifier' : 'Nouveau produit'}</strong>
                <button onClick={() => setShowForm(false)} style={{ background: 'none', border: 'none', color: '#64748b', cursor: 'pointer' }}>✕</button>
              </div>
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
                {[['title', 'Titre *'], ['brand', 'Marque'], ['model', 'Modèle'], ['location', 'Localisation'], ['year', 'Année'], ['hours', 'Heures'], ['price', 'Prix (€)'], ['source_url', 'URL source']].map(([k, lbl]) => (
                  <div key={k}>
                    <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 3 }}>{lbl}</label>
                    <input style={input} value={(form as any)[k]} onChange={e => setForm(p => ({ ...p, [k]: e.target.value }))} />
                  </div>
                ))}
                <div>
                  <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 3 }}>Catégorie</label>
                  <select style={input} value={form.category} onChange={e => setForm(p => ({ ...p, category: e.target.value }))}>
                    {['machines_tp', 'trucks', 'trailers', 'vans'].map(c => <option key={c} value={c}>{c}</option>)}
                  </select>
                </div>
                <div>
                  <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 3 }}>Statut</label>
                  <select style={input} value={form.status} onChange={e => setForm(p => ({ ...p, status: e.target.value }))}>
                    {['available', 'reserved', 'sold', 'new', 'archived'].map(s => <option key={s} value={s}>{s}</option>)}
                  </select>
                </div>
              </div>
              <div style={{ marginTop: 10 }}>
                <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 3 }}>Description</label>
                <textarea style={{ ...input, minHeight: 60, resize: 'vertical' }} value={form.description} onChange={e => setForm(p => ({ ...p, description: e.target.value }))} />
              </div>
              {editProd && (
                <div style={{ marginTop: 10, display: 'flex', alignItems: 'center', gap: 10 }}>
                  <input ref={imgRef} type="file" accept=".jpg,.jpeg,.png,.webp" style={{ fontSize: 12, color: '#94a3b8' }} />
                  <button onClick={() => uploadImg(editProd.id)} style={{ padding: '5px 12px', background: '#1e293b', border: '1px solid #334155', borderRadius: 6, color: '#e2e8f0', cursor: 'pointer', fontSize: 12 }}>📷 Upload image</button>
                </div>
              )}
              <div style={{ marginTop: 14, display: 'flex', gap: 10 }}>
                <button onClick={saveProduct} disabled={!form.title} style={{ padding: '8px 20px', background: '#3b82f6', color: '#fff', border: 'none', borderRadius: 7, fontWeight: 600, cursor: 'pointer' }}>💾 Enregistrer</button>
                <button onClick={() => setShowForm(false)} style={{ padding: '8px 16px', background: '#1e293b', border: '1px solid #334155', borderRadius: 7, color: '#94a3b8', cursor: 'pointer' }}>Annuler</button>
              </div>
            </div>
          )}

          <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
            {products.map(p => {
              const imgs = typeof p.images === 'string' ? JSON.parse(p.images || '[]') : (p.images || []);
              return (
                <div key={p.id} style={{ background: '#1e293b', border: '1px solid #334155', borderRadius: 8, padding: '10px 14px', display: 'flex', alignItems: 'center', gap: 12, flexWrap: 'wrap' }}>
                  {imgs[0] && <img src={imgs[0].startsWith('/uploads') ? `http://76.13.141.221:8003${imgs[0]}` : imgs[0]} alt="" style={{ width: 56, height: 40, objectFit: 'cover', borderRadius: 4, flexShrink: 0 }} />}
                  <div style={{ flex: 1, minWidth: 0 }}>
                    <div style={{ fontWeight: 600, fontSize: 13, color: '#e2e8f0', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{p.title}</div>
                    <div style={{ fontSize: 11, color: '#64748b' }}>{p.brand} {p.model} {p.year ? `· ${p.year}` : ''} {p.hours ? `· ${p.hours.toLocaleString()}h` : ''}</div>
                  </div>
                  <span style={{ fontWeight: 700, color: '#60a5fa', fontSize: 14, flexShrink: 0 }}>{p.price ? `${parseInt(p.price).toLocaleString()}€` : '—'}</span>
                  <span style={badge(STATUS_COLORS[p.status] || '#64748b')}>{p.status}</span>
                  <div style={{ display: 'flex', gap: 6 }}>
                    <button onClick={() => openEdit(p)} style={{ padding: '4px 10px', background: '#1e3a5f', border: '1px solid #3b82f6', borderRadius: 5, color: '#60a5fa', cursor: 'pointer', fontSize: 12 }}>✏️</button>
                    <button onClick={() => archiveProd(p.id)} style={{ padding: '4px 10px', background: '#450a0a', border: '1px solid #7f1d1d', borderRadius: 5, color: '#f87171', cursor: 'pointer', fontSize: 12 }}>🗑️</button>
                  </div>
                </div>
              );
            })}
            {products.length === 0 && <div style={{ textAlign: 'center', padding: 40, color: '#475569' }}>Aucun produit</div>}
          </div>
        </div>
      )}

      {/* ── SECTIONS ── */}
      {tab === 'sections' && (
        <div>
          <p style={{ color: '#64748b', fontSize: 13, marginBottom: 16 }}>Activez ou désactivez les sections du site vitrine.</p>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
            {sections.map(s => (
              <div key={s.name} style={{ ...card, display: 'flex', alignItems: 'center', justifyContent: 'space-between', padding: '12px 16px', marginBottom: 0 }}>
                <div>
                  <div style={{ fontWeight: 600, fontSize: 14, color: '#e2e8f0' }}>{s.display_name}</div>
                  <div style={{ fontSize: 11, color: '#64748b' }}>Position {s.position} · <code style={{ color: '#60a5fa' }}>{s.name}</code></div>
                </div>
                <button onClick={() => toggleSection(s.name, !s.enabled)} style={{ padding: '6px 16px', borderRadius: 6, border: 'none', cursor: 'pointer', fontWeight: 600, fontSize: 12, background: s.enabled ? '#4ade8033' : '#f8717133', color: s.enabled ? '#4ade80' : '#f87171' }}>
                  {s.enabled ? '✅ Actif' : '⏹ Désactivé'}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* ── TRANSLATIONS ── */}
      {tab === 'translations' && (
        <div>
          <div style={{ display: 'flex', gap: 8, marginBottom: 16, alignItems: 'center', flexWrap: 'wrap' }}>
            {LANGS.map(l => (
              <button key={l} onClick={() => setTlLang(l)} style={{ padding: '5px 14px', borderRadius: 6, border: '1px solid', cursor: 'pointer', fontSize: 13, fontWeight: tlLang === l ? 700 : 400, borderColor: tlLang === l ? '#3b82f6' : '#334155', background: tlLang === l ? '#3b82f620' : '#1e293b', color: tlLang === l ? '#60a5fa' : '#94a3b8' }}>
                {l.toUpperCase()}
              </button>
            ))}
            <button onClick={saveTl} disabled={tlSaving} style={{ marginLeft: 'auto', padding: '6px 20px', background: tlSaving ? '#334155' : '#3b82f6', color: '#fff', border: 'none', borderRadius: 7, fontWeight: 700, cursor: tlSaving ? 'not-allowed' : 'pointer', fontSize: 13 }}>
              {tlSaving ? '⏳ Sauvegarde...' : '💾 Sauvegarder'}
            </button>
          </div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 10 }}>
            {Object.entries(tlDirty).map(([key, val]) => (
              <div key={key} style={{ background: val !== tlData[key] ? '#1e3a5f' : '#1e293b', border: `1px solid ${val !== tlData[key] ? '#3b82f6' : '#334155'}`, borderRadius: 8, padding: '10px 12px' }}>
                <label style={{ display: 'block', fontSize: 10, color: '#64748b', marginBottom: 4, fontFamily: 'monospace', textTransform: 'uppercase', letterSpacing: '0.05em' }}>{key}</label>
                <input
                  style={{ ...input, fontSize: 13 }}
                  value={val}
                  onChange={e => setTlDirty(p => ({ ...p, [key]: e.target.value }))}
                />
              </div>
            ))}
          </div>
          {Object.keys(tlDirty).length === 0 && <div style={{ textAlign: 'center', padding: 40, color: '#475569' }}>Chargement…</div>}
        </div>
      )}

      {/* ── IMPORT ── */}
      {tab === 'import' && (
        <div>
          <div style={{ ...card, marginBottom: 14, background: '#0f2a1e', border: '1px solid #166534' }}>
            <strong style={{ display: 'block', marginBottom: 8, color: '#4ade80', fontSize: 13 }}>⏰ Cron scraper actif — toutes les 24h</strong>
            <p style={{ fontSize: 12, color: '#64748b', margin: '0 0 12px' }}>
              Le backend scrape automatiquement tob.pt toutes les 24h au démarrage du container.
              Seules les nouvelles annonces (source_url inconnue) sont insérées.
            </p>
            <button onClick={runImport} disabled={importing} style={{ padding: '8px 20px', background: importing ? '#334155' : '#166534', color: '#4ade80', border: '1px solid #166534', borderRadius: 6, fontWeight: 700, cursor: importing ? 'not-allowed' : 'pointer', fontSize: 13 }}>
              {importing ? '⏳ Scrape en cours...' : '▶ Lancer un scrape maintenant'}
            </button>
          </div>
          <div style={card}>
            <strong style={{ display: 'block', marginBottom: 12, color: '#e2e8f0' }}>Import manuel depuis tob.pt</strong>
            <p style={{ fontSize: 13, color: '#64748b', margin: '0 0 14px' }}>
              Importe les annonces machines depuis le catalogue <strong style={{ color: '#94a3b8' }}>tob.pt/pt/machinery.aspx</strong>.
              Les annonces déjà importées sont ignorées (déduplication par URL).
            </p>
            <label style={{ display: 'block', fontSize: 11, color: '#94a3b8', marginBottom: 6, textTransform: 'uppercase' }}>Nombre max d'annonces</label>
            <input style={{ ...input, width: 120, marginBottom: 14 }} type="number" min={1} max={200} value={maxItems} onChange={e => setMaxItems(e.target.value)} />
            <div style={{ marginBottom: 14, fontSize: 12, color: '#475569' }}>
              ℹ️ tob.pt ne propose pas de recherche par mot-clé — l'import couvre tout le catalogue machines.
            </div>
            <button onClick={runImport} disabled={importing} style={{ padding: '10px 24px', background: importing ? '#334155' : '#3b82f6', color: '#fff', border: 'none', borderRadius: 8, fontWeight: 700, cursor: importing ? 'not-allowed' : 'pointer', fontSize: 14 }}>
              {importing ? '⏳ Import en cours...' : '🔄 Lancer l\'import'}
            </button>
          </div>
          {importResult && (
            <div style={card}>
              <strong style={{ display: 'block', marginBottom: 10, color: '#4ade80' }}>Résultat : {importResult.inserted} annonce(s) insérée(s)</strong>
              {importResult.items?.map((item: any, i: number) => (
                <div key={i} style={{ fontSize: 13, color: '#94a3b8', padding: '4px 0', borderBottom: '1px solid #1e293b' }}>
                  {item.title} {item.price ? `— ${parseInt(item.price).toLocaleString()}€` : ''}
                </div>
              ))}
              {importResult.errors?.length > 0 && (
                <div style={{ marginTop: 10 }}>
                  <strong style={{ fontSize: 12, color: '#f87171' }}>Erreurs :</strong>
                  {importResult.errors.map((e: string, i: number) => <div key={i} style={{ fontSize: 12, color: '#f87171' }}>{e}</div>)}
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  );
}
