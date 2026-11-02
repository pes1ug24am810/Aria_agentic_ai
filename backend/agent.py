import re
import json
import uuid
import time
from typing import Dict, Any, List, Tuple
import config
from database import USER_DB, REWARDS_CATALOG, add_log
from tools import (
    get_user_profile,
    search_rewards,
    check_eligibility,
    generate_earn_path,
    redeem_reward
)

# Hybrid Agent Runner: Live API (Anthropic/Groq) + High-Fidelity Local Simulator

def run_groq_intent(user_input: str) -> Dict[str, Any]:
    """
    Simulates or calls Groq (Llama 3.1) for fast intent detection.
    """
    start_time = time.time()
    user_input_lower = user_input.lower()
    
    # Defaults
    intent = "chat"
    parameters = {}
    
    # 1. Real API Call
    if config.GROQ_API_KEY:
        try:
            from groq import Groq
            client = Groq(api_key=config.GROQ_API_KEY)
            system_prompt = (
                "You are an intent router for a rewards concierge. "
                "Classify the user intent into one of: 'greet', 'profile', 'search', 'redeem', 'earn', 'expiry', 'chat'. "
                "Output JSON with keys 'intent' and 'parameters' (e.g. for search: 'query' or 'category', for redeem: 'reward_id'). "
                "Keep parameters simple. Do not explain."
            )
            chat_completion = client.chat.completions.create(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                model="llama-3.1-8b-instant",
                response_format={"type": "json_object"}
            )
            res = json.loads(chat_completion.choices[0].message.content)
            intent = res.get("intent", "chat")
            parameters = res.get("parameters", {})
            add_log("Intent Router (Groq)", f"Detected intent: '{intent}' via Groq API", int((time.time() - start_time) * 1000))
            return {"intent": intent, "parameters": parameters, "model": "Groq Llama 3.1"}
        except Exception as e:
            add_log("Intent Router (Groq)", f"Groq API Error: {str(e)}. Falling back to local parser.", 5)
            
    # 2. Local High-Fidelity Regex Intent Parser
    # Profile requests
    if any(k in user_input_lower for k in ["profile", "balance", "point", "my points", "account", "paisa", "points balance"]):
        intent = "profile"
    # Expiry queries
    elif any(k in user_input_lower for k in ["expire", "expiry", "kab khatam", "date", "bacha", "expiration"]):
        intent = "expiry"
    # Redemption requests
    elif any(k in user_input_lower for k in ["redeem", "buy", "purchase", "check out", "confirm redeem", "lelo", "lena hai", "vouchers"]):
        intent = "redeem"
        # Extract reward ID or name
        for r_id, r in REWARDS_CATALOG.items():
            if r_id in user_input_lower or r["name"].lower() in user_input_lower:
                parameters["reward_id"] = r_id
                break
        # Also handle code-mixed hinglish numbers/vouchers
        if "pizza" in user_input_lower:
            parameters["reward_id"] = "reward_1"
        elif "taj" in user_input_lower:
            parameters["reward_id"] = "reward_2"
        elif "starbucks" in user_input_lower or "coffee" in user_input_lower:
            parameters["reward_id"] = "reward_3"
        elif "amazon" in user_input_lower:
            parameters["reward_id"] = "reward_4"
        elif "uber" in user_input_lower:
            parameters["reward_id"] = "reward_5"
        elif "pvr" in user_input_lower or "cinema" in user_input_lower or "movie" in user_input_lower:
            parameters["reward_id"] = "reward_6"
    # Earn requests
    elif any(k in user_input_lower for k in ["earn", "how to get", "kamaye", "kaise", "earn path", "shortfall", "more points"]):
        intent = "earn"
    # Search requests
    elif any(k in user_input_lower for k in [
        "search", "find", "show", "list", "dikhna", "chahiye", "coupon", "voucher", 
        "kuch", "wala", "reward", "available", "catalog", "option", "options", 
        "travel", "hotel", "hotels", "ride", "rides", "uber", "taj", "food", "pizza", 
        "starbucks", "shopping", "amazon", "entertainment", "movie", "movies", "pvr", 
        "cinema", "cinemas"
    ]):
        intent = "search"
        if any(c in user_input_lower for c in ["food", "khaana", "pizza", "starbucks", "restaurant"]):
            parameters["category"] = "Food"
        elif any(c in user_input_lower for c in ["travel", "hotel", "ride", "uber", "taj"]):
            parameters["category"] = "Travel"
        elif any(c in user_input_lower for c in ["shopping", "amazon", "gift"]):
            parameters["category"] = "Shopping"
        elif any(c in user_input_lower for c in ["entertainment", "movie", "pvr"]):
            parameters["category"] = "Entertainment"
        
        # Look for general search keyword
        stop_words = [
            "what", "are", "the", "rewards", "available", "is", "have", "you", "get", "can", "i", "to", 
            "list", "show", "me", "search", "for", "a", "of", "vouchers", "coupons", "avail", "options", 
            "dikhna", "chahiye", "wala", "kuch", "give", "gives", "want", "need", "needs", "please", 
            "reward", "voucher", "coupon", "all", "any", "option", "catalog", "find", "category", 
            "categories", "details", "detail", "associated", "with", "and", "ask", "asked", "asking", 
            "about", "tell", "told", "say", "said", "suggest", "recommend", "request",
            "mereko", "mujhe", "chahie", "milo", "milega", "dilao", "hai", "ho", "se", "ko", "ka", "ki", "ke", "bhi", "ek", "do",
            "chayiye", "chaye", "vala", "wali", "vale", "manga", "mangaya", "dikhao", "de", "mil", "mujako"
        ]
        # Remove punctuation to ensure robust word matching
        cleaned_input = re.sub(r'[^\w\s]', '', user_input_lower).strip()
        
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
        
        if cleaned_input in generic_queries:
            query_words = []
        else:
            query_words = [w for w in cleaned_input.split() if w not in stop_words]
            
        if query_words:
            parameters["query"] = " ".join(query_words)
            
    add_log("Intent Router (Groq)", f"Detected intent: '{intent}' via Local Parser", int((time.time() - start_time) * 1000))
    return {"intent": intent, "parameters": parameters, "model": "Local Parser (Groq Simulation)"}


