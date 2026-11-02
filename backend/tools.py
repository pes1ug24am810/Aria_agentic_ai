import time
import random
from typing import Dict, Any, List, Optional
from database import USER_DB, REWARDS_CATALOG, IDEMPOTENCY_LEDGER, add_log

# Tool 1: GetUserProfile
def get_user_profile(user_id: str) -> Dict[str, Any]:
    """
    Fetches the profile details of the user including name, tier, points balance, region, and points nearing expiry.
    """
    start_time = time.time()
    if user_id not in USER_DB:
        add_log("Tool Call", f"GetUserProfile failed - User {user_id} not found", int((time.time() - start_time) * 1000))
        return {"error": f"User ID '{user_id}' not found."}
    
    profile = USER_DB[user_id]
    add_log("Tool Call", f"GetUserProfile executed for {profile['name']} (Balance: {profile['points_balance']} pts)", int((time.time() - start_time) * 1000))
    return {
        "user_id": profile["user_id"],
        "name": profile["name"],
        "tier": profile["tier"],
        "points_balance": profile["points_balance"],
        "region": profile["region"],
        "email": profile["email"],
        "expiring_points": profile["expiring_points"],
        "expiry_date": profile["expiry_date"],
        "redemption_history": profile["redemption_history"],
        "available_rewards": profile.get("available_rewards", {})
    }

# Tool 2: SearchRewards
def search_rewards(query: Optional[str] = None, category: Optional[str] = None, max_points: Optional[int] = None, user_id: Optional[str] = None) -> List[Dict[str, Any]]:
    """
    Searches the rewards catalog by keyword query, category type, and maximum points cost.
    """
    start_time = time.time()
    results = []
    
    if query:
        cleaned_q = query.lower().strip()
        # Remove common punctuation
        import re
        cleaned_q = re.sub(r'[^\w\s]', '', cleaned_q)
        generic_queries = {
            "available rewards", "available reward", "rewards available", "reward available",
            "all rewards", "all reward", "show rewards", "show reward", "list rewards", "list reward",
            "available vouchers", "available voucher", "vouchers available", "voucher available",
            "all vouchers", "all voucher", "show vouchers", "show voucher", "list vouchers", "list voucher",
            "available coupons", "available coupon", "coupons available", "coupon available",
            "all coupons", "all coupon", "show coupons", "show coupon", "list coupons", "list coupon",
            "rewards", "reward", "vouchers", "voucher", "coupons", "coupon", "available", "all", "list", "show",
            "available rewards list", "list of available rewards", "list of rewards", "show available rewards"
        }
        if cleaned_q in generic_queries:
            query = None
    
    # Get user's specific catalog if user_id is provided, otherwise fall back to global
    catalog = REWARDS_CATALOG
    if user_id and user_id in USER_DB:
        catalog = USER_DB[user_id].get("available_rewards", REWARDS_CATALOG)
        
    # Validate category to prevent filtering out all rewards when router passes invalid ones
    valid_categories = {"food", "travel", "shopping", "entertainment"}
    if category and category.lower() not in valid_categories:
        category = None
        
    for r_id, reward in catalog.items():
        # Filter by category
        if category and reward["category"].lower() != category.lower():
            continue
            
        # Filter by points cost
        if max_points is not None and reward["points_cost"] > max_points:
            continue
            
        # Filter by keyword query
        if query:
            # Clean punctuation from query
            import re
            cleaned_query = re.sub(r'[^\w\s]', '', query.lower())
            generic_stop_words = {
                "voucher", "vouchers", "coupon", "coupons", "reward", "rewards", 
                "available", "show", "find", "search", "list", "get", "give", 
                "me", "the", "a", "an", "of", "for", "to", "in", "on", "at", "with",
                "mereko", "mujhe", "chahie", "chahiye", "milo", "milega", "dilao", "hai", 
                "ho", "se", "ko", "ka", "ki", "ke", "bhi", "ek", "do",
                "chayiye", "chaye", "vala", "wali", "vale", "manga", "mangaya", "dikhao", "de", "mil", "mujako"
            }
            q_words = [w for w in cleaned_query.split() if w not in generic_stop_words]
            if q_words:
                match = True
                for word in q_words:
                    if not (word in reward["name"].lower() or 
                            word in reward["description"].lower() or 
                            word in reward["category"].lower()):
                        match = False
                        break
                if not match:
                    continue
                
        results.append(reward)
        
    add_log("Tool Call", f"SearchRewards executed (Query: '{query}', Cat: '{category}', Max Pts: {max_points}) -> Found {len(results)} rewards", int((time.time() - start_time) * 1000))
    return results

