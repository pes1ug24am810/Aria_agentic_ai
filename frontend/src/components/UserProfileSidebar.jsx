import React from "react";
import { User, MapPin, Award, Calendar, RefreshCw, PlusCircle, MinusCircle, LogOut } from "lucide-react";

export default function UserProfileSidebar({ 
  profile, 
  onSelectUser, 
  onUpdatePoints, 
  onUpdateRegion,
  onTriggerPrompt,
  onLogout
}) {
  if (!profile) return (
    <div className="sidebar glass-panel" style={{ padding: "20px", justifyContent: "center", alignItems: "center" }}>
      <RefreshCw className="animate-spin text-cyan-400" />
      <p style={{ marginTop: "10px", fontSize: "0.9rem" }}>Loading profile...</p>
    </div>
  );

  return (
    <div className="sidebar">
      {/* User Card */}
      <div className="glass-panel user-card">
        <div className="avatar-container">
          <div className="avatar">
            {profile.name.charAt(0)}
          </div>
          <div className="user-meta">
            <h3>{profile.name}</h3>
            <span className={`tier-badge tier-${profile.tier}`}>
              {profile.tier} Member
            </span>
          </div>
        </div>

        <div className="points-display">
          <span className="points-value">{profile.points_balance.toLocaleString()}</span>
          <span className="points-label">pts available</span>
        </div>

        {/* Adjust points directly (Mock control for test cases) */}
        <div style={{ display: "flex", gap: "10px", marginTop: "5px" }}>
          <button 
            onClick={() => onUpdatePoints(profile.points_balance + 1000)}
            style={{ 
              flex: 1, 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center", 
              gap: "4px",
              padding: "6px",
              background: "rgba(255,255,255,0.05)",
              border: "var(--border-glass)",
              borderRadius: "6px",
              color: "var(--color-cyan)",
              fontSize: "0.8rem",
              cursor: "pointer"
            }}
          >
            <PlusCircle size={14} /> +1,000 pts
          </button>
          <button 
            onClick={() => onUpdatePoints(Math.max(0, profile.points_balance - 1000))}
            style={{ 
              flex: 1, 
              display: "flex", 
              alignItems: "center", 
              justifyContent: "center", 
              gap: "4px",
              padding: "6px",
              background: "rgba(255,255,255,0.05)",
              border: "var(--border-glass)",
              borderRadius: "6px",
              color: "var(--color-rose)",
              fontSize: "0.8rem",
              cursor: "pointer"
            }}
          >
            <MinusCircle size={14} /> -1,000 pts
          </button>
        </div>

        {/* Logout button */}
        <button 
          onClick={onLogout}
          style={{
            marginTop: "8px",
            width: "100%",
            display: "flex",
            alignItems: "center",
            justifyContent: "center",
            gap: "8px",
            padding: "8px",
            background: "rgba(244, 63, 94, 0.08)",
            border: "1px solid rgba(244, 63, 94, 0.2)",
            borderRadius: "8px",
            color: "var(--color-rose)",
            fontSize: "0.85rem",
            fontWeight: "600",
            cursor: "pointer",
            transition: "all 0.2s"
          }}
          className="logout-btn"
        >
          <LogOut size={14} /> Logout
        </button>
      </div>

      {/* Expiry Alert Widget */}
      {profile.expiring_points > 0 && (
        <div className="expiry-widget">
          <div className="expiry-header">
            <Calendar size={16} />
            <span>Points Expiry Urgency Alert</span>
          </div>
          <p className="expiry-text">
            <strong>{profile.expiring_points.toLocaleString()} points</strong> are expiring on <strong>{profile.expiry_date}</strong>. Use them before they lapse!
          </p>
          <button 
            className="expiry-action-btn"
            onClick={() => onTriggerPrompt("Suggest how to redeem my expiring points")}
          >
            Redeem Expiring Points
          </button>
        </div>
      )}

      {/* Simulation Controls */}
      <div className="glass-panel" style={{ padding: "20px" }}>
        <h4 style={{ fontSize: "0.9rem", fontWeight: "700", marginBottom: "12px", color: "var(--color-cyan)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          Context & Simulator
        </h4>
        
        {/* User Selector */}
        <div style={{ marginBottom: "15px" }}>
          <label className="settings-label" style={{ display: "block", marginBottom: "6px" }}>Select Mock User Profile</label>
          <select 
            value={profile.user_id} 
            onChange={(e) => onSelectUser(e.target.value)}
            style={{ 
              width: "100%", 
              background: "var(--bg-primary)", 
              border: "var(--border-glass)", 
              padding: "8px", 
              borderRadius: "6px", 
              color: "white" 
            }}
          >
            <option value="user_1">Rahul Sharma (Gold - 8.5k pts - BLR)</option>
            <option value="user_2">Priya Patel (Platinum - 15k pts - BOM)</option>
            <option value="user_3">Aarav Mehta (Silver - 1.2k pts - DEL)</option>
          </select>
        </div>

        {/* Region Selector */}
        <div>
          <label className="settings-label" style={{ display: "block", marginBottom: "6px" }}>Mock Region / Geography</label>
          <div style={{ display: "flex", alignItems: "center", gap: "8px", background: "rgba(0,0,0,0.2)", border: "var(--border-glass)", borderRadius: "6px", padding: "4px 8px" }}>
            <MapPin size={16} className="text-teal-400" style={{ color: "var(--color-teal)" }} />
            <select 
              value={profile.region} 
              onChange={(e) => onUpdateRegion(e.target.value)}
              style={{ 
                flex: 1,
                background: "transparent", 
                border: "none", 
                padding: "4px 0", 
                color: "white",
                outline: "none"
              }}
            >
              <option value="Bengaluru">Bengaluru (BLR)</option>
              <option value="Mumbai">Mumbai (BOM)</option>
              <option value="Delhi">Delhi (DEL)</option>
              <option value="Chennai">Chennai (MAA)</option>
              <option value="Pune">Pune (PNQ)</option>
            </select>
          </div>
        </div>
      </div>

      {/* History Log */}
      <div className="glass-panel" style={{ padding: "20px", flex: 1, display: "flex", flexDirection: "column", minHeight: "150px" }}>
        <h4 style={{ fontSize: "0.85rem", fontWeight: "700", marginBottom: "12px", color: "var(--text-secondary)", textTransform: "uppercase", letterSpacing: "0.5px" }}>
          Redemption History
        </h4>
        <div style={{ flex: 1, overflowY: "auto", display: "flex", flexDirection: "column", gap: "10px" }}>
          {profile.redemption_history && profile.redemption_history.length > 0 ? (
            profile.redemption_history.map((item, idx) => (
              <div 
                key={idx} 
                style={{ 
                  padding: "8px 10px", 
                  background: "rgba(255,255,255,0.02)", 
                  borderLeft: "2.5px solid var(--color-teal)", 
                  borderRadius: "0 6px 6px 0",
                  fontSize: "0.8rem"
                }}
              >
                <div style={{ display: "flex", justifyContent: "space-between", fontWeight: "600" }}>
                  <span>{item.reward_name}</span>
                  <span style={{ color: "var(--color-cyan)" }}>-{item.points} pts</span>
                </div>
                <div style={{ display: "flex", justifyContent: "space-between", color: "#555", fontSize: "0.7rem", marginTop: "3px" }}>
                  <span>{item.date}</span>
                  <span style={{ color: "var(--color-emerald)" }}>{item.status}</span>
                </div>
              </div>
            ))
          ) : (
            <p style={{ fontSize: "0.8rem", color: "#555", textAlign: "center", margin: "auto" }}>No recent redemptions</p>
          )}
        </div>
      </div>
    </div>
  );
}
