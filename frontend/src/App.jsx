import React, { useState, useEffect } from "react";
import UserProfileSidebar from "./components/UserProfileSidebar";
import ChatInterface from "./components/ChatInterface";
import ArchitectureVisualizer from "./components/ArchitectureVisualizer";
import Login from "./components/Login";
import confetti from "canvas-confetti";
import "./App.css";

const API_BASE = "http://localhost:8000";

export default function App() {
  const [activeUser, setActiveUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const [activeNode, setActiveNode] = useState("PRE_LOAD");
  const [logs, setLogs] = useState([]);
  const [hasKeys, setHasKeys] = useState({ has_groq: false, has_anthropic: false });

  // 1. Initial Load and Pre-loading Engine
  useEffect(() => {
    if (!activeUser) return;
    preloadUser(activeUser);
    fetchLogs();
    
    // Poll logs every 2 seconds to keep visualizer console fresh
    const interval = setInterval(fetchLogs, 2000);
    return () => clearInterval(interval);
  }, [activeUser]);

  const handleLogout = () => {
    setActiveUser(null);
    setProfile(null);
    setMessages([]);
  };

  const preloadUser = async (userId) => {
    setActiveNode("PRE_LOAD");
    try {
      // Trigger pre-loading endpoint
      const res = await fetch(`${API_BASE}/api/preload?user_id=${userId}`);
      if (!res.ok) throw new Error("Preload failed");
      const data = await res.json();
      
      // Update profile state
      setProfile(data.user_profile);
      
      // Initialize chat with a proactive personalized greeting from Aria
      const recText = data.preloaded_recommendations && data.preloaded_recommendations.length > 0
        ? `I recommend checking out the **${data.preloaded_recommendations[0].name}** (${data.preloaded_recommendations[0].points_cost} pts).`
        : "Let me search matching vouchers for you.";
        
      setMessages([
        {
          sender: "assistant",
          text: `Hello **${data.user_profile.name}**! I am **Aria**, your AI Rewards Concierge. (Aria Rewards Concierge me aapka swagat hai!)\n\nYour points balance is **${data.user_profile.points_balance.toLocaleString()}** and you are a **${data.user_profile.tier}** member. Note that **${data.user_profile.expiring_points.toLocaleString()} points** are expiring on **${data.user_profile.expiry_date}**! ${recText} What would you like to redeem today?`
        }
      ]);
      
      // Flash node status to show it completed
      setTimeout(() => setActiveNode(null), 1000);
    } catch (err) {
      console.error("Error preloading user:", err);
      // Fallback local load
      fetchProfile(userId);
    }
  };

  const fetchProfile = async (userId) => {
    try {
      const res = await fetch(`${API_BASE}/api/profile?user_id=${userId}`);
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
      }
    } catch (err) {
      console.error("Error fetching profile:", err);
    }
  };

  const fetchLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/logs`);
      if (res.ok) {
        const data = await res.json();
        setLogs(data.reverse()); // Show newest logs first
      }
    } catch (err) {
      console.error("Error fetching execution logs:", err);
    }
  };

  // 2. Chat Processing & Orchestrator Graph State Transition Simulation
  const handleSendMessage = async (text) => {
    // Add user message
    const updatedMessages = [...messages, { sender: "user", text }];
    setMessages(updatedMessages);
    setIsTyping(true);
    
    // Step 1: Active node goes to Router
    setActiveNode("ROUTER");
    
    try {
      const chatHistory = updatedMessages.slice(0, -1); // don't send current message in history list
      
      const response = await fetch(`${API_BASE}/api/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          user_id: activeUser,
          message: text,
          history: chatHistory
        })
      });
      
      if (!response.ok) throw new Error("Chat request failed");
      
      const data = await response.json();
      
      // Step 2: Simulate tool execution node highlight if tools were active
      if (data.tool_calls && data.tool_calls.length > 0) {
        setActiveNode("TOOL_CALL");
        await delay(800);
      }
      
      // Step 3: Reasoner active node highlight
      setActiveNode("REASONER");
      await delay(800);
      
      // Step 4: Guardrail check node highlight
      setActiveNode("GUARDRAIL");
      await delay(500);
      
      // Add assistant response
      setMessages((prev) => [...prev, { sender: "assistant", text: data.bot_response }]);
      
      // Check for redemption success in response to trigger confetti
      if (data.bot_response.includes("Successful") || data.bot_response.includes("Success")) {
        triggerConfetti();
      }
      
      // Reload profile to refresh point balances
      fetchProfile(activeUser);
      fetchLogs();
      
    } catch (err) {
      console.error("Chat error:", err);
      setMessages((prev) => [
        ...prev, 
        { sender: "assistant", text: "Oops, technical error. Backend disconnect ho gaya lagta hai. Please check that uvicorn server is running." }
      ]);
    } finally {
      setIsTyping(false);
      setActiveNode(null);
    }
  };

  const delay = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

  // 3. User & Context Control Actions
  const handleUpdatePoints = async (newVal) => {
    try {
      const res = await fetch(`${API_BASE}/api/profile?user_id=${activeUser}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ points_balance: newVal })
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        fetchLogs();
      }
    } catch (err) {
      console.error("Error updating points:", err);
    }
  };

  const handleUpdateRegion = async (newRegion) => {
    try {
      const res = await fetch(`${API_BASE}/api/profile?user_id=${activeUser}`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ region: newRegion })
      });
      if (res.ok) {
        const data = await res.json();
        setProfile(data);
        fetchLogs();
      }
    } catch (err) {
      console.error("Error updating region:", err);
    }
  };

  const handleRedeemReward = (rewardId) => {
    // Send natural command to the chat to trigger redemption agent flow
    handleSendMessage(`Confirm redeem ${rewardId}`);
  };

  const handleTriggerPrompt = (promptText) => {
    handleSendMessage(promptText);
  };

  const handleClearLogs = async () => {
    try {
      const res = await fetch(`${API_BASE}/api/clear-logs`, { method: "POST" });
      if (res.ok) {
        setLogs([]);
      }
    } catch (err) {
      console.error("Error clearing logs:", err);
    }
  };

  const handleSaveKeys = async (groqKey, anthropicKey) => {
    try {
      const res = await fetch(`${API_BASE}/api/config`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          groq_api_key: groqKey || null,
          anthropic_api_key: anthropicKey || null
        })
      });
      if (res.ok) {
        const data = await res.json();
        setHasKeys({ has_groq: data.has_groq, has_anthropic: data.has_anthropic });
        fetchLogs();
      }
    } catch (err) {
      console.error("Error saving config:", err);
    }
  };

  const triggerConfetti = () => {
    confetti({
      particleCount: 100,
      spread: 70,
      origin: { y: 0.6 },
      colors: ["#66fcf1", "#a855f7", "#10b981"]
    });
  };

  if (!activeUser) {
    return <Login onLogin={setActiveUser} />;
  }

  return (
    <div className="app-container">
      <UserProfileSidebar 
        profile={profile}
        onSelectUser={setActiveUser}
        onUpdatePoints={handleUpdatePoints}
        onUpdateRegion={handleUpdateRegion}
        onTriggerPrompt={handleTriggerPrompt}
        onLogout={handleLogout}
      />
      
      <ChatInterface 
        messages={messages}
        onSendMessage={handleSendMessage}
        isTyping={isTyping}
        onRedeemReward={handleRedeemReward}
        onTriggerPrompt={handleTriggerPrompt}
        profile={profile}
      />
      
      <ArchitectureVisualizer 
        activeNode={activeNode}
        logs={logs}
        onClearLogs={handleClearLogs}
        onSaveKeys={handleSaveKeys}
        hasKeys={hasKeys}
      />
    </div>
  );
}
