import React, { useState, useEffect, useRef } from "react";
import { Send, Bot, Sparkles, CheckCircle, AlertCircle } from "lucide-react";
import ariaLogo from "../assets/aria_logo.png";

export default function ChatInterface({ 
  messages, 
  onSendMessage, 
  isTyping, 
  onRedeemReward,
  onTriggerPrompt,
  profile
}) {
  const [input, setInput] = useState("");
  const messagesEndRef = useRef(null);

  // Auto scroll to bottom when new messages arrive
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages, isTyping]);

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!input.trim()) return;
    onSendMessage(input);
    setInput("");
  };

  const handleQuickPromptClick = (promptText) => {
    onTriggerPrompt(promptText);
  };

  // Pre-formatted quick prompts for Hinglish and Hackathon demo scenarios
  const quickPromptsList = [
    { label: "Check Expiry", text: "Points kab expire ho rahe hain?" },
    { label: "Search Food", text: "Mujhe food wala kuch chahiye" },
    { label: "Pizza Hut Vouchers", text: "Pizza Hut voucher coupon" },
    { label: "Aspirational (Taj)", text: "Taj Hotel voucher redeem karna hai" },
    { label: "Points Earn Path", text: "Points earn karne ke options dikhao" }
  ];

  // Render text that contains bold elements and codes
  const renderMessageText = (text) => {
    if (!text) return "";
    
    // Split by newlines
    const lines = text.split("\n");
    return lines.map((line, index) => {
      // Bold text formatting **text**
      let parts = line.split(/\*\*([^*]+)\*\*/g);
      
      // Inline code blocks `code`
      const formattedParts = parts.map((part, i) => {
        if (i % 2 === 1) { // Bold section
          return <strong key={i} style={{ color: "var(--color-cyan)" }}>{part}</strong>;
        }
        
        // Check for inline backticks
        let subParts = part.split(/`([^`]+)`/g);
        return subParts.map((sub, j) => {
          if (j % 2 === 1) {
            return (
              <code key={j} style={{ 
                fontFamily: "var(--font-mono)", 
                background: "rgba(0,0,0,0.4)", 
                padding: "2px 6px", 
                borderRadius: "4px",
                border: "1px solid rgba(255,255,255,0.05)",
                color: "var(--color-purple)"
              }}>
                {sub}
              </code>
            );
          }
          return sub;
        });
      });

      return (
        <React.Fragment key={index}>
          {formattedParts}
          {index < lines.length - 1 && <br />}
        </React.Fragment>
      );
    });
  };

  // Custom parser to identify if message contains voucher details
  // In a real application, we would send metadata separately. 
  // Here we extract reward info if it's formatted in the text, or generate it contextually.
  const getEmbeddedVouchers = (msgText) => {
    const vouchers = [];
    const availableRewards = profile?.available_rewards;
    
    // If the profile or available_rewards hasn't loaded yet, do not render any cards
    if (!availableRewards) return vouchers;
    
    if (msgText.includes("Pizza Hut Voucher") && availableRewards["reward_1"]) {
      vouchers.push({
        id: "reward_1",
        name: "Pizza Hut Voucher",
        cost: 500,
        category: "Food",
        desc: "Get ₹500 off on any Pizza Hut dine-in or delivery order.",
        reason: "Matches your past Pizza Hut redemptions + Available in Bengaluru"
      });
    }
    if (msgText.includes("Taj Hotels Voucher") && availableRewards["reward_2"]) {
      vouchers.push({
        id: "reward_2",
        name: "Taj Hotels Voucher",
        cost: 12000,
        category: "Travel",
        desc: "₹10,000 Luxury stay or dining voucher valid across Taj Hotels in India.",
        reason: "Elite Gold reward matching your travel preferences"
      });
    }
    if (msgText.includes("Starbucks Card") && availableRewards["reward_3"]) {
      vouchers.push({
        id: "reward_3",
        name: "Starbucks Card",
        cost: 1500,
        category: "Food",
        desc: "Starbucks digital card worth ₹1,000 for beverages and merchandise.",
        reason: "Available in your current mock location: Bengaluru"
      });
    }
    if (msgText.includes("Amazon Gift Card") && availableRewards["reward_4"]) {
      vouchers.push({
        id: "reward_4",
        name: "Amazon Gift Card",
        cost: 2000,
        category: "Shopping",
        desc: "Add ₹1,500 instantly to your Amazon Pay balance.",
        reason: "Universally eligible reward with high customer rating"
      });
    }
    if (msgText.includes("Uber Elite Ride Pass") && availableRewards["reward_5"]) {
      vouchers.push({
        id: "reward_5",
        name: "Uber Elite Ride Pass",
        cost: 3500,
        category: "Travel",
        desc: "Get ₹3,000 worth of premium rides (Uber Premier & Intercity).",
        reason: "Requires Gold Tier. Available in Bengaluru and Mumbai only."
      });
    }
    if (msgText.includes("PVR Cinemas Premium ticket") && availableRewards["reward_6"]) {
      vouchers.push({
        id: "reward_6",
        name: "PVR Cinemas Premium ticket",
        cost: 800,
        category: "Entertainment",
        desc: "₹600 voucher redeemable for cinema tickets and food & beverages at PVR.",
        reason: "Fits your entertainment catalog search filters"
      });
    }
    
    return vouchers;
  };

  return (
    <div className="chat-section glass-panel">
      {/* Header */}
      <div className="chat-header">
        <div className="logo-section">
          <img src={ariaLogo} className="logo-img" alt="Aria Logo" />
          <div className="logo-text">
            <h2>Aria</h2>
            <p>AI REWARDS CONCIERGE</p>
          </div>
        </div>
        <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.8rem", color: "var(--color-emerald)", fontWeight: "600" }}>
          <span style={{ width: "8px", height: "8px", borderRadius: "50%", background: "var(--color-emerald)", display: "inline-block", boxShadow: "0 0 8px var(--color-emerald)" }}></span>
          Active Session
        </div>
      </div>

      {/* Message List */}
      <div className="chat-messages">
        {messages.map((msg, index) => {
          const isUser = msg.sender === "user";
          const embeddedVouchers = !isUser ? getEmbeddedVouchers(msg.text) : [];
          
          return (
            <div key={index} className={`message ${isUser ? "user" : "assistant"}`}>
              {/* Profile icon for assistant */}
              {!isUser && (
                <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px", fontSize: "0.75rem", color: "var(--color-purple)", fontWeight: "600" }}>
                  <Sparkles size={12} /> Aria Assistant
                </div>
              )}
              
              <div className="message-bubble">
                {renderMessageText(msg.text)}
              </div>

              {/* Render voucher cards inline inside chat */}
              {embeddedVouchers.map((v, i) => (
                <div key={i} className="reward-voucher-card">
                  <div className="reward-card-banner">
                    <span className="reward-card-category">{v.category}</span>
                    <span className="reward-card-cost">{v.cost.toLocaleString()} pts</span>
                  </div>
                  <div className="reward-card-body">
                    <h4 className="reward-card-title">{v.name}</h4>
                    <p className="reward-card-desc">{v.desc}</p>
                    {v.reason && (
                      <div className="reward-card-reason">
                        <strong>Reason:</strong> {v.reason}
                      </div>
                    )}
                  </div>
                  <div className="reward-card-footer">
                    <span style={{ fontSize: "0.75rem", color: "var(--text-secondary)" }}>Instant Code Issuance</span>
                    <button 
                      className="reward-card-action-btn"
                      onClick={() => onRedeemReward(v.id)}
                    >
                      Redeem Reward
                    </button>
                  </div>
                </div>
              ))}
            </div>
          );
        })}

        {/* Typing indicator */}
        {isTyping && (
          <div className="message assistant">
            <div style={{ display: "flex", alignItems: "center", gap: "6px", marginBottom: "4px", fontSize: "0.75rem", color: "var(--color-purple)", fontWeight: "600" }}>
              <Bot size={12} /> Aria is thinking...
            </div>
            <div className="message-bubble" style={{ display: "flex", gap: "4px", padding: "12px 16px" }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--color-cyan)", display: "inline-block", animation: "bounce 1.4s infinite ease-in-out" }}></span>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--color-cyan)", display: "inline-block", animation: "bounce 1.4s infinite ease-in-out 0.2s" }}></span>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "var(--color-cyan)", display: "inline-block", animation: "bounce 1.4s infinite ease-in-out 0.4s" }}></span>
            </div>
          </div>
        )}

        <div ref={messagesEndRef} />
      </div>

      {/* Input controls */}
      <div className="chat-input-container">
        {/* Quick prompts scroll list */}
        <div className="quick-prompts">
          {quickPromptsList.map((p, idx) => (
            <div 
              key={idx} 
              className="quick-prompt-tag"
              onClick={() => handleQuickPromptClick(p.text)}
            >
              {p.label}
            </div>
          ))}
        </div>

        {/* Input Text Form */}
        <form onSubmit={handleSubmit} className="input-row">
          <input 
            type="text" 
            className="chat-input"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            placeholder="Aria se pucho... Ask about vouchers, points expiry, or earn paths in Hinglish"
          />
          <button type="submit" className="send-btn">
            <Send size={18} />
          </button>
        </form>
      </div>
    </div>
  );
}
