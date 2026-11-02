-- Aria AI Rewards Concierge Supabase Schema

-- 1. Create Users Table
CREATE TABLE IF NOT EXISTS users (
    user_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    tier TEXT NOT NULL,
    points_balance INTEGER NOT NULL DEFAULT 0,
    region TEXT NOT NULL,
    email TEXT NOT NULL,
    expiring_points INTEGER NOT NULL DEFAULT 0,
    expiry_date DATE NOT NULL
);

-- 1.5 Create User Credentials (Login) Table
CREATE TABLE IF NOT EXISTS user_credentials (
    user_id TEXT PRIMARY KEY REFERENCES users(user_id) ON DELETE CASCADE,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL
);

-- 2. Create Rewards Catalog Table
CREATE TABLE IF NOT EXISTS rewards_catalog (
    reward_id TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    points_cost INTEGER NOT NULL,
    value_inr INTEGER NOT NULL,
    category TEXT NOT NULL,
    availability TEXT NOT NULL,
    region_restriction TEXT NOT NULL,
    tier_restriction TEXT NOT NULL,
    description TEXT,
    terms TEXT
);

-- 3. Create Redemption History Table
CREATE TABLE IF NOT EXISTS redemption_history (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    user_id TEXT REFERENCES users(user_id) ON DELETE CASCADE,
    reward_name TEXT NOT NULL,
    points INTEGER NOT NULL,
    date DATE NOT NULL DEFAULT CURRENT_DATE,
    status TEXT NOT NULL
);

-- 4. Create Execution Logs Table
CREATE TABLE IF NOT EXISTS execution_logs (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    event_type TEXT NOT NULL,
    details TEXT,
    latency_ms INTEGER DEFAULT 0,
    timestamp TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
