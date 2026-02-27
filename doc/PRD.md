# AI Football Quant Terminal — Product Requirements Document (PRD)

> Version: 1.1
> Date: 2026-02-27
> Status: In Development

---

## 1. Product Overview

### 1.1 Vision
A Bloomberg Terminal-style real-time football analytics platform that displays AI-predicted match probabilities, quantitative indicators, and market edge analysis during live matches. Designed for YouTube/TikTok livestreaming with a tiered membership monetization model.

### 1.2 Positioning
- **What it is**: Real-time data visualization terminal for football matches
- **What it is NOT**: A betting platform, a match broadcasting tool, or a video replay system
- **Compliance**: Data visualization only — no match footage, audio, or play-by-play replication
- **Data delay**: Minimum 30 seconds from live events (regulatory compliance)

### 1.3 Target Users
| User Type | Needs | Tier |
|-----------|-------|------|
| Casual football fan | Live score + basic probability | Free |
| Football analytics enthusiast | Market edge, explain factors, quant metrics | Pro |
| Professional bettor / data scientist | Uncertainty, calibration, CI intervals, report export | Elite |
| Content creator / livestreamer | Full terminal display for streaming | Pro/Elite |

---

## 2. Core Features

### 2.1 Real-Time Match Terminal (Free)

**5-Layer UI Architecture:**

```
Layer 1: STATE BAR
  League | Round | Home Score Away | Minute | Half
  Health Status | Data Delay | Source Info

Layer 2: PROBABILITY
  1X2 AI Probability (Home / Draw / Away)
  Delta indicators (change from previous update)
  Model confidence score

Layer 3: TREND
  Sparkline chart: probability over time
  Pressure index trend
  xG delta trend

Layer 4: STATS
  Two-column team comparison
  Shots, Possession, xG, Corners, Fouls, Cards
  Event Tape (last 3 events for Free tier)

Layer 5: QUANT
  Pressure Index, Momentum Score
  Volatility Index, Risk of Concede
  Expected Goal Window, Model Variance
```

### 2.2 Market Edge (Pro)
- **Market Implied Probability**: Derived from real bookmaker odds
- **Edge (AI - Market)**: Difference between AI prediction and market consensus
- **Real Odds Display**: Live odds from The Odds API
- **Monetization**: Core reason users upgrade to Pro

### 2.3 Explain Panel — Why Delta (Pro)
- Top 3 factors driving probability change
- Visual impact bars with up/down direction
- Factors: shots on target, pressure, goals, red cards, possession, xG, time decay
- Builds trust in the model's reasoning

### 2.4 Event Tape (Free: 3 events, Pro: 5-8)
- Bloomberg-style event log
- Supported events: GOAL, YELLOW, RED, SUB, VAR, PENALTY
- Newest first, with minute marker
- Color-coded by event type

### 2.5 Uncertainty & Calibration (Elite)
- CI95 confidence intervals for each outcome
- Rolling Brier Score (20-minute window)
- Sharpness metric (entropy-based)
- Monte Carlo run count
- Professional-grade model quality evidence

### 2.6 Admin Panel
- Web-based match management (/admin/)
- Add/update/toggle/delete managed matches
- Health status dashboard
- Match configuration: teams, Elo ratings, API IDs, odds sport key

---

## 3. Data Sources

### 3.1 Live Match Data
| Provider | Status | Coverage | Use |
|----------|--------|----------|-----|
| SportMonks v3 API | Connected (Free Plan) | Danish Superliga, Scottish Premiership | Live stats, events, scores |
| API-Football | Ready (Fallback) | Wide coverage (needs key) | Alternative live data source |

**Note**: EPL live data requires SportMonks paid plan upgrade.

### 3.2 Odds Data
| Provider | Status | Coverage | Use |
|----------|--------|----------|-----|
| The Odds API | Active | EPL, major leagues | Real-time betting odds |

### 3.3 Training Data
| Source | Status | Use |
|--------|--------|-----|
| football-data.co.uk | Simulated (3000 matches) | XGBoost training baseline |
| Understat / FBref | Not integrated | xG training data (future) |

---

## 4. Technical Architecture

### 4.1 System Components
```
[Frontend: React 18 + Vite]
    |
    |-- WebSocket (ws://host/ws/{match_id})
    |-- REST API (http://host/api/*)
    |
[Nginx Reverse Proxy]
    |
    |-- / → Frontend (SPA)
    |-- /api/ → Backend
    |-- /ws/ → Backend (WebSocket upgrade)
    |-- /admin/ → Backend (Static files)
    |
[Backend: FastAPI Python]
    |
    |-- WebSocket Manager (per-match broadcast)
    |-- LivePredictor (XGBoost + Poisson correction)
    |-- Market Engine (implied prob + edge)
    |-- Explain Engine (top delta factors)
    |-- Uncertainty Engine (CI95, Brier, sharpness)
    |-- Match State Store (per-match delta, events, rolling metrics)
    |-- Data Clients (SportMonks, API-Football, The Odds API)
    |
[Redis]
    |-- Cache layer
    |-- Future: PubSub broadcast, session storage
```