def run_claude_reasoner(user_id: str, intent_res: Dict[str, Any], user_input: str, history: List[Dict[str, str]]) -> Tuple[str, List[Dict[str, Any]], str]:
    """
    Simulates or calls Claude 3.5 Sonnet for complex reasoning, tool execution, and Hinglish response construction.
    Returns: (bot_response, tool_calls_made, model_used)
    """
    start_time = time.time()
    intent = intent_res["intent"]
    
    # Map search synonyms and general query intents to "search"
    if intent in ["list_rewards", "available_rewards", "show_rewards", "rewards", "vouchers", "coupons", "avail"]:
        intent = "search"
        
    params = intent_res["parameters"]
    tool_calls_made = []
    
    # 1. Real API Call (Anthropic)
    if config.ANTHROPIC_API_KEY:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=config.ANTHROPIC_API_KEY)
            
            # Setup tools schema for Claude
            claude_tools = [
                {
                    "name": "get_user_profile",
                    "description": "Fetches profile info of user (balance, region, tier, etc.)",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"}
                        },
                        "required": ["user_id"]
                    }
                },
                {
                    "name": "search_rewards",
                    "description": "Searches rewards catalog matching filters",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "query": {"type": "string"},
                            "category": {"type": "string"},
                            "max_points": {"type": "integer"}
                        }
                    }
                },
                {
                    "name": "check_eligibility",
                    "description": "Checks user eligibility for a reward",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "reward_id": {"type": "string"}
                        },
                        "required": ["user_id", "reward_id"]
                    }
                },
                {
                    "name": "generate_earn_path",
                    "description": "Generates points earn path if balance is short",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "reward_id": {"type": "string"}
                        },
                        "required": ["user_id", "reward_id"]
                    }
                },
                {
                    "name": "redeem_reward",
                    "description": "Executes redemption of a reward voucher",
                    "input_schema": {
                        "type": "object",
                        "properties": {
                            "user_id": {"type": "string"},
                            "reward_id": {"type": "string"},
                            "idempotency_key": {"type": "string"}
                        },
                        "required": ["user_id", "reward_id", "idempotency_key"]
                    }
                }
            ]
            
            # Construct message threads
            messages = []
            for h in history:
                messages.append({"role": h["sender"], "content": h["text"]})
            messages.append({"role": "user", "content": user_input})
            
            system_prompt = (
                f"You are Aria, a premium AI Rewards Concierge. The current user is {user_id}. "
                "You understand and speak both English and Hindi naturally. "
                "Use the tools provided to resolve queries. Ensure strict eligibility checks. "
                "If points are insufficient, explain options clearly. "
                "Respond in English or Hindi based on the user's input. "
                "CRITICAL GUARDRAIL: You must ONLY assist with questions, details, searches, and redemptions related to rewards, points, or loyalty tiers. "
                "Do not discuss or answer questions about unrelated topics (like weather, general knowledge, coding, politics, etc.). "
                "If the user asks an unrelated question, politely pivot back and ask how you can help them with their rewards."
            )
            response = client.messages.create(
                model="claude-3-5-sonnet-20241022",
                max_tokens=1000,
                system=system_prompt,
                tools=claude_tools,
                messages=messages
            )
            
            bot_text = ""
            # Process tool calls in Claude response
            for content in response.content:
                if content.type == "text":
                    bot_text += content.text
                elif content.type == "tool_use":
                    tool_name = content.name
                    tool_input = content.input
                    tool_calls_made.append({"tool_name": tool_name, "arguments": tool_input})
                    
                    # Execute tool
                    tool_res = {}
                    if tool_name == "get_user_profile":
                        tool_res = get_user_profile(user_id)
                    elif tool_name == "search_rewards":
                        tool_res = search_rewards(tool_input.get("query"), tool_input.get("category"), tool_input.get("max_points"), user_id=user_id)
                    elif tool_name == "check_eligibility":
                        tool_res = check_eligibility(user_id, tool_input.get("reward_id"))
                    elif tool_name == "generate_earn_path":
                        tool_res = generate_earn_path(user_id, tool_input.get("reward_id"))
                    elif tool_name == "redeem_reward":
                        tool_res = redeem_reward(user_id, tool_input.get("reward_id"), tool_input.get("idempotency_key"))
                        
                    # Feed tool response back to Claude to get final description
                    tool_msg_history = messages + [
                        {"role": "assistant", "content": [content]},
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "tool_result",
                                    "tool_use_id": content.id,
                                    "content": json.dumps(tool_res)
                                }
                            ]
                        }
                    ]
                    
                    final_response = client.messages.create(
                        model="claude-3-5-sonnet-20241022",
                        max_tokens=1000,
                        system=system_prompt,
                        tools=claude_tools,
                        messages=tool_msg_history
                    )
                    
                    bot_text += "".join([c.text for c in final_response.content if c.type == "text"])
                    
            add_log("Reasoner (Claude)", "Executed complex reasoning and tool calls via Claude 3.5 Sonnet API", int((time.time() - start_time) * 1000))
            return bot_text, tool_calls_made, "Claude 3.5 Sonnet"
            
        except Exception as e:
            add_log("Reasoner (Claude)", f"Claude API Error: {str(e)}. Falling back to local simulator.", 5)

    # 2. Local High-Fidelity Simulator
    # Runs the actual tool functions on database data and generates natural response with English/Hindi options.
    user_profile = get_user_profile(user_id)
    bot_response = ""
    
    if intent == "profile":
        # Tool call
        tool_calls_made.append({"tool_name": "get_user_profile", "arguments": {"user_id": user_id}})
        p = user_profile
        bot_response = (
            f"Hello {p['name']}! Your current points balance is {p['points_balance']:,} points "
            f"(Tier: {p['tier']}).\n\n"
            f"Note: Your {p['expiring_points']:,} points are expiring on {p['expiry_date']}. "
            "Please redeem them before they expire. (Aapke points expire hone wale hain, kripya redeem kar lein!)"
        )
        
    elif intent == "expiry":
        tool_calls_made.append({"tool_name": "get_user_profile", "arguments": {"user_id": user_id}})
        p = user_profile
        # Suggest rewards that fit the expiring points balance and are region/tier eligible
        matching_rewards = search_rewards(max_points=p['expiring_points'], user_id=user_id)
        eligible_rewards = []
        for r in matching_rewards:
            elig = check_eligibility(user_id, r["reward_id"])
            if elig.get("region_eligible", True) and elig.get("tier_eligible", True):
                eligible_rewards.append(r)
        rewards_list = "\n".join([f"- **{r['name']}** ({r['points_cost']} pts) - {r['description']}" for r in eligible_rewards[:3]])
        
        bot_response = (
            f"Your {p['expiring_points']:,} points are expiring soon on {p['expiry_date']}!\n\n"
            "Here are some rewards you can redeem instantly (Aap ye rewards redeem kar sakte hain):\n"
            f"{rewards_list}\n\n"
            "Tell me the name of the reward you want to redeem."
        )
        
    elif intent == "search":
        category = params.get("category")
        query = params.get("query")
        tool_calls_made.append({"tool_name": "search_rewards", "arguments": params})
        
        rewards = search_rewards(query=query, category=category, user_id=user_id)
        if not rewards:
            bot_response = (
                "Sorry, I could not find any matching rewards. "
                "Kripya dusre categories search karein (Food, Travel, Shopping, Entertainment)."
            )
        else:
            eligible_rewards = []
            ineligible_rewards = []
            for r in rewards:
                elig = check_eligibility(user_id, r["reward_id"])
                if elig["eligible"]:
                    eligible_rewards.append((r, elig))
                elif elig.get("region_eligible", True):
                    ineligible_rewards.append((r, elig))
            
            bot_response = ""
            if eligible_rewards:
                bot_response += "Here are the rewards you are currently eligible to redeem:\n\n"
                for r, elig in eligible_rewards[:4]:
                    bot_response += (
                        f"🎁 **{r['name']}** ({r['points_cost']:,} pts)\n"
                        f"   • {r['description']}\n"
                        f"   • Category: {r['category']} | Region: {r['region_restriction']}\n\n"
                    )
            
            if ineligible_rewards and (not eligible_rewards or not query):
                bot_response += "Aspirational Rewards (Earn more points to unlock):\n\n"
                for r, elig in ineligible_rewards[:3]:
                    bot_response += (
                        f"🔒 **{r['name']}** ({r['points_cost']:,} pts) - *Shortfall: {elig['points_shortfall']:,} pts*\n"
                        f"   • {r['description']}\n"
                        f"   • Category: {r['category']} | Tier Required: {r['tier_restriction']}\n\n"
                    )
            
            bot_response += "Which reward would you like to redeem or find out more about?"
            
    elif intent == "redeem":
        reward_id = params.get("reward_id")
        if not reward_id:
            bot_response = "Which reward would you like to redeem? Kripya reward ka naam batayein."
        else:
            reward = REWARDS_CATALOG.get(reward_id)
            if not reward:
                bot_response = "Reward not found in the catalog."
            else:
                elig = check_eligibility(user_id, reward_id)
                tool_calls_made.append({"tool_name": "check_eligibility", "arguments": {"user_id": user_id, "reward_id": reward_id}})
                
                if elig["eligible"]:
                    # Create dummy idempotency key for this redemption
                    idemp_key = f"idemp-{uuid.uuid4().hex[:8]}"
                    tool_calls_made.append({"tool_name": "redeem_reward", "arguments": {"user_id": user_id, "reward_id": reward_id, "idempotency_key": idemp_key}})
                    
                    res = redeem_reward(user_id, reward_id, idemp_key)
                    if res["success"]:
                        bot_response = (
                            f"Redemption Successful!\n\n"
                            f"I have redeemed **{reward['name']}** for you.\n"
                            f"Voucher Code: `{res['voucher_code']}`\n"
                            f"Points Deducted: {res['points_deducted']:,} pts\n"
                            f"New Balance: {res['new_balance']:,} pts\n\n"
                            f"Voucher code successfully generated. Enjoy your reward!"
                        )
                    else:
                        bot_response = f"Redemption failed: {res['message']}"
                else:
                    # Check if user is ineligible for a reason other than points shortfall (like already redeemed)
                    if "Already redeemed" in elig["reason"] or elig["points_shortfall"] == 0:
                        bot_response = (
                            f"Cannot redeem **{reward['name']}**.\n"
                            f"Reason: {elig['reason']}"
                        )
                    else:
                        # Not eligible! Trigger Aspirational Earn Mode
                        tool_calls_made.append({"tool_name": "generate_earn_path", "arguments": {"user_id": user_id, "reward_id": reward_id}})
                        earn_res = generate_earn_path(user_id, reward_id)
                        
                        options_text = ""
                        for o in earn_res["earn_options"]:
                            options_text += f"- **{o['title']}**\n   {o['description']}\n\n"
                            
                        bot_response = (
                            f"You do not have enough points to redeem {reward['name']}.\n"
                            f"• Required: {reward['points_cost']:,} pts\n"
                            f"• Current Balance: {user_profile['points_balance']:,} pts\n"
                            f"• Shortfall: {elig['points_shortfall']:,} pts\n\n"
                            f"Aspirational Earn Mode Active (Points kamaane ke options):\n\n"
                            f"{options_text}"
                            f"Would you like to explore these options?"
                        )
                    
    elif intent == "earn":
        reward_id = "reward_2" # Taj Hotels is standard high aspirational
        tool_calls_made.append({"tool_name": "generate_earn_path", "arguments": {"user_id": user_id, "reward_id": reward_id}})
        earn_res = generate_earn_path(user_id, reward_id)
        
        options_text = ""
        for o in earn_res["earn_options"]:
            options_text += f"- **{o['title']}**\n   {o['description']}\n\n"
            
        bot_response = (
            f"Earning recommendations for **{REWARDS_CATALOG[reward_id]['name']}**:\n\n"
            f"{options_text}"
        )
        
    else: # Chat & Greet
        # Detect if user mentioned a category in their chat
        mentioned_cat = None
        user_input_lower = user_input.lower()
        if any(c in user_input_lower for c in ["food", "khaana", "pizza", "starbucks", "restaurant"]):
            mentioned_cat = "Food"
        elif any(c in user_input_lower for c in ["travel", "hotel", "ride", "uber", "taj"]):
            mentioned_cat = "Travel"
        elif any(c in user_input_lower for c in ["shopping", "amazon", "gift"]):
            mentioned_cat = "Shopping"
        elif any(c in user_input_lower for c in ["entertainment", "movie", "pvr"]):
            mentioned_cat = "Entertainment"

        p = user_profile
        # Try to find rewards matching the mentioned category and user's points balance
        matching_rewards = search_rewards(category=mentioned_cat, max_points=p["points_balance"], user_id=user_id)
        
        # If no eligible rewards in that category, fall back to matching rewards without category constraint
        if not matching_rewards and mentioned_cat:
            matching_rewards = search_rewards(category=mentioned_cat, user_id=user_id)
            
        # Fall back to general if no matches at all
        if not matching_rewards:
            matching_rewards = search_rewards(max_points=p["points_balance"], user_id=user_id)
            
        eligible_rewards = []
        for r in matching_rewards:
            elig = check_eligibility(user_id, r["reward_id"])
            if elig.get("region_eligible", True) and elig.get("tier_eligible", True):
                eligible_rewards.append(r)
                
        recommended = eligible_rewards[0] if eligible_rewards else REWARDS_CATALOG["reward_1"]
        
        # Check if user input contains generic greeting or unrelated query
        is_greeting = any(w in user_input_lower for w in ["hi", "hello", "hey", "hola", "namaste", "greetings", "good morning", "good afternoon", "good evening", "how are you", "what is your name", "who are you"])
        
        if is_greeting:
            bot_response = (
                f"Hello {p['name']}! I am Aria, your AI Rewards Concierge. \n\n"
                f"Your points balance is {p['points_balance']:,} and you are a {p['tier']} member. "
                f"Note that your {p['expiring_points']:,} points are expiring on {p['expiry_date']}!\n\n"
                f"Based on your profile, I recommend redeeming the **{recommended['name']}** ({recommended['points_cost']} pts). "
                f"How can I help you with your rewards catalog today?"
            )
        else:
            # Pivot back to rewards
            bot_response = (
                f"I can only help you with questions related to rewards, points balance, and loyalty program details. \n\n"
                f"Your points balance is {p['points_balance']:,} ({p['tier']} member). "
                f"I recommend checking out the **{recommended['name']}** ({recommended['points_cost']} pts). "
                f"Would you like to search rewards, check profile, or redeem?"
            )
        
    add_log("Reasoner (Claude)", "Generated simulated response with high-fidelity Hinglish rules", int((time.time() - start_time) * 1000))
    return bot_response, tool_calls_made, "Local Simulator (Claude 3.5)"


