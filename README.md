# Aria: Premium AI Rewards Concierge 

Aria is a premium conversational AI rewards concierge built for loyalty programs. Aria helps members track their points balance, check points expiry, search for eligible rewards based on regional and tier constraints, and instantly redeem vouchers.

The application features live AI reasoning (using Anthropic Claude and Groq Llama), a fallback high-fidelity local simulator, and cloud database persistence (Supabase).

---

##  Key Features

###  Core (Brief Requirements)

* **Proactive Greeting** — Aria greets user on portal open with personalised recommendations
* **Natural Multi-Turn Dialogue** — No forms, no dropdowns, just conversation
* **Transparent Reasoning** — Aria explains why it recommends each reward
* **End-to-End Redemption** — Full flow completed inside the chat
* **Strict Validation** — Eligibility, balance, region, tier checked before every redemption

###  Innovations (Beyond the Brief)

1. **Aspirational Earn Mode**
   * When a user can't afford a reward, Aria doesn't say "insufficient points." It shows the exact shortfall and generates personalised earn options — dining at partner restaurants, referring friends, card signup, or buying points directly.

2. **Hallucination-Proof Engine**
   * Every recommendation is grounded in tool outputs from validated data. Claude never invents reward names, points costs, or terms.

3. **Hinglish & Code-Mixed Language Support**
   * Handles inputs like "Mujhe kuch food wala chahiye" natively. 200+ Hinglish stop-words, category mappings, and intent patterns built in.

4. **Points Expiry Urgency Engine**
   * Proactively alerts users about expiring points and surfaces rewards they can redeem right now before they lose them.

5. **Pre-Loading Engine**
   * User profile, eligible rewards, and recommendations are fetched the moment the chat opens — zero lag on first message.

---

## Tech Stack

* **Backend**: FastAPI (Python), Uvicorn, Pydantic, Supabase client
* **Frontend**: React (Vite, JS), Lucide Icons, Canvas Confetti
* **AI Models**: Anthropic Claude 3.5 Sonnet (Reasoner), Groq Llama 3.1 8B (Intent Router)
* **Database**: PostgreSQL (via Supabase) / Local Mock Database fallback

---

## Project Structure

```text
├── backend/
│   ├── main.py          # FastAPI application server & routes
│   ├── agent.py         # AI intent routing & local simulation reasoning graph
│   ├── tools.py         # Core business logic tools (search, check, redeem, earn path)
│   ├── database.py      # Database proxy connectors (Supabase & Local Fallback)
│   ├── config.py        # Environment variables loader
│   ├── schema.sql       # Database table definitions
│   ├── test_backend.py  # Unit, security, and integration test suite
│   ├── requirements.txt # Python dependencies list
│   └── venv/            # Python virtual environment (ignored)
│
├── frontend/
│   ├── src/
│   │   ├── App.jsx      # Main application state and graph orchestrator
│   │   └── components/  # UserProfileSidebar, ChatInterface, ArchitectureVisualizer, Login
│   ├── package.json     # Node dependencies list
│   └── index.html       # Vite HTML entry point
│
└── README.md            # This file
```

---

## Getting Started

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   # On Windows:
   venv\Scripts\activate
   # On macOS/Linux:
   source venv/bin/activate
   ```

3. Install python dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the `backend/` folder and populate it:
   ```env
   PORT=8000
   HOST=127.0.0.1
   GROQ_API_KEY=your_groq_api_key
   ANTHROPIC_API_KEY=your_anthropic_api_key
   SUPABASE_URL=your_supabase_url
   SUPABASE_KEY=your_supabase_key
   ```
   *(Note: If API keys or Supabase configurations are omitted, the server will automatically fall back to the offline high-fidelity local simulator and mock in-memory database).*

5. Start the FastAPI server:
   ```bash
   python main.py
   ```
   The backend will run on `http://localhost:8000`.

---

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install node dependencies:
   ```bash
   npm install
   ```

3. Start the Vite development server:
   ```bash
   npm run dev
   ```
   The frontend will run on `http://localhost:5173`.

---

## Running Automated Tests

To verify backend tool security and database isolation integrity, run the test suite:

```bash
cd backend
# Make sure virtual environment is active
python test_backend.py
```
