# AI Football Quant Terminal — TODO Checklist

> Last updated: 2026-02-28
> Current version: v2.2.0
> Status key: [x] Done | [ ] Todo | [~] Partial/In Progress

---

## Phase 0: Foundation (v1.0 Core) — COMPLETE

### Frontend Setup
- [x] React 18 + Vite project scaffold
- [x] QuantTerminal.jsx (5-layer UI: State/Probability/Trend/Stats/Quant)
- [x] WebSocket hook (useWebSocket.js)
- [x] i18n bilingual (EN/ZH)
- [x] Dark Bloomberg-style theme (IBM Plex Mono)
- [x] SVG Sparkline trend chart
- [x] Font loading: IBM Plex Mono + Noto Sans SC (Google Fonts) *(v1.2)*

### Backend Setup
- [x] FastAPI + WebSocket server
- [x] Redis cache layer
- [x] Connection manager (ws/manager.py)
- [x] Config with env vars (.env)
- [x] Health endpoint (/api/health)

### Model Training (Baseline)
- [x] Feature engineering (13 features: odds, Elo, stats, xG)
- [x] Simulated data generator (3000 matches)
- [x] Training pipeline (Logistic, XGBoost, Calibrated XGBoost)
- [x] Model serialization (joblib .pkl)
- [x] LivePredictor with Poisson in-match correction

### Deployment
- [x] Docker Compose (4 services: redis, backend, frontend, nginx)
- [x] Dockerfile.backend (Python 3.11-slim)
- [x] Dockerfile.frontend (Node 20-alpine build + nginx)
- [x] Nginx reverse proxy (/, /api/, /ws/)
- [x] Local deployment verified

---

## Phase 1: v1.1 Production — COMPLETE

### v1.1 Data Protocol
- [x] Unified JSON Schema (10 sections)
- [x] snake_case payload + frontend mapPayload.js mapper
- [x] Meta block: source, delay, health, seq numbering
- [x] Delta calculation on backend (per-match state)

### v1.1 WebSocket
- [x] Fibonacci backoff reconnect (3s -> 5s -> 8s -> 13s)
- [x] Single instance management (prevent multiple connections)
- [x] Health tracking from meta.health
- [x] Heartbeat ping/pong (15s interval) *(v1.2)*
- [ ] Service Worker / IndexedDB cache for recent events

### v1.1 New Components
- [x] EventTape.jsx (goals/cards/subs/VAR, newest first)
- [x] MarketEdge.jsx (odds, implied prob, edge AI-MKT)
- [x] ExplainPanel.jsx (Why Delta, top 3 factors with impact bars)
- [x] ReportBanner.jsx (HT/FT report notification)

### v1.1 Backend Engines
- [x] market_engine.py (implied probability + edge)
- [x] explain_engine.py (top factors driving delta)
- [x] uncertainty_engine.py (CI95, rolling Brier, sharpness, MC runs)
- [x] match_state.py (per-match state)
- [x] QuantEngine fallback (when ML model unavailable)

### v1.1 Admin System
- [x] Admin REST API (CRUD: add/list/toggle/delete matches)
- [x] Admin HTML panel (backend/static/admin.html)
- [x] Static file serving via FastAPI mount (/admin/)
- [x] Nginx proxy for /admin route

### v1.1 Data Sources
- [x] The Odds API client (real EPL odds flowing)
- [x] SportMonks API client (v3, ready for paid plan)
- [x] API-Football client (legacy, kept as fallback)
- [x] Real odds injection into demo mode
- [ ] API-Football/SportMonks paid plan activation for live EPL data
- [ ] Rate limiting / quota tracking for API calls

### v1.1 UI Enhancements
- [x] Meta status bar (DELAY/HEALTH/SOURCE)
- [x] Probability section with delta indicators
- [x] Market + Edge section (Pro tier)
- [x] Uncertainty section (Elite tier)
- [x] VOL SPIKE / GOAL WINDOW / DATA STALE alert badges *(v1.2)*
- [ ] Membership tier gating (blur/lock Pro/Elite content for Free users)

---