def run_preloading_engine(user_id: str) -> Dict[str, Any]:
    """
    Simulates / implements the Pre-Loading Engine. Fetches profile and preloads context.
    """
    start_time = time.time()
    
    # Pre-loading fetches user data and triggers proactive alerts
    profile = get_user_profile(user_id)
    
    # Fetch user's specific catalog of available rewards, falling back to global
    available_rewards = profile.get("available_rewards", REWARDS_CATALOG)
    
    # Preloaded recommendations based on points, region, and tiers
    eligible_rewards = []
    for r_id, r in available_rewards.items():
        # Quick filters
        points_ok = r["points_cost"] <= profile["points_balance"]
        
        region_ok = True
        if r["region_restriction"] != "All":
            allowed = [x.strip().lower() for x in r["region_restriction"].split(",")]
            region_ok = profile["region"].lower() in allowed
            
        tier_ok = True
        if r["tier_restriction"] != "All":
            user_tier_rank = {"Silver": 1, "Gold": 2, "Platinum": 3}.get(profile["tier"], 0)
            req_tier_rank = {"Silver": 1, "Gold": 2, "Platinum": 3}.get(r["tier_restriction"], 0)
            tier_ok = user_tier_rank >= req_tier_rank
            
        if points_ok and region_ok and tier_ok:
            eligible_rewards.append(r)
            
    latency_ms = int((time.time() - start_time) * 1000)
    add_log("Pre-Loading", f"Preloaded profile for '{profile['name']}' and {len(eligible_rewards)} eligible vouchers in {latency_ms}ms", latency_ms)
    
    return {
        "user_profile": profile,
        "preloaded_recommendations": eligible_rewards[:3],
        "latency_ms": latency_ms
    }
