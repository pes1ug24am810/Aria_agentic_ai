import sys
import os
import time
import uuid

# Add directory to sys path so we can import modules
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import config
# Clear API keys for unit testing to ensure deterministic local simulation runs
config.GROQ_API_KEY = ""
config.ANTHROPIC_API_KEY = ""

import database
database.supabase_enabled = False

from database import USER_DB, REWARDS_CATALOG
from tools import (
    get_user_profile,
    search_rewards,
    check_eligibility,
    generate_earn_path,
    redeem_reward
)
from agent import run_groq_intent

def run_tests():
    print("=========================================================")
    print("            ARIA BACKEND UNIT & SECURITY TESTS           ")
    print("=========================================================")
    print()

    # Test 1: GetUserProfile Tool
    print("[TEST 1] Testing GetUserProfile...")
    profile = get_user_profile("user_1")
    assert profile["name"] == "Rahul Sharma", "Failed profile name verification"
    assert profile["points_balance"] == 8500, "Failed profile points balance"
    assert profile["tier"] == "Gold", "Failed profile tier verification"
    print("[OK] GetUserProfile test passed.")
    print()

    # Test 2: SearchRewards Tool
    print("[TEST 2] Testing SearchRewards...")
    food_rewards = search_rewards(category="Food")
    assert len(food_rewards) >= 2, "Failed to retrieve food category rewards"
    print(f"[OK] SearchRewards test passed. Found {len(food_rewards)} food rewards.")
    print()

    # Test 3: CheckEligibility Tool
    print("[TEST 3] Testing CheckEligibility (Eligible)...")
    elig1 = check_eligibility("user_1", "reward_3") # Starbucks Card - 1500 pts
    assert elig1["eligible"] == True, "User 1 should be eligible for Starbucks Card"
    
    print("[TEST 3.1] Testing CheckEligibility (Insufficient Points - Aspirational)...")
    elig2 = check_eligibility("user_1", "reward_2") # Taj Hotel - 12,000 pts
    assert elig2["eligible"] == False, "User 1 should not be eligible for Taj Hotel"
    assert elig2["points_shortfall"] == 3500, f"Expected points shortfall 3500, got {elig2['points_shortfall']}"
    print("[OK] CheckEligibility validation rules passed.")
    print()

    # Test 4: GenerateEarnPath Tool (Aspirational Earn Mode)
    print("[TEST 4] Testing GenerateEarnPath...")
    earn_path = generate_earn_path("user_1", "reward_2")
    assert earn_path["has_shortfall"] == True, "Should have a shortfall"
    assert len(earn_path["earn_options"]) > 0, "Should contain earn options"
    print(f"[OK] GenerateEarnPath test passed. Shortfall: {earn_path['shortfall']} pts. Generated {len(earn_path['earn_options'])} earn suggestions.")
    print()

    # Test 5: RedeemReward Tool & Security Gates (Idempotency, Rate Limiting, & Double Redemption)
    print("[TEST 5] Testing RedeemReward & Security Guards...")
    
    # 5.1 Fresh Redemption
    idemp_key = f"test-key-{uuid.uuid4()}"
    original_balance = USER_DB["user_1"]["points_balance"]
    res1 = redeem_reward("user_1", "reward_3", idemp_key)
    
    assert res1["success"] == True, "Redemption failed"
    assert res1["points_deducted"] == 1500, "Should deduct 1500 points"
    new_balance = USER_DB["user_1"]["points_balance"]
    assert original_balance - new_balance == 1500, f"Expected 1500 points deducted, got balance difference: {original_balance - new_balance}"
    print("[OK] RedeemReward (Fresh transaction) completed successfully.")
    
    # 5.2 Idempotency - Duplicate Transaction Prevention
    # Send request again with SAME key. Should return previous coupon, NOT deduct points.
    time.sleep(3) # Wait 3 seconds to avoid triggering rate limiter during idempotency check
    res2 = redeem_reward("user_1", "reward_3", idemp_key)
    
    assert res2["success"] == True, "Idempotent response failed"
    assert res2["idempotent"] == True, "Should be flagged as idempotent duplicate"
    assert res2["voucher_code"] == res1["voucher_code"], "Voucher codes must match"
    
    final_balance = USER_DB["user_1"]["points_balance"]
    assert final_balance == new_balance, f"Points were deducted twice! Balance before duplicate: {new_balance}, after duplicate: {final_balance}"
    print("[OK] Idempotency Security Guard verified: Stopped duplicate points charge.")
 
    # 5.3 Rate Limiting - Prevention of Rapid Clicks / Double Submission
    # Send another redemption with a DIFFERENT key but immediately (no sleep)
    new_idemp_key = f"test-key-{uuid.uuid4()}"
    res3 = redeem_reward("user_1", "reward_3", new_idemp_key)
    
    assert res3["success"] == False, "Rate limit failed to block rapid consecutive requests"
    assert res3["error_type"] == "RATE_LIMITED", f"Expected RATE_LIMITED error, got: {res3.get('error_type')}"
    print("[OK] Rate Limiting Security Guard verified: Blocked rapid double submission.")
    
    # 5.4 Double Redemption Prevention - Prevent user from redeeming same reward twice
    time.sleep(3) # Wait 3 seconds to clear rate limit
    new_idemp_key_2 = f"test-key-{uuid.uuid4()}"
    res4 = redeem_reward("user_1", "reward_3", new_idemp_key_2)
    
    assert res4["success"] == False, "Expected double redemption to be blocked"
    assert res4["error_type"] == "INELIGIBLE", f"Expected INELIGIBLE error, got: {res4.get('error_type')}"
    assert "Already redeemed" in res4["message"], f"Expected already redeemed error message, got: {res4.get('message')}"
    print("[OK] Double Redemption Prevention verified: Blocked second redemption of same reward.")
    print()

    # Test 6: Enhanced Query & Intent Parsing
    print("[TEST 6] Testing Enhanced Intent Parsing & Search...")
    
    # 6.1 Multi-word AND search matching
    search_res = search_rewards(query="Pizza Hut voucher coupon")
    assert len(search_res) == 1, f"Expected exactly 1 reward, got {len(search_res)}"
    assert search_res[0]["reward_id"] == "reward_1", "Expected Pizza Hut Voucher"
    
    # 6.2 Generic "list of rewards" query should have empty parameters (returns all rewards)
    intent_res1 = run_groq_intent("give me the list of rewards available")
    assert intent_res1["intent"] == "search", f"Expected intent 'search', got {intent_res1['intent']}"
    assert "query" not in intent_res1["parameters"], f"Expected no 'query' parameter for generic list request, got {intent_res1['parameters'].get('query')}"
    
    # 6.3 Punctuation cleaning
    intent_res2 = run_groq_intent("Pizza Hut voucher?")
    assert intent_res2["intent"] == "search"
    assert intent_res2["parameters"].get("query") == "pizza hut", f"Expected 'pizza hut', got {intent_res2['parameters'].get('query')}"
    
    # 6.4 Category matching inside intent router
    intent_res3 = run_groq_intent("i asked for travel")
    assert intent_res3["intent"] == "search", f"Expected 'search', got {intent_res3['intent']}"
    assert intent_res3["parameters"].get("category") == "Travel", f"Expected category 'Travel', got {intent_res3['parameters'].get('category')}"
    
    # 6.5 Recommendation override inside Chat fallback
    from agent import run_claude_reasoner
    bot_resp, _, _ = run_claude_reasoner("user_1", {"intent": "chat", "parameters": {}}, "i asked for travel", [])
    assert "Uber Elite Ride Pass" in bot_resp, f"Expected Uber Elite Ride Pass to be recommended in fallback chat response, got: {bot_resp}"
    
    print("[OK] Enhanced query & intent parsing tests passed.")
    print()

    # Test 7: Already Redeemed Filtering
    print("[TEST 7] Testing Already Redeemed Filtering...")
    # user_1 has redeemed Pizza Hut Voucher
    search_res1 = search_rewards(query="Pizza Hut", user_id="user_1")
    assert len(search_res1) == 0, f"Expected 0 results for user_1 because they already redeemed Pizza Hut, got {len(search_res1)}"
    
    # user_2 has not redeemed Pizza Hut Voucher
    search_res2 = search_rewards(query="Pizza Hut", user_id="user_2")
    assert len(search_res2) == 1, f"Expected 1 result for user_2, got {len(search_res2)}"
    assert search_res2[0]["reward_id"] == "reward_1"
    
    # Preloading recommendations should not contain Pizza Hut Voucher for user_1
    from agent import run_preloading_engine
    preload_res = run_preloading_engine("user_1")
    rec_names = [r["name"] for r in preload_res["preloaded_recommendations"]]
    assert "Pizza Hut Voucher" not in rec_names, f"Expected Pizza Hut Voucher to be filtered out of recommendations for user_1, got {rec_names}"
    
    # Verify database catalog isolation and direct deletion
    # user_1 redeemed Starbucks Card (reward_3) in Test 5, so it should be deleted from user_1's catalog
    user_1_catalog = USER_DB["user_1"]["available_rewards"]
    assert "reward_3" not in user_1_catalog, "Starbucks Card should be deleted from user_1's catalog after redemption"
    
    # But user_2 did not redeem it, so it should still be in user_2's catalog
    user_2_catalog = USER_DB["user_2"]["available_rewards"]
    assert "reward_3" in user_2_catalog, "Starbucks Card should still be present in user_2's catalog"
    
    print("[OK] Already Redeemed Filtering test passed.")
    print()

    print("=========================================================")
    print("             ALL BACKEND SYSTEM TESTS PASSED             ")
    print("=========================================================")

if __name__ == "__main__":
    # Configure utf-8 encoding for standard output if python version supports it, or use safe printing
    sys.stdout.reconfigure(encoding='utf-8') if hasattr(sys.stdout, 'reconfigure') else None
    run_tests()
