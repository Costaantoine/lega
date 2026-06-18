# Plan — Page "Bientôt disponible" temporaire pour la vitrine LEGA.PT

> **Pour Hermes :** Exécuter avec le skill `subagent-driven-development` si delegation, ou manuellement tâche par tâche.

**Objectif :** Afficher uniquement l'image hero avec "Bientôt disponible" sur le site vitrine (port 3002), tout en gardant le site complet fonctionnel en arrière-plan, accessible via un paramètre secret.

**Architecture :** Un seul fichier modifié — `page.tsx`. Ajout d'un mode "coming soon" contrôlé par query parameter `?preview=true`. En mode normal, seule une full-screen hero image s'affiche. En mode preview, tout le site normal est visible.

**Tech Stack :** Next.js (inline styles, sans Tailwind), TypeScript, `useSearchParams`

**Contrainte :** temporaire = facile à enlever. Pas de nouveau composant, pas de changement de route. Le site en arrière-plan continue de fonctionner (API, DB, WebSocket, chat Léa, tout est intact).

---

## Tâche 1 : Ajouter la détection du mode preview

**Objectif :** Lire un paramètre d'URL `?preview=true` pour activer le mode site complet.

**Fichier :**
- Modifier : `/opt/bvi/vitrine/frontend/app/page.tsx:79-127` (dans `LegaSite()`, après les `useState` et avant le premier `useEffect`)

**Changement :**
Ajouter un `useSearchParams` (ou `window.location.search` pour éviter le wrapper Suspense) pour détecter le mode preview.

Étape 1 — Ajouter l'import de `useSearchParams` :
```tsx
// Ligne 2 : remplacer le import
import { useState, useEffect, useCallback, useRef } from "react";
// par :
import { useState, useEffect, useCallback, useRef, useMemo } from "react";
```

Étape 2 — Après la ligne 127 (fin des useState) :
```tsx
// Mode preview : ?preview=true affiche le site complet
const isPreview = useMemo(() => {
  if (typeof window === "undefined") return false;
  return new URLSearchParams(window.location.search).get("preview") === "true";
}, []);
```

## Tâche 2 : Modifier le render conditionnel

**Objectif :** Si pas en mode preview, afficher uniquement la hero image + "Bientôt disponible", sans navbar ni footer ni aucun autre contenu. Si preview, afficher le site complet comme avant.

**Fichier :**
- Modifier : `/opt/bvi/vitrine/frontend/app/page.tsx` (le return du render, autour de la ligne 372)

**Changement :**
Remplacer le début du render par une condition. Le mode coming soon inclut les drapeaux de langue en haut à droite (comme la navbar normale) :

```tsx
  // ── Render ───────────────────────────────────────────────────────────────
  // Mode "Coming Soon" — que si pas en preview
  if (!preview) {
    return (
      <div style={s({ minHeight: "100vh", background: "#f8fafc", overflow: "hidden" })}>
        {/* ── Language selector flottant ── */}
        <div style={s({
          position: "fixed", top: 16, right: 16, zIndex: 100,
          display: "flex", gap: 6,
        })}>
          {LANGS.map(l => (
            <button key={l.code} onClick={() => setLang(l.code)}
              style={s({
                display: "flex", alignItems: "center", gap: 4,
                padding: "6px 10px", border: "none", borderRadius: 6,
                cursor: "pointer", fontSize: 12, fontWeight: 600,
                background: lang === l.code ? C2 : "rgba(0,0,0,0.35)",
                color: lang === l.code ? "#fff" : "rgba(255,255,255,0.8)",
                backdropFilter: "blur(4px)",
              })}>
              {/* eslint-disable-next-line @next/next/no-img-element */}
              <img src={l.flag} alt={l.short} width={20} height={15}
                style={{ borderRadius: "2px", objectFit: "cover" }} />
              {l.short}
            </button>
          ))}
        </div>

        <HeroCarousel siteBase={SITE_BASE} colorPrimary={C1} colorSecondary={C2}>
          <div style={s({
            display: "flex", flexDirection: "column",
            alignItems: "center", justifyContent: "center",
            minHeight: "60vh",
          })}>
            <h1 style={s({
              fontSize: "clamp(36px, 8vw, 72px)",
              fontWeight: 800, margin: "0 0 16px",
              lineHeight: 1.15, letterSpacing: "-0.03em",
              textShadow: "0 2px 20px rgba(0,0,0,0.3)",
            })}>
              Bientôt Disponible
            </h1>
            <p style={s({
              fontSize: "clamp(16px, 3vw, 24px)",
              margin: "0 0 40px", opacity: 0.9,
              maxWidth: 500, textAlign: "center",
            })}>
              LEGA.PT arrive bientôt. Restez connecté pour découvrir notre sélection de machines TP et véhicules.
            </p>
          </div>
        </HeroCarousel>
      </div>
    );
  }
```

Et le render normal (site complet) reste inchangé, mais commence maintenant après ce bloc.

**Important :** Le condition `if (!preview)` doit être placée **avant** le `<div dir={...}>` de la ligne 372, et le rendu complet du site reste dans le return final du composant inchangé.

En pratique, la structure devient :
```tsx
export default function LegaSite() {
  // ... tous les useState, useEffect, handlers existants ...

  const isPreview = useMemo(() => { /* ... */ }, []);

  if (isPreview) {
    return (/* Coming Soon view — HeroCarousel + Bientôt disponible */);
  }

  // ── Render normal (inchangé) ──
  return (
    <div dir={dir} style={s({...})}>
      {/* tout le contenu existant : navbar, hero, stats, catalogue, docs, chat, etc. */}
    </div>
  );
}
```

## Tâche 3 : Vérifier le build

**Fichier :** Aucun, juste commande terminal.

**Vérification :**
```bash
cd /opt/bvi/vitrine/frontend
npm run build 2>&1 | tail -10
```
Expected : Build successful.

Si `next build` échoue à cause de `useSearchParams` (nécessite Suspense), remplacer par `useMemo` avec `window.location.search` (comme proposé dans Tâche 1, pas de Suspense wrapper nécessaire).

## Tâche 4 : Vérifier le rendu live

```bash
# Vérifier que la page répond — doit montrer "Bientôt disponible"
curl -s http://localhost:3002 | grep -c "Bientôt Disponible"

# Vérifier que le mode preview fonctionne
curl -s "http://localhost:3002?preview=true" | grep -c "LEGA.PT"
```

## Vérification

- [ ] Accès normal à `http://localhost:3002` → hero image + "Bientôt Disponible", rien d'autre
- [ ] `http://localhost:3002?preview=true` → site complet avec navbar, catalogue, chat Léa, etc.
- [ ] Chat Léa, catalogue, contact, documentation continuent de fonctionner en mode preview
- [ ] Le build Next.js passe

## Restauration (pour plus tard)

Pour remettre le site normal, supprimer simplement :
1. Le bloc `if (isPreview) { return (...); }`
2. La ligne `const isPreview = useMemo(...`
3. L'import `useMemo` (optionnel)

Et voilà, le site redevient normal immédiatement.

## Notes

- Le mode **coming soon** est totalement temporaire et réversible en 30 secondes
- Tous les services backend (API, DB, WebSocket, bus Ollama/DeepSeek) tournent normalement
- Le site vitrine Next.js est en hot-reload (pas besoin de rebuild manuel après modification)
- Le paramètre `?preview=true` est un secret simple — ne pas le communiquer au public