### 4.2 Data Flow
```
External APIs (SportMonks / Odds API)
    ↓ (30s polling)
Backend Data Clients
    ↓
Feature Builder → LivePredictor (XGBoost)
    ↓
Match State Store (delta calc, event dedup)
    ↓
Engine Pipeline: Market → Explain → Uncertainty → Quant
    ↓
v1.1 JSON Payload Assembly
    ↓ (2s push via WebSocket)
Frontend mapPayload.js → React Components
    ↓
Rendered Terminal UI (1920x1080)
    ↓ (OBS Browser Source)
YouTube / TikTok Livestream
```

### 4.3 WebSocket Protocol
- **URL**: `ws://host/ws/{match_id}`
- **Push interval**: 2 seconds
- **Reconnect**: Fibonacci backoff (3s → 5s → 8s → 13s)
- **Payload**: v1.1 JSON Schema (10 top-level sections)
- **Health states**: OK (green), DEGRADED (yellow), STALE (red)
- **Sequence numbering**: Monotonic `meta.seq` for ordering

### 4.4 Deployment
- **Containerized**: Docker Compose (4 services)
- **Services**: Redis 7, Backend (Python 3.11), Frontend (Node 20 build + nginx), Nginx (reverse proxy)
- **Ports**: 80 (nginx), 8000 (backend), 5173 (frontend direct), 6379 (redis)

---

## 5. AI/ML Model

### 5.1 Pre-Match Model
- **Algorithm**: Calibrated XGBoost Classifier
- **Features (13)**: Odds-implied probability (3), Elo ratings (2), shot stats (4), xG stats (2), corners (2)
- **Classes**: Home Win / Draw / Away Win
- **Output**: Probability vector + confidence score
- **Training data**: 3000 matches (currently simulated, needs real data upgrade)

### 5.2 In-Match Correction
- **Method**: Poisson-based live adjustment
- **Inputs**: Current score, minute, remaining time
- **Behavior**: Score-leader probability increases with time decay; draw probability contracts late-game

### 5.3 Evaluation Metrics
| Metric | Current | Target |
|--------|---------|--------|
| CV Accuracy | ~47% (simulated data) | >50% (real data) |
| Brier Score | Not tracked yet | <0.22 |
| LogLoss | Not tracked yet | <0.95 |
| Calibration | Not verified | Within 5% bins |

---

## 6. Membership Tiers

### 6.1 Free Tier
- 1X2 AI probability with delta
- Trend sparklines (probability, pressure, xG)
- Basic stats (shots, possession, xG)
- Event Tape (last 3 events)
- 30-second data delay

### 6.2 Pro Tier ($9.99/month)
- Everything in Free, plus:
- **Market Implied Probability + Edge (AI vs Market)** — core monetization driver
- **Explain Panel (Why Delta)** — top 3 factors
- Full Event Tape (5-8 events)
- Full Quant indicators (Pressure, Volatility, Risk, Goal Window)
- Faster data refresh (target: 15s delay)

### 6.3 Elite Tier ($29.99/month)
- Everything in Pro, plus:
- **Uncertainty**: CI95 intervals, rolling Brier, sharpness, MC runs
- Multi-match terminal (3-4 simultaneous matches)
- HT/FT report export (JSON + image snapshot)
- Historical key moment replay
- API access (future)

---

## 7. Compliance & Legal

### 7.1 Copyright Safety
- Display: "DATA VISUALIZATION ONLY" watermark
- No official league logos used
- No match footage/audio/play-by-play
- Minimum 30-second data delay
- All data from licensed API providers

### 7.2 Gambling Compliance
- Platform is analytics/visualization only
- No direct betting integration
- No financial advice claims
- Disclaimer: "For educational and entertainment purposes"

---

## 8. Success Metrics

### 8.1 Product KPIs
| Metric | Target (Month 1) | Target (Month 3) |
|--------|------------------|------------------|
| YouTube concurrent viewers | 50 | 500 |
| Pro subscribers | 10 | 100 |
| Elite subscribers | 2 | 20 |
| Model Brier Score | <0.25 | <0.20 |
| WebSocket uptime | 95% | 99% |
| Average session length | 20 min | 45 min |

### 8.2 Revenue Target
| Month | Free Users | Pro | Elite | MRR |
|-------|-----------|-----|-------|-----|
| Month 1 | 200 | 10 | 2 | $160 |
| Month 3 | 2000 | 100 | 20 | $1,600 |
| Month 6 | 10000 | 500 | 100 | $8,000 |

---

## 9. Roadmap Timeline

### Phase 1: Foundation (Done)
- React frontend + FastAPI backend
- Docker deployment
- Demo mode with simulated data
- XGBoost baseline model

### Phase 2: v1.1 Production (Current)
- Full JSON schema with 10 sections
- Real odds integration (The Odds API)
- SportMonks live data client (pending plan upgrade)
- Admin panel for match management
- Market Edge, Explain, Uncertainty engines

### Phase 3: Streaming Ready (Next 2 weeks)
- Event Alert System (visual + sound)
- Monte Carlo score matrix
- Pre-match / Post-match panels
- OBS integration and first test stream
- Real training data (football-data.co.uk CSVs)

### Phase 4: Growth (Month 2)
- AI Voice Commentary (TTS)
- Multi-match terminal
- Model track record display
- Chat voting system
- Membership payment integration

### Phase 5: Scale (Month 3+)
- Value Bet scanner
- Pressure flow visualization
- API SaaS offering
- Cloud deployment with CI/CD
- Multi-league coverage
