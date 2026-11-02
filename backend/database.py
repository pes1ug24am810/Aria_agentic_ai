import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional

# In-Memory Database representing production data systems for Kobie Client Loyalty
LOCAL_USER_DB: Dict[str, Dict[str, Any]] = {
    "user_1": {
        "user_id": "user_1",
        "name": "Rahul Sharma",
        "tier": "Gold",
        "points_balance": 8500,
        "region": "Bengaluru",
        "email": "rahul.sharma@example.in",
        "expiring_points": 3000,
        "expiry_date": "2026-07-01",
        "redemption_history": [
            {"reward_name": "Pizza Hut Voucher", "points": 500, "date": "2026-05-10", "status": "Completed"},
            {"reward_name": "Amazon Gift Card", "points": 2000, "date": "2026-04-18", "status": "Completed"}
        ]
    },
    "user_2": {
        "user_id": "user_2",
        "name": "Priya Patel",
        "tier": "Platinum",
        "points_balance": 15000,
        "region": "Mumbai",
        "email": "priya.patel@example.in",
        "expiring_points": 500,
        "expiry_date": "2026-09-15",
        "redemption_history": [
            {"reward_name": "Taj Hotels Voucher", "points": 12000, "date": "2026-03-02", "status": "Completed"}
        ]
    },
    "user_3": {
        "user_id": "user_3",
        "name": "Aarav Mehta",
        "tier": "Silver",
        "points_balance": 1200,
        "region": "Delhi",
        "email": "aarav.mehta@example.in",
        "expiring_points": 800,
        "expiry_date": "2026-06-25",
        "redemption_history": []
    }
}

LOCAL_REWARDS_CATALOG: Dict[str, Dict[str, Any]] = {
    "reward_1": {
        "reward_id": "reward_1",
        "name": "Pizza Hut Voucher",
        "points_cost": 500,
        "value_inr": 500,
        "category": "Food",
        "availability": "Available",
        "region_restriction": "All",
        "tier_restriction": "All",
        "description": "Get ₹500 off on any Pizza Hut dine-in or delivery order.",
        "terms": "Valid for 6 months from issue date. Cannot be clubbed with other offers."
    },
    "reward_2": {
        "reward_id": "reward_2",
        "name": "Taj Hotels Voucher",
        "points_cost": 12000,
        "value_inr": 10000,
        "category": "Travel",
        "availability": "Available",
        "region_restriction": "All",
        "tier_restriction": "Gold",
        "description": "₹10,000 Luxury stay or dining voucher valid across Taj Hotels in India.",
        "terms": "Requires Gold Tier or above. Advance booking required. Excludes black-out dates."
    },
    "reward_3": {
        "reward_id": "reward_3",
        "name": "Starbucks Card",
        "points_cost": 1500,
        "value_inr": 1000,
        "category": "Food",
        "availability": "Available",
        "region_restriction": "Bengaluru, Mumbai, Delhi",
        "tier_restriction": "All",
        "description": "Starbucks digital card worth ₹1,000 for beverages and merchandise.",
        "terms": "Valid only in select metropolitan stores (Bengaluru, Mumbai, Delhi)."
    },
    "reward_4": {
        "reward_id": "reward_4",
        "name": "Amazon Gift Card",
        "points_cost": 2000,
        "value_inr": 1500,
        "category": "Shopping",
        "availability": "Available",
        "region_restriction": "All",
        "tier_restriction": "All",
        "description": "Add ₹1,500 instantly to your Amazon Pay balance.",
        "terms": "Direct load to Amazon Pay account. Non-transferable."
    },
    "reward_5": {
        "reward_id": "reward_5",
        "name": "Uber Elite Ride Pass",
        "points_cost": 3500,
        "value_inr": 3000,
        "category": "Travel",
        "availability": "Limited",
        "region_restriction": "Bengaluru, Mumbai",
        "tier_restriction": "Gold",
        "description": "Get ₹3,000 worth of premium rides (Uber Premier & Intercity).",
        "terms": "Applicable in Bengaluru and Mumbai only. Valid for Gold and Platinum tiers."
    },
    "reward_6": {
        "reward_id": "reward_6",
        "name": "PVR Cinemas Premium ticket",
        "points_cost": 800,
        "value_inr": 600,
        "category": "Entertainment",
        "availability": "Available",
        "region_restriction": "Delhi, Mumbai",
        "tier_restriction": "All",
        "description": "₹600 voucher redeemable for cinema tickets and food & beverages at PVR.",
        "terms": "Redeemable online via PVR app or at box offices in Delhi NCR and Mumbai."
    }
}