## Phase 1.5: v1.2 λ_live Engine — COMPLETE

### λ_live Total Goals O/U Engine
- [x] `total_goals_engine.py`: 9-stage formula (τ → Tempo → G → R → λ → Poisson → Market → Signal → Cooldown)
- [x] `TotalGoalsPanel.jsx`: Bloomberg-style O/U panel with Lambda/LINE/Edge/Signal
- [x] O/U totals market fetching in odds_client.py
- [x] Lambda trend tab in QuantTerminal (sparkline + summary)
- [x] MicroBars (Tempo/Pressure/Volatility)
- [x] Signal system: SIGNAL/STRONG/HIGH with cooldown countdown

### Real Data Training
- [x] Real match data: 23,533 matches (6 leagues × 10 seasons, football-data.co.uk)
- [x] Understat xG integration: 21,030 matches (5 leagues, 2014-2026)
- [x] 25-feature pipeline: Elo, xG, rolling form, avg odds
- [x] TimeSeriesSplit cross-validation (no data leakage)
- [x] Production model: LogReg 56.57% accuracy, 0.9048 LogLoss

### UI Polish
- [x] WebSocket heartbeat ping/pong (15s interval, 5s pong timeout)
- [x] Alert badges (VOL SPIKE / GOAL WINDOW / DATA STALE)
- [x] Font loading fix (preconnect + stylesheet)
- [x] Copyright watermark overlay
- [x] Data delay compliance flash (30s minimum)
- [x] Disclaimer bar: "DATA VISUALIZATION ONLY"

---

## Phase 2: v2.0 Streaming Fan Engagement — COMPLETE *(v2.0)*

### O/U Scanner (Multi-Line)
- [x] Scan multiple lines: 1.5/2.0/2.25/2.5/2.75/3.0/3.5 *(v2.0)*
- [x] Per-line Edge display with Active marker *(v2.0)*
- [x] Frontend `OUScanner.jsx` component *(v2.0)*
- [x] Backend: `scan_lines()` Poisson O/U for each line *(v2.0)*

### Goal Window System
- [x] High goal window detection (tempo_c≥1.15, λ_rate>0.029) *(v2.0)*
- [x] Countdown banner with estimated duration *(v2.0)*
- [x] Window Active timer display *(v2.0)*
- [x] Confidence percentage *(v2.0)*
- [x] Frontend `GoalWindow.jsx` + Backend `goal_window_engine.py` *(v2.0)*

### Signal Cooldown Display
- [x] Visible cooldown countdown timer (180s/120s) *(v2.0)*
- [x] "NEXT EVAL IN xx:xx" display *(v2.0)*
- [x] Signal state progression: MONITORING → BUILDING → READY → COOLDOWN *(v2.0)*
- [x] Edge building animation ("EDGE BUILDING...") *(v2.0)*

### Edge Heat Bar
- [x] Visual progress bar for Edge value *(v2.0)*
- [x] Color gradient: neutral → gold → bright gold *(v2.0)*
- [x] Threshold markers at 4%/6% *(v2.0)*

### Model Cycle Timer
- [x] "NEXT MODEL UPDATE 00:xx" countdown *(v2.0)*
- [x] Current State display: Monitoring / Evaluating / Recalculating *(v2.0)*
- [x] Volatility level indicator *(v2.0)*
- [x] Goal recalculation animation ("MODEL RESET — Recalculating λ...") *(v2.0)*

---

## Phase 3: v2.0 Market & Risk Transparency — COMPLETE *(v2.0)*

### Market Line Movement
- [x] Odds flow monitoring (line change tracking) *(v2.0)*
- [x] Over/Under odds change tracking *(v2.0)*
- [x] Market pressure indicator (OVER/UNDER/NEUTRAL direction) *(v2.0)*
- [x] Frontend `LineMovement.jsx` component *(v2.0)*

### Risk Panel
- [x] Model Variance display *(v2.0)*
- [x] Signal Stability percentage (10-sample rolling) *(v2.0)*
- [x] Market Volatility level (Low/Medium/High) *(v2.0)*
- [x] Max Drawdown Guard status *(v2.0)*
- [x] Frontend `RiskPanel.jsx` + Backend `risk_engine.py` *(v2.0)*

