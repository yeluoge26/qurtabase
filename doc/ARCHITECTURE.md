# AI Football Quant Terminal — Architecture

> Version: 1.1 | 2026-02-27

---

## System Architecture Overview

```
                         ┌─────────────────────┐
                         │   YouTube / TikTok   │
                         │     Livestream        │
                         └─────────┬───────────┘
                                   │ RTMPS
                         ┌─────────┴───────────┐
                         │    OBS Studio        │
                         │  Browser Source       │
                         │  1920x1080 / 30fps   │
                         └─────────┬───────────┘
                                   │ http://localhost
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                        Nginx :80                            │
    │                    (Reverse Proxy)                          │
    │                                                             │
    │  /           → Frontend :80  (React SPA)                   │
    │  /api/*      → Backend :8000 (REST API)                    │
    │  /ws/*       → Backend :8000 (WebSocket upgrade)           │
    │  /admin/*    → Backend :8000 (Static files)                │
    └───────┬──────────────────────┬──────────────────────────────┘
            │                      │
   ┌────────┴────────┐    ┌───────┴─────────────────────────────┐
   │   Frontend       │    │           Backend                    │
   │   React 18       │    │           FastAPI                    │
   │   + Vite         │    │                                     │
   │                  │    │  ┌─────────┐  ┌──────────────────┐ │
   │  Components:     │    │  │  Admin   │  │  WebSocket       │ │
   │  QuantTerminal   │    │  │  API     │  │  Manager         │ │
   │  EventTape       │    │  │  (CRUD)  │  │  (broadcast)     │ │
   │  MarketEdge      │    │  └────┬────┘  └───────┬──────────┘ │
   │  ExplainPanel    │    │       │               │             │
   │  ReportBanner    │    │  ┌────┴───────────────┴──────────┐ │
   │                  │    │  │       Engine Pipeline           │ │
   │  Hooks:          │    │  │                                │ │
   │  useWebSocket    │    │  │  LivePredictor (XGBoost)       │ │
   │                  │    │  │  → MarketEngine                │ │
   │  Utils:          │    │  │  → ExplainEngine               │ │
   │  mapPayload      │    │  │  → UncertaintyEngine           │ │
   │  i18n            │    │  │  → QuantEngine                 │ │
   │                  │    │  │  → MatchStateStore              │ │
   │  Output:         │    │  └──────────┬─────────────────────┘ │
   │  dist/ (nginx)   │    │             │                       │
   └──────────────────┘    │  ┌──────────┴─────────────────────┐ │
                           │  │       Data Clients              │ │
                           │  │                                │ │
                           │  │  SportMonksClient (v3 API)     │ │
                           │  │  FootballAPIClient (fallback)  │ │
                           │  │  OddsAPIClient (The Odds API)  │ │
                           │  │  CacheManager (in-memory)      │ │
                           │  └──────────┬─────────────────────┘ │
                           └─────────────┼───────────────────────┘
                                         │
                ┌────────────────────────┼───────────────────────┐
                │                        │                       │
     ┌──────────┴──────────┐  ┌─────────┴────────┐  ┌──────────┴──────────┐
     │   SportMonks API    │  │  The Odds API     │  │   Redis :6379       │
     │   (Live data)       │  │  (Betting odds)   │  │   (Cache + future   │
     │                     │  │                   │  │    PubSub)          │
     │   Free Plan:        │  │   Active:         │  │                    │
     │   Danish/Scottish   │  │   EPL real odds   │  │   Stores:          │
     │                     │  │   20 events       │  │   - API responses  │
     │   Paid Plan:        │  │                   │  │   - Match state    │
     │   EPL + all leagues │  │                   │  │   - Session data   │
     └────────────────────┘  └───────────────────┘  └───────────────────┘
```

---

## Data Flow Diagram