# Tool 3: CheckEligibility
def check_eligibility(user_id: str, reward_id: str) -> Dict[str, Any]:
    """
    Checks if a user is eligible to redeem a specific reward based on points balance, tier, and regional constraints.
    """
    start_time = time.time()
    if user_id not in USER_DB:
        return {"eligible": False, "reason": "User not found", "points_shortfall": 0}
        
    user = USER_DB[user_id]
    
    # Check if reward exists in user's specific available rewards catalog
    available_rewards = user.get("available_rewards", REWARDS_CATALOG)
    if reward_id not in available_rewards:
        # If the reward is in global catalog but not in user's catalog, it has been redeemed
        if reward_id in REWARDS_CATALOG:
            reason_str = "Already redeemed (limit: 1 per user)"
        else:
            reason_str = "Reward not found"
            
        add_log("Tool Call", f"CheckEligibility (User: {user['name']}, Reward ID: {reward_id}) -> Eligible: False ({reason_str})", int((time.time() - start_time) * 1000))
        return {
            "eligible": False,
            "reason": reason_str,
            "points_shortfall": 0,
            "tier_eligible": True,
            "region_eligible": True,
            "reward_cost": 0,
            "user_balance": user["points_balance"]
        }
        
    reward = available_rewards[reward_id]
    
    # 1. Check points balance
    points_shortfall = max(0, reward["points_cost"] - user["points_balance"])
    
    # 2. Check tier restriction
    tier_eligible = True
    if reward["tier_restriction"] != "All":
        user_tier_rank = {"Silver": 1, "Gold": 2, "Platinum": 3}.get(user["tier"], 0)
        req_tier_rank = {"Silver": 1, "Gold": 2, "Platinum": 3}.get(reward["tier_restriction"], 0)
        if user_tier_rank < req_tier_rank:
            tier_eligible = False
            
    # 3. Check regional restriction
    region_eligible = True
    if reward["region_restriction"] != "All":
        allowed_regions = [r.strip().lower() for r in reward["region_restriction"].split(",")]
        if user["region"].lower() not in allowed_regions:
            region_eligible = False
            
    # Compile eligibility decision
    eligible = (points_shortfall == 0) and tier_eligible and region_eligible
    
    reasons = []
    if points_shortfall > 0:
        reasons.append(f"Insufficient points (shortfall of {points_shortfall} points)")
    if not tier_eligible:
        reasons.append(f"Requires {reward['tier_restriction']} tier, but user is in {user['tier']} tier")
    if not region_eligible:
        reasons.append(f"Restricted to {reward['region_restriction']}, but user region is {user['region']}")
        
    reason_str = ", ".join(reasons) if not eligible else "Eligible for redemption"
    
    add_log("Tool Call", f"CheckEligibility (User: {user['name']}, Reward: {reward['name']}) -> Eligible: {eligible} ({reason_str})", int((time.time() - start_time) * 1000))
    
    return {
        "eligible": eligible,
        "reason": reason_str,
        "points_shortfall": points_shortfall,
        "tier_eligible": tier_eligible,
        "region_eligible": region_eligible,
        "reward_cost": reward["points_cost"],
        "user_balance": user["points_balance"]
    }

# Tool 4: GenerateEarnPath
def generate_earn_path(user_id: str, reward_id: str) -> Dict[str, Any]:
    """
    Computes points shortfall for a reward and generates a personalized earn path with partner spend targets and referrals.
    """
    start_time = time.time()
    eligibility = check_eligibility(user_id, reward_id)
    shortfall = eligibility["points_shortfall"]
    
    if shortfall == 0:
        add_log("Tool Call", f"GenerateEarnPath called for {reward_id} but user is already eligible", int((time.time() - start_time) * 1000))
        return {
            "has_shortfall": False,
            "message": "You already have enough points to redeem this reward!",
            "shortfall": 0,
            "earn_options": []
        }
        
    user = USER_DB[user_id]
    reward = REWARDS_CATALOG[reward_id]
    
    # Generate action paths
    earn_options = [
        {
            "id": "partner_spend",
            "title": "Partner Restaurants & Dining",
            "description": f"Spend ₹{shortfall * 2:,} at partner restaurants to earn {shortfall} points.",
            "points_contribution": shortfall,
            "action_text": "View Partner Locations"
        },
        {
            "id": "refer_friend",
            "title": "Refer a Friend",
            "description": f"Refer {max(1, int(shortfall / 1000))} friend(s) to Aria rewards. Get 1,000 points per referral.",
            "points_contribution": max(1, int(shortfall / 1000)) * 1000,
            "action_text": "Share Referral Code"
        },
        {
            "id": "co_branded_card",
            "title": "Aria Elite Credit Card Signup",
            "description": "Apply for the Aria co-branded card. Get 5,000 bonus points instantly upon card approval.",
            "points_contribution": 5000,
            "action_text": "Apply Now (Instant Approval)"
        },
        {
            "id": "buy_points",
            "title": "Direct Points Purchase",
            "description": f"Purchase {shortfall} points directly for ₹{int(shortfall * 0.5)} (at ₹0.50/point).",
            "points_contribution": shortfall,
            "action_text": f"Buy Points for ₹{int(shortfall * 0.5)}"
        }
    ]
    
    add_log("Tool Call", f"GenerateEarnPath (Shortfall: {shortfall} pts for {reward['name']}) -> Generated {len(earn_options)} options", int((time.time() - start_time) * 1000))
    return {
        "has_shortfall": True,
        "shortfall": shortfall,
        "reward_name": reward["name"],
        "reward_points": reward["points_cost"],
        "user_balance": user["points_balance"],
        "earn_options": earn_options
    }

