# AI Football Quant Terminal — CHANGELOG

> All notable changes to this project will be documented in this file.
> Format: [Semantic Versioning](https://semver.org/)

---

## [v2.0.0] — 2026-02-27

### Added — Streaming Fan Engagement (P0)
- **`OUScanner.jsx`**: Multi-line O/U scanner (1.5/2.0/2.25/2.5/2.75/3.0/3.5) with per-line Edge, active marker, mini bars
- **`GoalWindow.jsx`** + **`goal_window_engine.py`**: High goal window detection (tempo_c≥1.15, λ_rate>0.029), confidence %, countdown banner
- **`SignalCooldownBar.jsx`**: Signal state progression (MONITORING → BUILDING → READY → COOLDOWN) with visible countdown timer
- **`EdgeHeatBar.jsx`**: Visual Edge progress bar with color gradient (gray→gold→bright gold), threshold markers at 4%/6%
- **`ModelCycleTimer.jsx`**: Model evaluation countdown, state indicator (Monitoring/Evaluating/Recalculating), volatility level

### Added — Market & Risk Transparency (P1)
- **`LineMovement.jsx`**: Odds flow monitoring with line change tracking, market pressure direction (OVER/UNDER/NEUTRAL)
- **`RiskPanel.jsx`** + **`risk_engine.py`**: Model Variance, Signal Stability (10-sample), Market Volatility, Drawdown Guard
- Line movement tracking in DemoSimulator and live WebSocket loop

### Added — Backend Engines
- **`backend/services/goal_window_engine.py`**: GoalWindowEngine with 3-min deactivation delay, duration estimation brackets
- **`backend/services/risk_engine.py`**: RiskEngine with deque-based rolling history (10 snapshots), signal sign-change detection
- **`total_goals_engine.py`**: Added `scan_lines()` method for multi-line Poisson O/U (handles half/whole/quarter lines)

### Changed
- `QuantTerminal.jsx`: Integrated 7 new components, version bumped to v2.0
- `mapPayload.js`: Added scanner, goalWindow, risk, lineMovement mappers
- `i18n.js`: Added 8 new translation keys (EN/ZH)
- `main.py`: Integrated GoalWindowEngine, RiskEngine, line movement tracking in both demo and live modes

---

## [v1.2.0] — 2026-02-27

### Added — λ_live Total Goals O/U Engine
- **`backend/services/total_goals_engine.py`**: Full 9-stage λ_live engine
  - τ_nl = (r/90)^0.85 remaining time coefficient
  - Tempo factor: weighted geometric mean (xG 0.60, SOT 0.25, DA 0.15)
  - Game state G(d,t) = 1 + α·tanh(β·(-d))·s(t)
  - Red card factor R_c clipped [0.75, 1.25]
  - λ_total_live = goals_so_far + λ_rem_pre · Tempo_c · G · R_c
  - Poisson CDF for O/U probabilities
  - Market calibration η=0.25
  - Signal system: SIGNAL (≥4% edge), STRONG (≥6%), HIGH (≥8%)
  - Cooldown: 180s after goal, 120s after signal
- **`frontend/src/components/TotalGoalsPanel.jsx`**: Bloomberg-style O/U panel
  - Lambda Pre/Live/Market display
  - LINE (30px), probability bars, Edge, Signal indicator
  - MicroBar sub-component (Tempo/Pressure/Volatility)
  - `useCooldown` hook for client-side countdown
- **`frontend/src/utils/mapPayload.js`**: Added `totalGoals` field mapping
- **`frontend/src/utils/i18n.js`**: Added `lambdaTrend` key (EN/ZH)
- Lambda trend tab in QuantTerminal (sparkline + PRE/MARKET/LINE summary)
- O/U totals market fetching in `backend/data/odds_client.py`
- TotalGoalsEngine integrated in both demo and live modes in `main.py`

### Added — Real Data Training Pipeline
- **`backend/training/train_real.py`**: Production training on real match data
  - 23,533 matches across 6 leagues × 10 seasons (football-data.co.uk)
  - TimeSeriesSplit 5-fold cross-validation (no data leakage)
  - LogisticRegression: 56.57% accuracy, 0.9048 LogLoss, 0.1787 Brier
  - XGBoost: 55.93% accuracy, CalibratedXGBoost: 56.31% accuracy
- **`backend/training/features.py`**: Complete rewrite with 25 features
  - Elo ratings (K=20, home_adv=65)
  - xG integration via Understat (72.4% match rate)
  - Rolling 5-match form (points, goals scored/conceded)
  - Average odds across 4 bookmakers (B365, BW, PS, WH)
  - TEAM_NAME_MAP (~60 entries for cross-source matching)
- **`backend/training/download_understat_v2.py`**: Understat xG scraper
  - 21,030 matches across 5 leagues (2014-2026)
- **`backend/training/data/real/`**: 60 CSV files (EPL, La Liga, Bundesliga, Serie A, Ligue 1, Eredivisie)
- **`backend/training/data/understat/`**: xG data (all_leagues_xg.csv + per-league)

### Added — UI/UX Enhancements
- **Alert badges**: VOL SPIKE (amber), GOAL WINDOW (green), DATA STALE (red)
- **WebSocket heartbeat**: ping/pong 15s interval, 5s pong timeout, DEGRADED detection
- **Font loading**: Proper `<link>` tags for IBM Plex Mono + Noto Sans SC
- **Delay compliance**: Red flash animation when dataDelaySec < 30s
- **Disclaimer bar**: "DATA VISUALIZATION ONLY — NOT FINANCIAL ADVICE"
- **Copyright watermark**: Fixed-position overlay at bottom-right
- **Lambda trend chart**: Sparkline with PRE/MARKET/LINE summary in trend tabs

### Changed
- `backend/data/odds_client.py`: markets param `"h2h"` → `"h2h,totals"` for O/U odds
- `frontend/src/QuantTerminal.jsx`: Integrated TotalGoalsPanel, AlertBadge, delay flash, watermark
- `frontend/src/hooks/useWebSocket.js`: Added heartbeat mechanism with pong detection
- `frontend/index.html`: Added Google Fonts preconnect + stylesheet links
- Removed `@import url(...)` from globalCSS, added `@keyframes delayFlash`

---

## [v1.1.0] — 2026-02-26

### Added — Unified Data Protocol
- 10-section JSON Schema: meta/match/probability/market/stats/events/quant/uncertainty/explain/report
- snake_case backend payload + frontend `mapPayload.js` mapper
- Meta block: source, delay, health (OK/DEGRADED/STALE), sequence numbering
- Delta calculation on backend (per-match state tracking)

### Added — New Frontend Components
- **`EventTape.jsx`**: Goals/cards/subs/VAR event stream (newest first)
- **`MarketEdge.jsx`**: Odds, implied probability, Edge (AI - Market)
- **`ExplainPanel.jsx`**: Why Delta — top 3 factors with impact bars
- **`ReportBanner.jsx`**: HT/FT report notification banner

### Added — Backend Engines
- **`market_engine.py`**: Implied probability + edge computation (overround removal)
- **`explain_engine.py`**: Top factors driving probability delta
- **`uncertainty_engine.py`**: CI95, rolling Brier, sharpness, Monte Carlo runs
- **`match_state.py`**: Per-match state (last prob, event dedup, rolling Brier, seq)
- **QuantEngine fallback**: Heuristic engine when ML model unavailable

### Added — Admin System
- Admin REST API: CRUD (add/list/toggle/delete matches)
- Admin HTML panel (`backend/static/admin.html`)
- FastAPI static file serving at `/admin/`
- Nginx proxy for `/admin` route

### Added — Multi-Source Data Integration
- The Odds API client (real EPL odds flowing)
- SportMonks API client (v3, ready for paid plan)
- API-Football client (legacy, kept as fallback)
- Real odds injection into demo mode

### Added — UI Enhancements
- Meta status bar (DELAY / HEALTH / SOURCE)
- Probability section with delta indicators (▲/▼)
- Market + Edge section (Pro tier)
- Uncertainty section (Elite tier)

### Changed
- WebSocket reconnect: Fibonacci backoff (3s → 5s → 8s → 13s)
- Single WebSocket instance management (prevent duplicates)
- Health tracking from `meta.health` field

---

## [v1.0.0] — 2026-02-25

### Added — Core Platform
- **Frontend**: React 18 + Vite, 5-layer QuantTerminal UI
- **Backend**: FastAPI + WebSocket server with Redis cache
- **Model**: XGBoost multi-class → Calibrated XGBoost (simulated 3000 matches)
- **Live**: Poisson in-match correction (LivePredictor)
- **Deployment**: Docker Compose (4 services: redis, backend, frontend, nginx)

### Added — Frontend Features
- `QuantTerminal.jsx`: State/Probability/Trend/Stats/Quant layers
- `useWebSocket.js`: WebSocket hook with reconnect
- i18n bilingual support (EN/ZH)
- Dark Bloomberg-style theme (IBM Plex Mono)
- SVG Sparkline trend charts

### Added — Backend Features
- FastAPI WebSocket server with connection manager
- Redis cache layer for match data
- Config via environment variables (.env)
- Health endpoint (`/api/health`)
- Demo simulator with realistic match progression

### Added — Model Training
- 13-feature engineering pipeline (odds, Elo, stats, xG)
- Simulated data generator (3000 matches)
- Training pipeline: Logistic Regression, XGBoost, Calibrated XGBoost
- Model serialization via joblib (.pkl)

### Added — Deployment
- `docker-compose.yml` with 4 services
- `Dockerfile.backend` (Python 3.11-slim)
- `Dockerfile.frontend` (Node 20-alpine + nginx)
- Nginx reverse proxy (/, /api/, /ws/)

---

## [v2.0.0-plan] — Planned Features (from projectimprovev2.md)

### Priority 1 — Streaming Fan Engagement (Week 1-2)
- O/U Scanner: Multi-line scanning (2.0/2.25/2.5/2.75 with Edge)
- Goal Window countdown banner with estimated duration
- Signal Cooldown countdown (180s/120s visible timer)
- Edge Heat bar (visual bar instead of number only)
- Model Cycle / Next Evaluation countdown timer

### Priority 2 — Market & Risk Transparency (Week 2-3)
- Market Line Movement monitoring (odds flow, direction arrows)
- Risk Panel (Model Variance, Signal Stability, Market Volatility)
- Pre vs Live comparison (λ/Tempo delta percentage)
- Market Pressure indicator (OVER/UNDER direction)

### Priority 3 — Signal Control System (Week 3-4)
- Signal Control Panel (CONFIRM/REJECT for semi-automatic mode)
- Signal state machine: READY → PENDING → CONFIRMED → COOLDOWN
- Track Record / Performance panel (today's signals, wins, ROI)
- Post-Match Summary auto-generation

### Priority 4 — AI Voice Commentary (Month 2)
- Semi-automatic TTS (Edge TTS / OpenAI TTS / ElevenLabs)
- 10-stage broadcast rhythm script templates
- Trigger rules: λ change >8%, Edge >4%, Tempo >70, Goal, Red card
- Cooldown: 90s between non-critical broadcasts
- UI highlight sync when AI speaks

### Priority 5 — OBS Scene Integration (Month 2)
- 4 scenes: PRE-MATCH, LIVE TRADING, SIGNAL FOCUS, POST-MATCH
- Layer structure: Background → Terminal → Signal Overlay → AI Status → Performance → Disclaimer
- Hotkey mapping (F1-F4)
- Browser Source 1920x1080, 30fps, 6000kbps

### Priority 6 — Advanced Features (Month 3+)
- Multi-match grid terminal (3-4 matches)
- Chat voting system (YouTube/TikTok)
- Monte Carlo score matrix with heat map
- Sound design (Bloomberg-style audio cues)
- Membership tier gating (Free/Pro/Elite)