LOCAL_IDEMPOTENCY_LEDGER: Dict[str, Dict[str, Any]] = {}
EXECUTION_LOGS: List[Dict[str, Any]] = []

# Supabase Client Initialization
supabase = None
supabase_enabled = False

from dotenv import load_dotenv
load_dotenv()

SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_KEY = os.getenv("SUPABASE_KEY", "")

if SUPABASE_URL and SUPABASE_KEY:
    try:
        from supabase import create_client
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
        # Quick test query to check if table is reachable
        supabase.table("users").select("user_id").limit(1).execute()
        supabase_enabled = True
        print("[Supabase] Connected successfully.")
    except Exception as e:
        print("[Supabase] Connection failed or tables not ready, using Local Mock Database. Error:", e)

# ----------------- Logs Management -----------------

def add_log(event_type: str, details: str, latency_ms: int = 15):
    t = time.time()
    # In-memory logging
    EXECUTION_LOGS.append({
        "timestamp": t,
        "event_type": event_type,
        "details": details,
        "latency_ms": latency_ms
    })
    
    # Supabase logging
    if supabase_enabled:
        try:
            supabase.table("execution_logs").insert({
                "event_type": event_type,
                "details": details,
                "latency_ms": latency_ms
            }).execute()
        except Exception as e:
            print("[Supabase] Failed to write log:", e)

def get_logs():
    if supabase_enabled:
        try:
            res = supabase.table("execution_logs").select("*").order("timestamp", desc=True).limit(30).execute()
            logs = []
            for r in res.data:
                # Parse ISO timestamp to epoch
                dt_str = r["timestamp"].replace("Z", "+00:00")
                epoch = datetime.fromisoformat(dt_str).timestamp()
                logs.append({
                    "timestamp": epoch,
                    "event_type": r["event_type"],
                    "details": r["details"],
                    "latency_ms": r["latency_ms"]
                })
            return logs
        except Exception as e:
            print("[Supabase] Failed to fetch logs, using local logs. Error:", e)
    return EXECUTION_LOGS[-30:]

def clear_logs():
    global EXECUTION_LOGS
    EXECUTION_LOGS = []
    if supabase_enabled:
        try:
            # Delete all logs (PostgreSQL delete all matching condition)
            supabase.table("execution_logs").delete().neq("id", -1).execute()
        except Exception as e:
            print("[Supabase] Failed to clear logs:", e)

# ----------------- Proxy lists & dictionaries -----------------

class SupabaseRedemptionHistoryList(list):
    def __init__(self, user_id, items):
        super().__init__(items)
        self.user_id = user_id

    def insert(self, index, item):
        super().insert(index, item)
        if supabase_enabled:
            try:
                supabase.table("redemption_history").insert({
                    "user_id": self.user_id,
                    "reward_name": item["reward_name"],
                    "points": item["points"],
                    "date": item["date"],
                    "status": item["status"]
                }).execute()
            except Exception as e:
                print(f"[Supabase] Redemption history insertion failed for user {self.user_id}:", e)

class SupabaseUserProxy(dict):
    def __init__(self, user_id, data):
        super().__init__(data)
        self.user_id = user_id

    def __setitem__(self, key, value):
        super().__setitem__(key, value)
        if supabase_enabled:
            try:
                # Update specific user columns
                if key in ["points_balance", "tier", "region", "name", "email", "expiring_points", "expiry_date"]:
                    supabase.table("users").update({key: value}).eq("user_id", self.user_id).execute()
            except Exception as e:
                print(f"[Supabase] User field update failed for key '{key}':", e)

class SupabaseUserDb(dict):
    def __contains__(self, user_id):
        if supabase_enabled:
            try:
                res = supabase.table("users").select("user_id").eq("user_id", user_id).execute()
                return len(res.data) > 0
            except Exception as e:
                print("[Supabase] User check failed:", e)
        return user_id in LOCAL_USER_DB

    def __getitem__(self, user_id):
        if supabase_enabled:
            try:
                # Fetch user info
                user_res = supabase.table("users").select("*").eq("user_id", user_id).execute()
                if not user_res.data:
                    raise KeyError(user_id)
                user_data = user_res.data[0]
                
                # Fetch redemption history
                hist_res = supabase.table("redemption_history").select("reward_name, points, date, status").eq("user_id", user_id).order("id", desc=True).execute()
                history_list = []
                for h in hist_res.data:
                    history_list.append({
                        "reward_name": h["reward_name"],
                        "points": h["points"],
                        "date": str(h["date"]),
                        "status": h["status"]
                    })
                
                # Setup custom list class to capture real-time inserts
                user_data["redemption_history"] = SupabaseRedemptionHistoryList(user_id, history_list)
                
                # Dynamic initialization of available_rewards for the Supabase user
                import copy
                user_data["available_rewards"] = copy.deepcopy(LOCAL_REWARDS_CATALOG)
                redeemed_names = {h["reward_name"].lower() for h in history_list}
                to_delete = []
                for r_id, r in user_data["available_rewards"].items():
                    if r["name"].lower() in redeemed_names:
                        to_delete.append(r_id)
                for r_id in to_delete:
                    del user_data["available_rewards"][r_id]
                
                return SupabaseUserProxy(user_id, user_data)
            except Exception as e:
                print(f"[Supabase] User fetch failed for '{user_id}', using local fallback. Error:", e)
        
        # Fallback local dict logic
        local_user = LOCAL_USER_DB[user_id]
        return local_user