```
                    External Data Sources
                    =====================

    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  SportMonks   │   │  The Odds    │   │  football-   │
    │  Live API     │   │  API         │   │  data.co.uk  │
    │  (30s poll)   │   │  (60s poll)  │   │  (training)  │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
           │                  │                   │
           ▼                  ▼                   ▼
    ┌──────────────────────────────┐      ┌──────────────┐
    │      Backend Processing      │      │   Training    │
    │                              │      │   Pipeline    │
    │  1. Fetch raw data           │      │              │
    │  2. Parse stats/events       │      │  features.py │
    │  3. Build feature vector     │      │  train.py    │
    │  4. XGBoost predict_proba    │      │  → .pkl      │
    │  5. Poisson live correction  │      └──────────────┘
    │  6. Market implied + edge    │
    │  7. Explain top factors      │
    │  8. Uncertainty CI95/Brier   │
    │  9. Match state delta calc   │
    │  10. Assemble v1.1 payload   │
    └──────────────┬───────────────┘
                   │
                   ▼ WebSocket push (2s interval)
    ┌──────────────────────────────┐
    │      v1.1 JSON Payload       │
    │                              │
    │  {                           │
    │    meta: { health, seq }     │
    │    match: { score, minute }  │
    │    probability: { H/D/A }   │
    │    market: { odds, edge }   │
    │    stats: { shots, xG... }  │
    │    events: [ ... ]          │
    │    quant: { pressure... }   │
    │    uncertainty: { CI95 }    │
    │    explain: { factors }     │
    │    report: { HT/FT }       │
    │  }                           │
    └──────────────┬───────────────┘
                   │
                   ▼ mapPayload.js
    ┌──────────────────────────────┐
    │      Frontend Rendering      │
    │                              │
    │  ┌───────────────────────┐  │
    │  │ State Bar (meta)      │  │
    │  ├───────────────────────┤  │
    │  │ Probability + Delta   │  │
    │  │ Market Edge (Pro)     │  │
    │  │ Explain (Pro)         │  │
    │  ├───────────────────────┤  │
    │  │ Trend Sparklines      │  │
    │  ├───────────────────────┤  │
    │  │ Stats + Event Tape    │  │
    │  ├───────────────────────┤  │
    │  │ Quant Indicators      │  │
    │  │ Uncertainty (Elite)   │  │
    │  └───────────────────────┘  │
    │                              │
    │  1920 x 1080 Bloomberg UI   │
    └──────────────────────────────┘
```

---

## File Structure Map

```
e:\code\qurtabase\
│
├── doc/
│   ├── implementation-guide.md      # Original v1.0 guide
│   ├── v1.1 implement.txt          # v1.1 upgrade spec
│   ├── feature-roadmap.md          # Feature roadmap (P0-P3)
│   ├── PRD.md                      # Product Requirements Document
│   ├── ARCHITECTURE.md             # This file
│   └── TODO.md                     # Feature checklist tracker
│
├── frontend/                        # React 18 + Vite
│   ├── package.json
│   ├── vite.config.js               # Dev proxy: /api,/ws → localhost:8000
│   ├── index.html
│   └── src/
│       ├── main.jsx                 # React entry point
│       ├── App.jsx                  # Match selector → QuantTerminal
│       ├── QuantTerminal.jsx        # Main terminal (5-layer UI)
│       ├── hooks/
│       │   └── useWebSocket.js      # WS with Fibonacci backoff
│       ├── utils/
│       │   ├── mapPayload.js        # snake_case → camelCase mapper
│       │   └── i18n.js              # EN/ZH translations
│       └── components/
│           ├── EventTape.jsx        # Match events log
│           ├── MarketEdge.jsx       # Odds + implied prob + edge
│           ├── ExplainPanel.jsx     # Why Delta (top 3 factors)
│           └── ReportBanner.jsx     # HT/FT report notification
│
├── backend/                         # FastAPI Python
│   ├── main.py                      # App entry: WS, Admin API, Demo, Live
│   ├── config.py                    # Settings (env vars, API keys)
│   ├── requirements.txt
│   ├── data/
│   │   ├── sportmonks_client.py     # SportMonks v3 API (primary)
│   │   ├── api_client.py           # API-Football (fallback)
│   │   ├── odds_client.py          # The Odds API
│   │   └── cache.py                # In-memory + optional Redis cache
│   ├── models/
│   │   ├── predictor.py            # LivePredictor (XGBoost + Poisson)
│   │   ├── quant.py                # QuantEngine (fallback)
│   │   └── trained/
│   │       ├── model_calibrated.pkl # Production model
│   │       ├── model_xgb.pkl       # XGBoost raw
│   │       ├── model_logistic.pkl  # Logistic baseline
│   │       └── model_meta.json     # Feature names, class mapping
│   ├── services/
│   │   ├── market_engine.py        # Implied prob + edge calculation
│   │   ├── explain_engine.py       # Top factors for probability delta
│   │   └── uncertainty_engine.py   # CI95, Brier rolling, sharpness
│   ├── store/
│   │   └── match_state.py          # Per-match state (delta, events, Brier)
│   ├── ws/
│   │   └── manager.py              # WebSocket connection manager
│   ├── static/
│   │   ├── index.html              # Admin panel (served at /admin/)
│   │   └── admin.html              # Admin panel (original)
│   └── training/
│       ├── train.py                # 3-model comparison pipeline
│       ├── features.py             # Feature engineering (13 features)
│       ├── generate_data.py        # Simulated data generator
│       └── data/
│           └── matches.csv         # Training data (3000 simulated)
│
├── model/                           # Original model prototypes
│   ├── features.py
│   ├── predictor.py
│   ├── train.py
│   ├── generate_data.py
│   └── model_meta.json
│
├── jsx/
│   └── quant-terminal.jsx          # Original React prototype
│
├── docker-compose.yml              # 4 services: redis, backend, frontend, nginx
├── Dockerfile.backend              # Python 3.11-slim
├── Dockerfile.frontend             # Node 20-alpine build + nginx serve
├── nginx.conf                      # Reverse proxy config
├── .env                            # API keys (not committed)
├── .env.example                    # Template for API keys
└── .gitignore
```

