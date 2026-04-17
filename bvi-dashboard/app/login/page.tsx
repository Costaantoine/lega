"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";

const API = process.env.NEXT_PUBLIC_API_URL || "http://76.13.141.221:8002/api";

export default function LoginPage() {
  const router = useRouter();
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    setLoading(true);
    setError("");
    try {
      const res = await fetch(`${API}/auth/login`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password }),
      });
      if (!res.ok) {
        const data = await res.json();
        setError(data.detail || "Identifiants incorrects");
        return;
      }
      const data = await res.json();
      localStorage.setItem("bvi_token", data.access_token);
      router.push("/");
    } catch {
      setError("Impossible de contacter l'API");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      minHeight: "100vh",
      display: "flex",
      alignItems: "center",
      justifyContent: "center",
      background: "#0f172a",
    }}>
      <div style={{
        background: "#1e293b",
        border: "1px solid #334155",
        borderRadius: 16,
        padding: "40px 48px",
        width: 360,
        boxShadow: "0 25px 50px rgba(0,0,0,0.5)",
      }}>
        <div style={{ textAlign: "center", marginBottom: 32 }}>
          <div style={{ fontSize: 40, marginBottom: 8 }}>🏗️</div>
          <h1 style={{ margin: 0, fontSize: 22, fontWeight: 700, color: "#f1f5f9" }}>
            LEGA Admin
          </h1>
          <p style={{ margin: "6px 0 0", fontSize: 13, color: "#64748b" }}>
            Accès dashboard superviseur
          </p>
        </div>

        <form onSubmit={handleLogin}>
          <div style={{ marginBottom: 16 }}>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Identifiant
            </label>
            <input
              type="text"
              value={username}
              onChange={e => setUsername(e.target.value)}
              autoComplete="username"
              required
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "10px 12px",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 8,
                color: "#f1f5f9",
                fontSize: 14,
                outline: "none",
              }}
            />
          </div>

          <div style={{ marginBottom: 24 }}>
            <label style={{ display: "block", fontSize: 12, color: "#94a3b8", marginBottom: 6, fontWeight: 600, textTransform: "uppercase", letterSpacing: "0.05em" }}>
              Mot de passe
            </label>
            <input
              type="password"
              value={password}
              onChange={e => setPassword(e.target.value)}
              autoComplete="current-password"
              required
              style={{
                width: "100%",
                boxSizing: "border-box",
                padding: "10px 12px",
                background: "#0f172a",
                border: "1px solid #334155",
                borderRadius: 8,
                color: "#f1f5f9",
                fontSize: 14,
                outline: "none",
              }}
            />
          </div>

          {error && (
            <div style={{
              background: "#450a0a",
              border: "1px solid #7f1d1d",
              borderRadius: 8,
              padding: "10px 12px",
              marginBottom: 16,
              fontSize: 13,
              color: "#fca5a5",
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: "100%",
              padding: "12px",
              background: loading ? "#334155" : "#3b82f6",
              border: "none",
              borderRadius: 8,
              color: "#fff",
              fontSize: 15,
              fontWeight: 600,
              cursor: loading ? "not-allowed" : "pointer",
              transition: "background 0.2s",
            }}
          >
            {loading ? "Connexion..." : "Se connecter"}
          </button>
        </form>
      </div>
    </div>
  );
}