class SupabaseRewardsCatalog(dict):
    def __contains__(self, reward_id):
        if supabase_enabled:
            try:
                res = supabase.table("rewards_catalog").select("reward_id").eq("reward_id", reward_id).execute()
                return len(res.data) > 0
            except Exception as e:
                print("[Supabase] Reward check failed:", e)
        return reward_id in LOCAL_REWARDS_CATALOG

    def __getitem__(self, reward_id):
        if supabase_enabled:
            try:
                res = supabase.table("rewards_catalog").select("*").eq("reward_id", reward_id).execute()
                if not res.data:
                    raise KeyError(reward_id)
                return res.data[0]
            except Exception as e:
                print(f"[Supabase] Reward fetch failed for '{reward_id}':", e)
        return LOCAL_REWARDS_CATALOG[reward_id]

    def items(self):
        if supabase_enabled:
            try:
                res = supabase.table("rewards_catalog").select("*").execute()
                return {r["reward_id"]: r for r in res.data}.items()
            except Exception as e:
                print("[Supabase] Fetch catalog items failed, using local. Error:", e)
        return LOCAL_REWARDS_CATALOG.items()

    def values(self):
        if supabase_enabled:
            try:
                res = supabase.table("rewards_catalog").select("*").execute()
                return res.data
            except Exception as e:
                print("[Supabase] Fetch catalog values failed, using local. Error:", e)
        return LOCAL_REWARDS_CATALOG.values()

    def get(self, reward_id, default=None):
        if supabase_enabled:
            try:
                res = supabase.table("rewards_catalog").select("*").eq("reward_id", reward_id).execute()
                if res.data:
                    return res.data[0]
                return default
            except Exception as e:
                print(f"[Supabase] Reward get failed for '{reward_id}':", e)
        return LOCAL_REWARDS_CATALOG.get(reward_id, default)

class SupabaseIdempotencyLedger(dict):
    # Idempotency checks are kept in-memory or can be mapped to local dictionary 
    # as they are fast transient transaction locks
    pass

LOCAL_CREDENTIALS: Dict[str, Dict[str, str]] = {
    "rahul": {"user_id": "user_1", "password": "password123"},
    "priya": {"user_id": "user_2", "password": "password123"},
    "aarav": {"user_id": "user_3", "password": "password123"}
}

def verify_credentials(username: str, password: str) -> Optional[str]:
    """
    Verifies username and password. Returns user_id if valid, else None.
    """
    if supabase_enabled and supabase:
        try:
            res = supabase.table("user_credentials").select("user_id, password").eq("username", username).execute()
            if res.data:
                db_password = res.data[0]["password"]
                if db_password == password:
                    return res.data[0]["user_id"]
            return None
        except Exception as e:
            print("[Supabase] Credentials check failed, using local fallback. Error:", e)
            
    # Fallback to local
    for local_username, creds in LOCAL_CREDENTIALS.items():
        if local_username.lower() == username.lower() and creds["password"] == password:
            return creds["user_id"]
    return None

# Expose database connectors
USER_DB = SupabaseUserDb()
REWARDS_CATALOG = SupabaseRewardsCatalog()
IDEMPOTENCY_LEDGER = SupabaseIdempotencyLedger()

# Initialize user-specific catalogs, excluding pre-existing redemptions
import copy
for user_id, user_data in LOCAL_USER_DB.items():
    user_data["available_rewards"] = copy.deepcopy(LOCAL_REWARDS_CATALOG)
    redeemed_names = {h["reward_name"].lower() for h in user_data.get("redemption_history", [])}
    to_delete = []
    for r_id, r in user_data["available_rewards"].items():
        if r["name"].lower() in redeemed_names:
            to_delete.append(r_id)
    for r_id in to_delete:
        del user_data["available_rewards"][r_id]