### Pre vs Live Comparison
- [x] PRE λ → LIVE λ with Δ percentage delta *(v2.3)*
- [x] TEMPO vs EXP 50 with Δ percentage *(v2.3)*
- [x] Integrated into TotalGoalsPanel header (compact 16px row) *(v2.3)*

### Market Pressure Index
- [x] Market pressure indicator in LineMovement *(v2.0)*
- [x] Direction: OVER / UNDER / NEUTRAL *(v2.0)*
- [x] Derived from odds movement direction *(v2.0)*

---

## Phase 4: v2.0 Signal Control & Track Record — COMPLETE *(v2.1)*

### Signal Control Panel (Semi-Automatic)
- [x] SIGNAL READY display with line/model/market/edge *(v2.1)*
- [x] [CONFIRM] / [REJECT] buttons (Enter/Escape keyboard shortcuts) *(v2.1)*
- [x] Signal state machine: idle → ready → confirmed → cooldown *(v2.1)*
- [x] Signal lock after confirmation (120s cooldown) *(v2.1)*
- [x] Trigger AI broadcast on confirm *(v2.2)*
- [x] Frontend `SignalControlPanel.jsx` component *(v2.1)*
- [x] Backend `POST /api/signal/confirm` + `GET /api/signal/state` *(v2.1)*

### Track Record / Performance Panel
- [x] Today's signals count, wins, losses *(v2.1)*
- [x] ROI percentage display *(v2.1)*
- [x] Signal log with result markers (✓/✗/●) *(v2.1)*
- [x] Corner display (always visible) *(v2.1)*
- [x] Frontend `TrackRecord.jsx` component *(v2.1)*
- [x] Backend `performance_tracker.py` + `GET /api/performance` *(v2.1)*

### Post-Match Summary
- [x] Auto-generated summary on match end (minute≥90) *(v2.1)*
- [x] Fields: Pre λ, Final Goals, Peak λ, Best Edge, λ Accuracy *(v2.1)*
- [x] POST-MATCH scene trigger *(v2.1)*
- [x] Export JSON with EXPORT JSON button (match_summary_YYYY-MM-DD_HH-MM.json) *(v2.3)*
- [x] Frontend `PostMatchSummary.jsx` component *(v2.1)*
- [x] Backend `post_match_engine.py` *(v2.1)*

---

## Phase 5: v2.0 AI Voice Commentary — COMPLETE *(v2.2)*

### TTS Engine Integration
- [x] Edge TTS (en-US-GuyNeural / zh-CN-YunxiNeural), -10% rate *(v2.2)*
- [x] Voice style: male, low-pitched, 0.9x speed *(v2.2)*
- [x] Bilingual templates (EN/ZH) — 10-stage scripts with 2 variants each *(v2.2)*
- [x] `POST /announce` endpoint — returns MP3 audio bytes *(v2.2)*

### Semi-Automatic Broadcast Flow
- [x] System detects edge ≥4% → SIGNAL PENDING (AI: "potential opportunity detected") *(v2.2)*
- [x] User confirms → SIGNAL CONFIRMED (AI: formal broadcast via Stage 5) *(v2.2)*
- [x] Goal → auto-broadcast (AI: "goal, recalculating...") — critical priority *(v2.2)*
- [x] Post-match → auto-summary broadcast (Stage 10, minute≥90) *(v2.2)*

### Trigger Rules & Cooldown
- [x] λ_total change > 8%: "significant model fluctuation" *(v2.2)*
- [x] Edge > 4%: "edge building" (SIGNAL_PENDING) *(v2.2)*
- [x] Edge > 6%: formal signal (SIGNAL_CONFIRM when confirmed) *(v2.2)*
- [x] Tempo > 70: "high tempo zone" *(v2.2)*
- [x] Goal / Red card: mandatory critical trigger *(v2.2)*
- [x] Max 1 non-critical broadcast per 90 seconds *(v2.2)*
- [x] 60s cooldown after goal, 30s after red card *(v2.2)*

