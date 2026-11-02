import React, { useState } from "react";
import { Lock, User, LogIn, ShieldCheck } from "lucide-react";

export default function Login({ onLogin }) {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError("");

    try {
      const response = await fetch("http://localhost:8000/api/login", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ username, password })
      });

      if (!response.ok) {
        const errorData = await response.json();
        throw new Error(errorData.detail || "Invalid username or password");
      }

      const data = await response.json();
      onLogin(data.user_id);
    } catch (err) {
      setError(err.message || "Invalid username or password");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card glass-panel-purple">
        <div className="login-logo-section">
          <div className="login-avatar-glow">
            <ShieldCheck size={36} className="text-cyan-400" style={{ color: "var(--color-cyan)" }} />
          </div>
          <h2>Aria</h2>
          <p>AI REWARDS CONCIERGE SECURE LOGIN</p>
        </div>

        <form onSubmit={handleSubmit} className="login-form">
          {error && <div className="login-error">{error}</div>}

          <div className="login-input-group">
            <label className="settings-label">Username</label>
            <div className="login-input-wrapper">
              <User size={16} className="login-icon" />
              <input 
                type="text" 
                placeholder="Enter username (e.g., rahul)" 
                value={username}
                onChange={(e) => {
                  setUsername(e.target.value);
                  setError("");
                }}
                className="login-input-text"
                required
              />
            </div>
          </div>

          <div className="login-input-group">
            <label className="settings-label">Password</label>
            <div className="login-input-wrapper">
              <Lock size={16} className="login-icon" />
              <input 
                type="password" 
                placeholder="Enter password (e.g., password123)" 
                value={password}
                onChange={(e) => {
                  setPassword(e.target.value);
                  setError("");
                }}
                className="login-input-text"
                required
              />
            </div>
          </div>

          <div className="login-user-info-hint">
            <span className="hint-label">Try:</span> rahul / password123, priya / password123
          </div>

          <button 
            type="submit" 
            className="login-btn"
            disabled={loading}
          >
            {loading ? (
              <span className="spinner"></span>
            ) : (
              <>
                <LogIn size={16} style={{ marginRight: "8px" }} /> Secure Sign In
              </>
            )}
          </button>
        </form>

        <div className="login-footer">
          Powered by Aria Loyalty Data Systems
        </div>
      </div>
    </div>
  );
}
