import React, { useState } from "react";
import { Cpu, Terminal, ShieldAlert, Key, Settings, Check, HelpCircle } from "lucide-react";

export default function ArchitectureVisualizer({
  activeNode,
  logs,
  onClearLogs,
  onSaveKeys,
  hasKeys
}) {
  const [groqKey, setGroqKey] = useState("");
  const [anthropicKey, setAnthropicKey] = useState("");
  const [showSettings, setShowSettings] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);

  const handleSave = (e) => {
    e.preventDefault();
    onSaveKeys(groqKey, anthropicKey);
    setSaveSuccess(true);
    setTimeout(() => setSaveSuccess(false), 3000);
  };

  // Agent State Node definition
  const nodes = [
    { id: "PRE_LOAD", name: "Pre-Loading Engine", desc: "Primes recommendations & user context" },
    { id: "ROUTER", name: "Intent Router (Groq Llama 3.1)", desc: "Sub-second classifier & parameters extraction" },
    { id: "TOOL_CALL", name: "Structured Tool Executor", desc: "Validation of balance, region, tier eligibility" },
    { id: "REASONER", name: "Reasoner (Claude 3.5 Sonnet)", desc: "Context synthesis & Hinglish phrasing engine" },
    { id: "GUARDRAIL", name: "Security & Idempotency Guard", desc: "Blocks duplicates & enforces rate limits" }
  ];

  return (
    <div className="visualizer-section">
      {/* Agent Orchestrator State Flow Graph */}
      <div className="glass-panel viz-panel">
        <h3 className="panel-title">
          <Cpu size={16} className="text-cyan-400" style={{ color: "var(--color-cyan)" }} />
          Orchestrator Visualizer
        </h3>
        <p style={{ fontSize: "0.75rem", color: "var(--text-secondary)", marginBottom: "15px", lineHeight: "1.4" }}>
          LangGraph Agent State flow. Green indicates active processes.
        </p>

        <div className="state-flow-graph">
          {nodes.map((n) => {
            const isActive = activeNode === n.id;
            const isPurpleNode = n.id === "REASONER";
            
            return (
              <div 
                key={n.id} 
                className={`state-node ${isActive ? (isPurpleNode ? "active-purple" : "active") : ""}`}
              >
                <span className="node-indicator"></span>
                <div className="node-info">
                  <span className="node-name" style={{ color: isActive ? (isPurpleNode ? "var(--color-purple)" : "var(--color-cyan)") : "white" }}>
                    {n.name}
                  </span>
                  <span className="node-desc">{n.desc}</span>
                </div>
              </div>
            );
          })}
        </div>
      </div>

      {/* Real-time System Logs Console */}
      <div className="console-logs-widget">
        <div className="console-header">
          <span className="console-title">
            <Terminal size={12} style={{ marginRight: "6px", display: "inline-block", verticalAlign: "middle" }} />
            API & Tool Console Logs
          </span>
          <button className="clear-logs-btn" onClick={onClearLogs}>
            Clear
          </button>
        </div>
        <div className="console-body">
          {logs && logs.length > 0 ? (
            logs.map((log, idx) => {
              const dateStr = new Date(log.timestamp * 1000).toLocaleTimeString();
              const typeClass = log.event_type.toLowerCase().replace(" ", "-");
              
              return (
                <div key={idx} className="log-entry">
                  <span className="log-time">[{dateStr}] latency: {log.latency_ms}ms</span>
                  <div>
                    <span className={`log-type ${typeClass}`}>{log.event_type}: </span>
                    <span style={{ color: "var(--text-secondary)" }}>{log.details}</span>
                  </div>
                </div>
              );
            })
          ) : (
            <p style={{ fontStyle: "italic", color: "#444", margin: "auto", textAlign: "center", fontFamily: "var(--font-mono)" }}>
              Console Idle. Try typing a query.
            </p>
          )}
        </div>
      </div>

      {/* Security keys configuration panel */}
      <div className="glass-panel-purple" style={{ padding: "16px" }}>
        <div 
          onClick={() => setShowSettings(!showSettings)}
          style={{ display: "flex", justifyContent: "space-between", alignItems: "center", cursor: "pointer" }}
        >
          <span style={{ display: "flex", alignItems: "center", gap: "8px", fontSize: "0.85rem", fontWeight: "700", textTransform: "uppercase", color: "var(--color-purple)" }}>
            <Key size={16} /> API settings
          </span>
          <Settings size={16} style={{ color: "var(--color-purple)" }} />
        </div>

        {showSettings && (
          <form onSubmit={handleSave} className="settings-panel" style={{ marginTop: "12px", borderTop: "1px solid rgba(168,85,247,0.1)", paddingTop: "12px" }}>
            <div className="settings-input-group">
              <label className="settings-label">Groq API Key (Llama 3.1 Router)</label>
              <input 
                type="password" 
                className="settings-input"
                placeholder={hasKeys.has_groq ? "••••••••••••••••" : "Paste GROQ_API_KEY"}
                value={groqKey}
                onChange={(e) => setGroqKey(e.target.value)}
              />
            </div>
            
            <div className="settings-input-group" style={{ marginTop: "8px" }}>
              <label className="settings-label">Anthropic API Key (Claude 3.5 Reasoner)</label>
              <input 
                type="password" 
                className="settings-input"
                placeholder={hasKeys.has_anthropic ? "••••••••••••••••" : "Paste ANTHROPIC_API_KEY"}
                value={anthropicKey}
                onChange={(e) => setAnthropicKey(e.target.value)}
              />
            </div>

            <button type="submit" className="settings-save-btn" style={{ marginTop: "10px" }}>
              {saveSuccess ? (
                <span style={{ display: "flex", alignItems: "center", justifyContent: "center", gap: "4px" }}>
                  <Check size={14} /> Saved & Configured!
                </span>
              ) : (
                "Save API Configurations"
              )}
            </button>
          </form>
        )}

        <div style={{ marginTop: "10px", fontSize: "0.7rem", color: "rgba(255,255,255,0.4)", display: "flex", gap: "6px", alignItems: "center" }}>
          <ShieldAlert size={12} style={{ color: hasKeys.has_groq && hasKeys.has_anthropic ? "var(--color-emerald)" : "var(--color-amber)" }} />
          <span>
            {hasKeys.has_groq && hasKeys.has_anthropic 
              ? "Running in Live API Mode (Llama 3.1 + Claude 3.5)" 
              : "Running in High-Fidelity Simulator Mode (No Keys required)"}
          </span>
        </div>
      </div>
    </div>
  );
}