### UI-Voice Sync
- [x] Panel highlight (0.8s glow) when AI speaks — `useVoiceHighlight.js` *(v2.2)*
- [x] "AI SPEAKING..." indicator (top-right) — `AISpeakingIndicator.jsx` *(v2.2)*
- [x] Late Game mode announcement (60min+) + Final Window (80min+) *(v2.2)*

### 10-Stage Script Templates
- [x] Stage 1: Pre-match opening *(v2.2)*
- [x] Stage 2: Kickoff monitoring *(v2.2)*
- [x] Stage 3: Tempo accumulation (15-35min) *(v2.2)*
- [x] Stage 4: Signal pending (suspense) *(v2.2)*
- [x] Stage 5: Signal confirm *(v2.2)*
- [x] Stage 6: Signal lock + cooldown *(v2.2)*
- [x] Stage 7: Goal trigger + recalc *(v2.2)*
- [x] Stage 8: Late game (60min+) *(v2.2)*
- [x] Stage 9: Final window (80min+) *(v2.2)*
- [x] Stage 10: Post-match summary *(v2.2)*

---

## Phase 6: v2.0 OBS Scene Integration — COMPLETE *(v2.3)*

### 4-Scene Structure
- [x] Scene 1: PRE-MATCH (kickoff countdown) *(v2.3)*
- [x] Scene 2: LIVE TRADING (main scene, 90% of time) *(v2.3)*
- [x] Scene 3: SIGNAL FOCUS (signal zoom, 5-10s on confirm) *(v2.3)*
- [x] Scene 4: POST-MATCH SUMMARY *(v2.3)*

### OBS Layer Structure
- [x] 6-layer structure documented (Background → Terminal → Signal → AI Status → Performance → Disclaimer) *(v2.3)*

### OBS Configuration
- [x] Hotkey mapping: F1=Signal, F2=Live, F3=Summary, F4=TTS *(v2.3)*
- [x] Output: 1080p 30fps, 6000kbps, Keyframe 2s *(v2.3)*
- [x] YouTube RTMPS streaming guide *(v2.3)*
- [x] Browser Source settings documented *(v2.3)*
- [x] `doc/OBS_SETUP.md` comprehensive setup guide *(v2.3)*

### Streaming Enhancements
- [x] System Online indicator (green pulsing dot + "SYSTEM ONLINE", red when disconnected) *(v2.3)*
- [x] Model version display ("MODEL v2.2") *(v2.3)*
- [x] Audio settings documented (TTS -3dB, ambient -28dB) *(v2.3)*

---

## Phase 7: Advanced Features — COMPLETE *(v2.3)*

### Event Alert System
- [x] Goal: Full-viewport gold flash 2.5s *(v2.1)*
- [x] Red card: Full-viewport red flash 2s *(v2.1)*
- [x] Probability swing > 15%: Full-viewport cyan flash 3s *(v2.1)*
- [x] `EventAlert.jsx` + `useEventAlert.js` hook with sequential queue *(v2.1)*
- [x] Web Audio API sound triggers (goal/red card/signal) via `useSoundEffects.js` *(v2.3)*

### Monte Carlo Score Matrix
- [x] Poisson-based correct score probability matrix (6×6, 0-5 goals) *(v2.3)*
- [x] Heat map visualization (opacity-scaled gold cells, gold glow on max) *(v2.3)*
- [x] Most Likely scores display (top 3) *(v2.3)*
- [x] Frontend `ScoreMatrix.jsx` + Backend `score_matrix_engine.py` *(v2.3)*

### Multi-Match Terminal
- [x] Responsive grid layout (auto-fill, 3-4 matches) *(v2.3)*
- [x] Per-match compact card (status dot, score, λ/edge/signal) *(v2.3)*
- [x] Frontend `MatchGrid.jsx` component (standalone, data-driven) *(v2.3)*
- [ ] WebSocket connection per match (backend multi-match support)

