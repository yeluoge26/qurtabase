# AI Football Quant Terminal — CHANGELOG

> All notable changes to this project will be documented in this file.
> Format: [Semantic Versioning](https://semver.org/)

---

## [v2.3.0] — 2026-02-28

### Added — OBS Scene Integration (P4)
- **`doc/OBS_SETUP.md`**: Comprehensive OBS Studio setup guide (4 scenes, 6 layers, hotkeys, output settings, YouTube RTMPS)
- **System Online indicator**: Green pulsing dot + "SYSTEM ONLINE" in header (red "OFFLINE" when disconnected)
- **Model version display**: "MODEL v2.2" in header bar

### Added — Advanced Features (P5)
- **`score_matrix_engine.py`** + **`ScoreMatrix.jsx`**: Poisson-based 6×6 correct score probability matrix with heat map visualization, top 3 most likely scores
- **`compute_value_bet()`** + **`ValueBetScanner.jsx`**: Expected Value scanner for O/U bets, EV% display, confidence rating (LOW/MED/HIGH/STRONG), pulsing VALUE badge
- **`useSoundEffects.js`**: Web Audio API Bloomberg-style sound effects — goal (C5-E5-G5 arpeggio), red card (400Hz alarm), prob swing (800→1600Hz sweep), half-time (closing bell), model ding, signal confirm
- **`MatchGrid.jsx`**: Multi-match grid terminal (responsive grid, compact cards with λ/edge/signal, standalone)
- **`VotePanel.jsx`**: Audience voting panel (1/X/2 bars, MODEL vs AUDIENCE comparison, >10% divergence badge, standalone)

### Added — Leftover Completions
- **Pre vs Live λ comparison**: Compact 16px row in TotalGoalsPanel header (PRE λ → LIVE λ Δ%, TEMPO vs EXP 50 Δ%)
- **Post-Match JSON Export**: EXPORT JSON button in PostMatchSummary (match_summary_YYYY-MM-DD_HH-MM.json)

### Changed
- `QuantTerminal.jsx`: Added System Online indicator, MODEL v2.2 label, ScoreMatrix, ValueBetScanner, useSoundEffects integration
- `TotalGoalsPanel.jsx`: Added Pre vs Live comparison strip
- `PostMatchSummary.jsx`: Added EXPORT JSON button with date-formatted filename
- `total_goals_engine.py`: Added `compute_value_bet()` method
- `main.py`: Integrated ScoreMatrixEngine in demo/live payloads
- `mapPayload.js`: Added scoreMatrix, valueBet mappers
- `i18n.js`: Added 11 new translation keys (EN/ZH)

---

## [v2.2.0] — 2026-02-28

### Added — AI Voice Commentary System (P3)
- **`tts_engine.py`**: Edge TTS integration (en-US-GuyNeural / zh-CN-YunxiNeural), -10% rate, async MP3 generation
- **`POST /announce`**: TTS endpoint — accepts text + lang, returns MP3 audio bytes
- **`broadcast_engine.py`**: 10-stage bilingual script templates (2 variants each), trigger rules engine with priority system
- **Trigger rules**: Goal/Red card (critical, mandatory), Edge ≥4% (SIGNAL_PENDING), Edge ≥6% (SIGNAL_CONFIRM), λ shift >8%, Tempo >70, Late Game (60min+), Final Window (80min+)
- **Cooldown system**: 90s global non-critical, 60s post-goal, 30s post-red-card; critical bypasses cooldown
- **`AISpeakingIndicator.jsx`**: Pulsing gold indicator with audio wave bars animation, "AI SPEAKING..." / "AI READY" status
- **`BroadcastBar.jsx`**: Ticker-style broadcast bar with stage badge (color-coded), cooldown countdown timer
- **`useVoiceHighlight.js`**: Panel highlight hook mapping broadcast stages to panel glow effects (0.8s fade)

### Changed
- `QuantTerminal.jsx`: Integrated AISpeakingIndicator (top-right), BroadcastBar (above footer), useVoiceHighlight
- `main.py`: Added BroadcastEngine + TTSEngine, broadcast state tracking, _compute_broadcast() in demo/live loops, signal confirm triggers Stage 5 broadcast, post-match triggers Stage 10
- `mapPayload.js`: Added broadcast mapper (text, stage, priority, speaking, cooldown_remaining)
- `i18n.js`: Added 8 new keys (EN/ZH) for AI speaking, broadcast stages
- `requirements.txt`: Added `edge-tts==6.1.19`

---

## [v2.1.0] — 2026-02-28

### Added — Signal Control & Track Record (P2)
- **`SignalControlPanel.jsx`**: Semi-automatic signal confirmation with CONFIRM/REJECT buttons, Enter/Escape keyboard shortcuts
- **Backend signal state machine**: idle → ready (edge≥4%) → confirmed (user CONFIRM) → cooldown (120s) → idle
- **`POST /api/signal/confirm`** + **`GET /api/signal/state`**: REST endpoints for signal control
- **`TrackRecord.jsx`** + **`performance_tracker.py`**: Today's signals/wins/losses/ROI, signal log with result markers (✓/✗/●)
- **`GET /api/performance`**: Performance summary endpoint with demo seed data
- **`PostMatchSummary.jsx`** + **`post_match_engine.py`**: Auto-generated post-match summary (Pre λ, Peak λ, Best Edge, λ Accuracy HIT/MISS)
- **`EventAlert.jsx`** + **`useEventAlert.js`**: Full-viewport flash alerts for goals (gold 2.5s), red cards (red 2s), prob swings >15% (cyan 3s)
- Sequential alert queue with event ID dedup, pointer-events: none overlay

### Changed
- `QuantTerminal.jsx`: Integrated 4 new T1 components (SignalControlPanel, TrackRecord, PostMatchSummary, EventAlert)
- `main.py`: Added signal state machine, PostMatchEngine, PerformanceTracker, 3 new REST endpoints
- `mapPayload.js`: Added signalControl, postMatch, performance mappers
- `i18n.js`: Added 14 new translation keys (EN/ZH) for signal/track/post-match/alert

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

