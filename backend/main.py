from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Dict, Any, Optional
import os
import config
from database import USER_DB, REWARDS_CATALOG, get_logs, clear_logs, add_log, verify_credentials
from agent import run_groq_intent, run_claude_reasoner, run_preloading_engine
from tools import get_user_profile

app = FastAPI(title="Aria Rewards Concierge Backend API")

# Enable CORS for frontend development server
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # In development, allow all origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Request / Response Schemas

class ChatMessage(BaseModel):
    sender: str  # 'user' or 'assistant'
    text: str

class ChatRequest(BaseModel):
    user_id: str
    message: str
    history: List[ChatMessage]

class ProfileUpdate(BaseModel):
    points_balance: Optional[int] = None
    region: Optional[str] = None
    tier: Optional[str] = None

class ConfigUpdateRequest(BaseModel):
    groq_api_key: Optional[str] = None
    anthropic_api_key: Optional[str] = None

class LoginRequest(BaseModel):
    username: str
    password: str

# Routes

@app.post("/api/login")
async def login_endpoint(req: LoginRequest):
    user_id = verify_credentials(req.username, req.password)
    if not user_id:
        add_log("Authentication", f"Failed login attempt for username: {req.username}", 0)
        raise HTTPException(status_code=401, detail="Invalid username or password")
    
    add_log("Authentication", f"Successful login for {req.username} ({user_id})", 1)
    return {"status": "success", "user_id": user_id}

@app.post("/api/chat")
async def chat_endpoint(req: ChatRequest):
    if req.user_id not in USER_DB:
        raise HTTPException(status_code=404, detail="User not found")
        
    try:
        # Step 1: Run Groq Intent Detection
        intent_res = run_groq_intent(req.message)
        
        # Step 2: Run Claude Reasoner & Tool Execution
        history_list = [{"sender": h.sender, "text": h.text} for h in req.history]
        bot_response, tool_calls, claude_model = run_claude_reasoner(
            req.user_id, intent_res, req.message, history_list
        )
        
        return {
            "bot_response": bot_response,
            "intent": intent_res["intent"],
            "tool_calls": tool_calls,
            "router_model": intent_res["model"],
            "reasoner_model": claude_model
        }
    except Exception as e:
        add_log("API Error", f"Error in chat endpoint: {str(e)}", 0)
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/profile")
async def get_profile(user_id: str):
    if user_id not in USER_DB:
        raise HTTPException(status_code=404, detail="User not found")
    return get_user_profile(user_id)

@app.post("/api/profile")
async def update_profile(user_id: str, profile: ProfileUpdate):
    if user_id not in USER_DB:
        raise HTTPException(status_code=404, detail="User not found")
        
    user = USER_DB[user_id]
    if profile.points_balance is not None:
        user["points_balance"] = profile.points_balance
        add_log("Profile Update", f"User {user_id} points balance updated to {profile.points_balance}", 1)
    if profile.region is not None:
        user["region"] = profile.region
        add_log("Profile Update", f"User {user_id} region updated to {profile.region}", 1)
    if profile.tier is not None:
        user["tier"] = profile.tier
        add_log("Profile Update", f"User {user_id} tier updated to {profile.tier}", 1)
        
    return get_user_profile(user_id)

@app.get("/api/rewards")
async def get_rewards():
    return list(REWARDS_CATALOG.values())

@app.get("/api/preload")
async def preload_endpoint(user_id: str):
    if user_id not in USER_DB:
        raise HTTPException(status_code=404, detail="User not found")
    return run_preloading_engine(user_id)

@app.post("/api/config")
async def update_config(req: ConfigUpdateRequest):
    if req.groq_api_key is not None:
        config.GROQ_API_KEY = req.groq_api_key
        os.environ["GROQ_API_KEY"] = req.groq_api_key
        add_log("Security Update", "Groq API Key updated", 0)
    if req.anthropic_api_key is not None:
        config.ANTHROPIC_API_KEY = req.anthropic_api_key
        os.environ["ANTHROPIC_API_KEY"] = req.anthropic_api_key
        add_log("Security Update", "Anthropic API Key updated", 0)
    return {"status": "success", "has_groq": bool(config.GROQ_API_KEY), "has_anthropic": bool(config.ANTHROPIC_API_KEY)}

@app.get("/api/logs")
async def get_execution_logs():
    return get_logs()

@app.post("/api/clear-logs")
async def clear_execution_logs():
    clear_logs()
    add_log("System", "Logs cleared", 0)
    return {"status": "success"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=config.HOST, port=config.PORT, reload=True)