### Chat Voting System
- [x] Frontend `VotePanel.jsx` (1/X/2 bars, MODEL vs AUDIENCE, divergence highlight) *(v2.3)*
- [x] Model vs Audience comparison with >10% divergence badge *(v2.3)*
- [ ] YouTube Live Chat API reader (backend)
- [ ] TikTok/Douyin Live Connector (backend)
- [ ] Vote parsing (1/X/2) + real-time aggregation (backend)

### Sound Design
- [x] Goal: Bloomberg 3-note arpeggio (C5-E5-G5) *(v2.3)*
- [x] Red card: alarm double beep (400Hz square wave) *(v2.3)*
- [x] Probability swing: ascending frequency sweep (800→1600Hz) *(v2.3)*
- [x] Half-time: exchange closing bell (800Hz sine, 600ms) *(v2.3)*
- [x] Model recalculation: clean ding (1200Hz, 150ms) *(v2.3)*
- [x] Signal confirm: two-tone (E5-G5) *(v2.3)*
- [x] `useSoundEffects.js` Web Audio API hook — no external files *(v2.3)*

### Value Bet Scanner (EV)
- [x] Model vs Market edge detection with EV computation *(v2.3)*
- [x] Expected Value per $1 for OVER/UNDER *(v2.3)*
- [x] Confidence rating (LOW/MED/HIGH/STRONG) *(v2.3)*
- [x] Frontend `ValueBetScanner.jsx` + Backend `compute_value_bet()` *(v2.3)*

---

## Phase 8: Monetization & Operations

### Membership Tiers
- [ ] Free: 1X2 probability, basic stats, 3 events, trend
- [ ] Pro ($9.99/mo): Market/Edge, Explain, full events, Quant indicators
- [ ] Elite ($29.99/mo): Uncertainty, multi-match, report export, history replay
- [ ] Payment integration (Stripe / Paddle)
- [ ] Authentication system (JWT/session)
- [ ] Content blur/gate for locked tiers

### Cloud Deployment
- [ ] Cloud server setup (AWS/DO/Aliyun)
- [ ] SSL certificate (Let's Encrypt)
- [ ] Domain configuration
- [ ] CI/CD pipeline
- [ ] Monitoring & alerting

---

## Model Training Improvement

### Data Quality
- [x] Replace simulated data with real football-data.co.uk CSVs *(v1.2)*
- [x] Add La Liga, Bundesliga, Serie A, Ligue 1 data *(v1.2)*
- [x] Integrate Understat xG data for training *(v1.2)*
- [x] Feature: recent form (last 5 matches rolling stats) *(v1.2)*
- [ ] Feature: H2H historical record

### Model Architecture
- [x] Brier Score + LogLoss evaluation *(v1.2)*
- [ ] Calibration curve analysis
- [x] Feature importance analysis and selection *(v1.2)*
- [ ] Hyperparameter tuning (Optuna/GridSearch)
- [ ] Ensemble: XGBoost + LightGBM + Logistic weighted blend
- [x] Time-based cross-validation (no data leakage) *(v1.2)*

### Live Adjustment
- [x] Improved Poisson correction with λ_live engine *(v1.2)*
- [ ] In-match feature update (shots, possession, xG delta)
- [x] Red card impact model (R_c factor in total_goals_engine) *(v1.2)*
- [ ] Substitution impact tracking
- [ ] Weather / referee bias factors

### Continuous Learning
- [ ] Post-match result collection pipeline
- [ ] Weekly model retraining automation
- [ ] A/B model comparison framework
- [ ] Model version tracking (MLflow or simple JSON log)

---

## Tech Debt & Polish

- [x] Copyright compliance: "DATA VISUALIZATION ONLY" watermark *(v1.2)*
- [x] Data delay display (minimum 30s per compliance) *(v1.2)*
- [ ] Fix sklearn version mismatch warning
- [ ] Add comprehensive error handling for API failures
- [ ] Add logging (structured JSON logs)
- [ ] Unit tests for engines (market, explain, uncertainty, total_goals)
- [ ] Integration tests for WebSocket payload schema
- [ ] Frontend responsive layout (mobile-friendly)
- [ ] Accessibility (keyboard navigation, ARIA labels)
- [ ] API rate limit middleware
- [ ] Redis persistence configuration