---

## Engine Pipeline Detail

```
                Input: Raw Live Data + Odds
                           │
                ┌──────────┴──────────┐
                │   LivePredictor     │
                │                     │
                │  1. build_features  │  13 features → numpy array
                │  2. model.predict   │  XGBoost → [P(A), P(D), P(H)]
                │  3. poisson_update  │  Score + time → adjusted probs
                │  4. compute_quant   │  Pressure, momentum, volatility
                │                     │
                │  Output:            │
                │  probability{}      │  home/draw/away %
                │  quant{}            │  7 indicators
                └──────────┬──────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
  │ MarketEngine│  │ExplainEngine│  │Uncertainty  │
  │             │  │             │  │Engine       │
  │ odds →      │  │ cur vs prev │  │ prob →      │
  │ implied     │  │ state diff  │  │ CI95 range  │
  │ prob        │  │ → top 3     │  │ Brier score │
  │ edge =      │  │   factors   │  │ sharpness   │
  │ AI - market │  │   + summary │  │ MC runs     │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │                │                 │
         └─────────────────┼─────────────────┘
                           │
                ┌──────────┴──────────┐
                │   MatchStateStore   │
                │                     │
                │  - last_probability │  → delta calc
                │  - event_ids set    │  → dedup
                │  - brier_buffer[]   │  → rolling window
                │  - last_update_ts   │  → health detection
                │  - seq counter      │  → ordering
                └──────────┬──────────┘
                           │
                           ▼
                   v1.1 JSON Payload
                   (10 sections, ~2KB)
                           │
                           ▼
                   WebSocket broadcast
                   (every 2 seconds)
```

---

## Docker Compose Topology

```
  ┌────────────────────────────────────────────────────────────┐
  │                    Docker Network                           │
  │                                                            │
  │  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐ │
  │  │  Redis    │    │   Backend    │    │    Frontend      │ │
  │  │  :6379    │◄───│   :8000     │    │    :80 (nginx)   │ │
  │  │          │    │              │    │                  │ │
  │  │  alpine  │    │  python:3.11 │    │  node:20 build  │ │
  │  │  7-alpine│    │  FastAPI     │    │  + nginx:alpine │ │
  │  └──────────┘    │  uvicorn     │    └────────┬────────┘ │
  │                  │              │              │          │
  │                  │  Volumes:    │              │          │
  │                  │  ./models/   │              │          │
  │                  │   trained/   │              │          │
  │                  └──────┬───────┘              │          │
  │                         │                      │          │
  │                  ┌──────┴──────────────────────┴────────┐ │
  │                  │         Nginx  :80 / :443            │ │
  │                  │         (Reverse Proxy)              │ │
  │                  │                                     │ │
  │                  │  /        → frontend:80             │ │
  │                  │  /api/*   → backend:8000            │ │
  │                  │  /ws/*    → backend:8000 (upgrade)  │ │
  │                  │  /admin/* → backend:8000 (static)   │ │
  │                  └─────────────────────────────────────┘ │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
                              │
                     Exposed ports:
                     80  → Nginx (main entry)
                     443 → Nginx (HTTPS, future)
                     8000 → Backend (direct access)
                     5173 → Frontend (direct access)
                     6379 → Redis (direct access)
```

---

## Mode Selection Logic

```
Startup:
  │
  ├── SPORTMONKS_API_KEY set?
  │     ├── Yes → Mode: LIVE, Source: SportMonks
  │     └── No ──┐
  │              │
  │              ├── FOOTBALL_API_KEY set?
  │              │     ├── Yes → Mode: LIVE, Source: API-Football
  │              │     └── No → Mode: DEMO (simulated match data)
  │
  ├── ODDS_API_KEY set?
  │     ├── Yes → Real odds injected (even in DEMO mode)
  │     └── No → Simulated odds
  │
  └── Match Request (ws/{match_id}):
        │
        ├── match_id == "demo" → Always demo simulator
        │     └── + real odds if ODDS_API_KEY present
        │
        └── match_id == other → Live mode if API key available
              └── Fallback to demo if API fails
```
