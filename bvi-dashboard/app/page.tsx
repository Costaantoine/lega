"use client";
import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import MonitoringPage from "./components/MonitoringPage";
import AgentsPage from "./components/AgentsPage";
import TasksPage from "./components/TasksPage";
import ProductsPage from "./components/ProductsPage";
import ActivationsPage from "./components/ActivationsPage";
import SourceManager from "./components/SourceManager";
import SiteVitrinePage from "./components/SiteVitrinePage";

const API = process.env.NEXT_PUBLIC_API_URL || "http://76.13.141.221:8002/api";

const NAV = [
  { id: "monitoring", label: "Monitoring", icon: "📊" },
  { id: "agents", label: "Agents", icon: "🤖" },
  { id: "tasks", label: "Tâches", icon: "📋" },
  { id: "products", label: "Produits", icon: "📦" },
  { id: "activations", label: "Activations", icon: "🎁" },
  { id: "sources", label: "Sources", icon: "🔗" },
  { id: "vitrine", label: "Site Vitrine", icon: "🌐" },
];

export default function AdminDashboard() {
  const router = useRouter();
  const [page, setPage] = useState("monitoring");
  const [health, setHealth] = useState<any>(null);
  const [sidebarOpen, setSidebarOpen] = useState(true);
  const [pendingCount, setPendingCount] = useState(0);
  const [authReady, setAuthReady] = useState(false);
  const [adminUser, setAdminUser] = useState("admin");

  // Vérification token au montage
  useEffect(() => {
    const token = localStorage.getItem("bvi_token");
    if (!token) { router.replace("/login"); return; }
    fetch(`${API}/auth/me`, { headers: { Authorization: `Bearer ${token}` } })
      .then(r => { if (!r.ok) throw new Error(); return r.json(); })
      .then(d => { setAdminUser(d.username); setAuthReady(true); })
      .catch(() => { localStorage.removeItem("bvi_token"); router.replace("/login"); });
  }, [router]);

  const handleLogout = () => {
    localStorage.removeItem("bvi_token");
    router.push("/login");
  };

  useEffect(() => {
    const fetchHealth = async () => {
      try {
        const res = await fetch(`${API}/health`);
        setHealth(await res.json());
      } catch { }
    };
    fetchHealth();
    const iv = setInterval(fetchHealth, 15000);
    return () => clearInterval(iv);
  }, []);

  useEffect(() => {
    const fetchPending = async () => {
      const tok = localStorage.getItem('bvi_token') || '';
      try {
        const res = await fetch(`${API}/activations?status=pending`, { headers: { Authorization: `Bearer ${tok}` } });
        const data = await res.json();
        if (Array.isArray(data)) setPendingCount(data.length);
      } catch { }
    };
    fetchPending();
    const iv = setInterval(fetchPending, 20000);
    return () => clearInterval(iv);
  }, []);

  const navBtnStyle = (id: string): React.CSSProperties => ({
    display: "flex",
    alignItems: "center",
    gap: 10,
    padding: sidebarOpen ? "10px 14px" : "10px 0",
    justifyContent: sidebarOpen ? "flex-start" : "center",
    borderRadius: 8,
    border: "none",
    background: page === id ? "#3b82f620" : "transparent",
    color: page === id ? "#60a5fa" : "#94a3b8",
    cursor: "pointer",
    fontSize: 14,
    fontWeight: page === id ? 600 : 400,
    width: "100%",
    textAlign: "left",
    transition: "background 0.15s",
    borderLeft: page === id ? "3px solid #3b82f6" : "3px solid transparent",
  });

  if (!authReady) {
    return (
      <div style={{ display: "flex", alignItems: "center", justifyContent: "center", height: "100vh", background: "#0f172a", color: "#64748b", fontSize: 14 }}>
        Vérification session...
      </div>
    );
  }

  return (
    <div style={{ display: "flex", height: "100vh", overflow: "hidden" }}>
      {/* Sidebar */}
      <div style={{
        width: sidebarOpen ? 210 : 52, background: "#0a1628", borderRight: "1px solid #1e293b",
        display: "flex", flexDirection: "column", transition: "width 0.2s", flexShrink: 0, overflow: "hidden",
      }}>
        {/* Logo */}
        <div style={{ padding: "16px 14px", borderBottom: "1px solid #1e293b", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          {sidebarOpen && <span style={{ fontWeight: 700, fontSize: 15, color: "#f8fafc" }}>🚜 LEGA Admin</span>}
          <button onClick={() => setSidebarOpen(p => !p)} style={{ background: "none", border: "none", color: "#475569", cursor: "pointer", fontSize: 16, padding: 4 }}>
            {sidebarOpen ? "◀" : "▶"}
          </button>
        </div>

        {/* Nav */}
        <nav style={{ flex: 1, padding: "12px 8px", display: "flex", flexDirection: "column", gap: 4 }}>
          {NAV.map(({ id, label, icon }) => (
            <button key={id} onClick={() => setPage(id)} style={navBtnStyle(id)}>
              <span style={{ fontSize: 17, flexShrink: 0 }}>{icon}</span>
              {sidebarOpen && (
                <span style={{ display: "flex", alignItems: "center", gap: 6 }}>
                  {label}
                  {id === "activations" && pendingCount > 0 && (
                    <span style={{ background: "#f87171", color: "#fff", borderRadius: 10, padding: "1px 7px", fontSize: 11, fontWeight: 700 }}>{pendingCount}</span>
                  )}
                </span>
              )}
            </button>
          ))}
        </nav>

        {/* Health footer */}
        {sidebarOpen && health && (
          <div style={{ padding: "12px 14px", borderTop: "1px solid #1e293b", fontSize: 11, color: "#475569" }}>
            <div style={{ display: "flex", alignItems: "center", gap: 6 }}>
              <span style={{ width: 7, height: 7, borderRadius: "50%", background: health.status === "ok" ? "#4ade80" : "#f87171", display: "inline-block" }} />
              API v{health.version}
            </div>
            <div style={{ marginTop: 4 }}>{health.active_ws} WS actifs</div>
          </div>
        )}
      </div>

      {/* Main content */}
      <div style={{ flex: 1, display: "flex", flexDirection: "column", overflow: "hidden" }}>
        {/* Top bar */}
        <div style={{ padding: "12px 24px", borderBottom: "1px solid #1e293b", background: "#0a1628", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <span style={{ fontWeight: 600, fontSize: 15 }}>
              {NAV.find(n => n.id === page)?.icon} {NAV.find(n => n.id === page)?.label}
            </span>
          </div>
          <div style={{ display: "flex", alignItems: "center", gap: 12, fontSize: 13 }}>
            {pendingCount > 0 && (
              <button onClick={() => setPage("activations")} style={{ padding: "4px 12px", borderRadius: 6, border: "none", background: "#f8717133", color: "#f87171", cursor: "pointer", fontWeight: 600, fontSize: 12 }}>
                🎁 {pendingCount} trial{pendingCount > 1 ? "s" : ""} en attente
              </button>
            )}
            <span style={{ color: "#475569" }}>{adminUser}</span>
            <button onClick={handleLogout} style={{ padding: "4px 12px", borderRadius: 6, border: "1px solid #334155", background: "transparent", color: "#64748b", cursor: "pointer", fontSize: 12 }}>
              Déconnexion
            </button>
          </div>
        </div>

        {/* Page content */}
        <div style={{ flex: 1, overflowY: "auto", padding: "24px" }}>
          {page === "monitoring" && <MonitoringPage />}
          {page === "agents" && <AgentsPage />}
          {page === "tasks" && <TasksPage />}
          {page === "products" && <ProductsPage />}
          {page === "activations" && <ActivationsPage />}
          {page === "sources" && (
            <div>
              <h2 style={{ marginTop: 0, fontSize: 20 }}>🔗 Sources de données</h2>
              <div style={{ background: "#1e293b", borderRadius: 12, padding: 20 }}>
                <SourceManager />
              </div>
            </div>
          )}
          {page === "vitrine" && <SiteVitrinePage />}
        </div>
      </div>
    </div>
  );
}