# Tool 5: RedeemReward
RATE_LIMIT_STORE: Dict[str, float] = {}

def redeem_reward(user_id: str, reward_id: str, idempotency_key: str) -> Dict[str, Any]:
    """
    Redeems a reward for a user. Features rate limiting, regional check, and idempotency key verification to block double transactions.
    """
    start_time = time.time()
    
    # 1. Rate Limiting Check (per user, max 1 request per 3 seconds)
    current_time = time.time()
    last_req_time = RATE_LIMIT_STORE.get(user_id, 0.0)
    if current_time - last_req_time < 3.0:
        add_log("Security Guard", f"RedeemReward blocked - Rate limit triggered for User {user_id}", int((time.time() - start_time) * 1000))
        return {
            "success": False,
            "error_type": "RATE_LIMITED",
            "message": "Transaction request rate limit exceeded. Please wait a moment and try again."
        }
    RATE_LIMIT_STORE[user_id] = current_time
    
    # 2. Idempotency Check
    if idempotency_key in IDEMPOTENCY_LEDGER:
        existing_txn = IDEMPOTENCY_LEDGER[idempotency_key]
        add_log("Security Guard", f"RedeemReward duplicate blocked - Key '{idempotency_key}' already processed", int((time.time() - start_time) * 1000))
        return {
            "success": True,
            "idempotent": True,
            "message": "Duplicate request detected and resolved. Returning original voucher.",
            "voucher_code": existing_txn["voucher_code"],
            "reward_name": existing_txn["reward_name"],
            "points_deducted": existing_txn["points_deducted"]
        }
        
    # 3. Base Checks
    if user_id not in USER_DB:
        return {"success": False, "error_type": "USER_NOT_FOUND", "message": "User not found."}
    if reward_id not in REWARDS_CATALOG:
        return {"success": False, "error_type": "REWARD_NOT_FOUND", "message": "Reward not found."}
        
    user = USER_DB[user_id]
    reward = REWARDS_CATALOG[reward_id]
    
    # 4. Check eligibility
    eligibility = check_eligibility(user_id, reward_id)
    if not eligibility["eligible"]:
        add_log("Validation Guard", f"RedeemReward blocked - User ineligible: {eligibility['reason']}", int((time.time() - start_time) * 1000))
        return {
            "success": False,
            "error_type": "INELIGIBLE",
            "message": f"Cannot redeem reward. Reason: {eligibility['reason']}",
            "details": eligibility
        }
        
    # 5. Perform Transaction
    points_deducted = reward["points_cost"]
    user["points_balance"] -= points_deducted
    
    # Generate unique voucher code
    voucher_code = f"ARIA-{reward_id.upper().replace('_', '')}-{random.randint(1000, 9999)}-{random.randint(1000, 9999)}"
    
    # Log in user history
    user["redemption_history"].insert(0, {
        "reward_name": reward["name"],
        "points": points_deducted,
        "date": time.strftime("%Y-%m-%d"),
        "status": "Completed"
    })
    
    # Delete from user's specific available rewards catalog directly
    if "available_rewards" in user and reward_id in user["available_rewards"]:
        del user["available_rewards"][reward_id]
    
    # Log in Idempotency Ledger
    IDEMPOTENCY_LEDGER[idempotency_key] = {
        "user_id": user_id,
        "reward_id": reward_id,
        "reward_name": reward["name"],
        "points_deducted": points_deducted,
        "voucher_code": voucher_code,
        "timestamp": current_time
    }
    
    add_log("Transaction", f"SUCCESS - Redeemed {reward['name']} for {user['name']} (-{points_deducted} pts). Code: {voucher_code}", int((time.time() - start_time) * 1000))
    
    return {
        "success": True,
        "idempotent": False,
        "voucher_code": voucher_code,
        "reward_name": reward["name"],
        "points_deducted": points_deducted,
        "new_balance": user["points_balance"],
        "message": f"Successfully redeemed! Your new balance is {user['points_balance']} points."
    }
