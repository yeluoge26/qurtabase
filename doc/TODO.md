# AI Football Quant Terminal — TODO Checklist

> Last updated: 2026-02-27
> Current version: v1.2.0
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

## Phase 2: v2.0 Streaming Fan Engagement — P0 Must Have

### O/U Scanner (Multi-Line)
- [ ] Scan multiple lines: 2.0 / 2.25 / 2.5 / 2.75
- [ ] Per-line Edge display with Active marker
- [ ] Frontend `OUScanner.jsx` component
- [ ] Backend: compute Poisson O/U for each line

### Goal Window System
- [ ] High goal window detection (Tempo + xG velocity threshold)
- [ ] Countdown banner: "HIGH GOAL WINDOW — Estimated 5-10 min"
- [ ] Window Active timer display
- [ ] Confidence percentage
- [ ] Frontend `GoalWindow.jsx` component

### Signal Cooldown Display
- [ ] Visible cooldown countdown timer (180s/120s)
- [ ] "NEXT EVAL IN xx:xx" display
- [ ] Signal state progression: BUILDING → READY → CONFIRMED → COOLDOWN
- [ ] Edge building animation ("EDGE BUILDING...")

### Edge Heat Bar
- [ ] Visual progress bar for Edge value (not just number)
- [ ] Color gradient: neutral → gold → bright gold
- [ ] Threshold markers on bar

### Model Cycle Timer
- [ ] "NEXT MODEL UPDATE 00:xx" countdown
- [ ] Current State display: Monitoring / Evaluating / Recalculating
- [ ] Volatility level indicator
- [ ] Goal recalculation animation ("MODEL RESET — Recalculating λ...")

---

## Phase 3: v2.0 Market & Risk Transparency — P1

### Market Line Movement
- [ ] Odds flow monitoring (e.g. 2.5 → 2.25)
- [ ] Over/Under odds change tracking
- [ ] Market pressure indicator (OVER/UNDER direction arrows)
- [ ] Frontend `LineMovement.jsx` component

### Risk Panel
- [ ] Model Variance display
- [ ] Signal Stability percentage
- [ ] Market Volatility level (Low/Medium/High)
- [ ] Max Drawdown Guard status
- [ ] Frontend `RiskPanel.jsx` component

### Pre vs Live Comparison
- [ ] PRE TOTAL λ vs LIVE TOTAL λ with percentage delta
- [ ] TEMPO vs EXPECTED comparison
- [ ] Integrated into TotalGoalsPanel header

### Market Pressure Index
- [ ] PUBLIC BIAS / MARKET PRESSURE indicator
- [ ] Direction: OVER / UNDER / NEUTRAL
- [ ] Derived from odds movement direction

---

## Phase 4: v2.0 Signal Control & Track Record — P2

### Signal Control Panel (Semi-Automatic)
- [ ] SIGNAL READY display with line/model/market/edge
- [ ] [CONFIRM] / [REJECT] buttons (keyboard shortcut support)
- [ ] Signal state machine: ready → pending → confirmed → cooldown
- [ ] Signal lock after confirmation
- [ ] Trigger AI broadcast on confirm
- [ ] Frontend `SignalControlPanel.jsx` component
- [ ] Backend signal state endpoint

### Track Record / Performance Panel
- [ ] Today's signals count, wins, losses
- [ ] ROI percentage display
- [ ] Historical prediction database (match_id, predicted, actual)
- [ ] Corner display (always visible)
- [ ] Frontend `TrackRecord.jsx` component
- [ ] Backend `/api/performance` endpoint

### Post-Match Summary
- [ ] Auto-generated summary on match end
- [ ] Fields: Pre λ, Final Goals, Peak λ, Best Edge, Signal Accuracy
- [ ] POST-MATCH scene trigger
- [ ] Export capability (JSON / image snapshot)
- [ ] Frontend `PostMatchSummary.jsx` component

---

## Phase 5: v2.0 AI Voice Commentary — P3

### TTS Engine Integration
- [ ] Edge TTS / OpenAI TTS / ElevenLabs / CosyVoice support
- [ ] Voice style: male, low-pitched, 0.9x speed, slight room reverb
- [ ] Bilingual templates (EN/ZH)
- [ ] `POST /announce` endpoint for TTS trigger

### Semi-Automatic Broadcast Flow
- [ ] System detects edge → SIGNAL PENDING (AI: "potential opportunity detected")
- [ ] User confirms → SIGNAL CONFIRMED (AI: formal broadcast)
- [ ] Goal → auto-broadcast (AI: "goal, recalculating...")
- [ ] Post-match → auto-summary broadcast

### Trigger Rules & Cooldown
- [ ] λ_total change > 8%: "significant model fluctuation"
- [ ] Edge > 4%: "edge building"
- [ ] Edge > 6%: formal signal
- [ ] Tempo > 70: "high tempo zone"
- [ ] Goal / Red card: mandatory trigger
- [ ] Max 1 non-critical broadcast per 90 seconds
- [ ] 60s cooldown after goal

### UI-Voice Sync
- [ ] Panel highlight (0.8s glow) when AI speaks about that section
- [ ] "AI SPEAKING..." indicator (top-right)
- [ ] Late Game mode announcement (70min+)

### 10-Stage Script Templates
- [ ] Stage 1: Pre-match opening
- [ ] Stage 2: Kickoff monitoring
- [ ] Stage 3: Tempo accumulation (15-35min)
- [ ] Stage 4: Signal pending (suspense)
- [ ] Stage 5: Signal confirm
- [ ] Stage 6: Signal lock + cooldown
- [ ] Stage 7: Goal trigger + recalc
- [ ] Stage 8: Late game (60min+)
- [ ] Stage 9: Final window (80min+)
- [ ] Stage 10: Post-match summary

---

## Phase 6: v2.0 OBS Scene Integration — P4

### 4-Scene Structure
- [ ] Scene 1: PRE-MATCH (赛前预热, kickoff countdown)
- [ ] Scene 2: LIVE TRADING (主场景, 90% of time)
- [ ] Scene 3: SIGNAL FOCUS (信号放大, 5-10s on confirm)
- [ ] Scene 4: POST-MATCH SUMMARY (赛后总结)

### OBS Layer Structure
- [ ] Layer 1: Background (#0E1117 color source)
- [ ] Layer 2: Main terminal (Browser Source 1920x1080)
- [ ] Layer 3: Signal Overlay (separate browser source, 6s fade)
- [ ] Layer 4: AI voice status bar ("AI SPEAKING...")
- [ ] Layer 5: Today performance panel (fixed bottom-right)
- [ ] Layer 6: Disclaimer bar (fixed bottom 20px)

### OBS Configuration
- [ ] Hotkey mapping: F1=Signal, F2=Live, F3=Summary, F4=TTS
- [ ] Output: 1080p 30fps, 6000kbps, Keyframe 2s
- [ ] YouTube RTMPS streaming tested
- [ ] Browser Source: Shutdown when not visible, Refresh on scene active

### Streaming Enhancements
- [ ] System Online indicator (green dot, top-left)
- [ ] Model version display (e.g. "MODEL v2.3")
- [ ] Audio: TTS -3dB, ambient -28dB

---

## Phase 7: Advanced Features — P5 (Month 3+)

### Event Alert System
- [ ] Goal: State Bar flash yellow 2s
- [ ] Red card: State Bar flash red
- [ ] Probability swing > 15%: Full-screen ALERT banner
- [ ] OBS WebSocket notification for sound triggers

### Monte Carlo Score Matrix
- [ ] Poisson-based correct score probability matrix
- [ ] Heat map visualization (color-coded cells)
- [ ] Most Likely scores display (top 3)
- [ ] Frontend `ScoreMatrix.jsx` component

### Multi-Match Terminal
- [ ] Grid layout (3-4 matches side by side)
- [ ] Per-match compact card
- [ ] WebSocket connection per match
- [ ] Frontend `MatchGrid.jsx` component

### Chat Voting System
- [ ] YouTube Live Chat API reader
- [ ] TikTok/Douyin Live Connector
- [ ] Vote parsing (1/X/2) + real-time aggregation
- [ ] Model vs Audience comparison
- [ ] Frontend `VotePanel.jsx` component

### Sound Design
- [ ] Goal: Bloomberg trade execution sound
- [ ] Red card: alarm beep
- [ ] Probability swing > 15%: stock limit-up alert
- [ ] Half-time: exchange closing bell
- [ ] Model recalculation: clean "ding"

### Value Bet Scanner (EV)
- [ ] Model vs Market edge detection (threshold: +5%)
- [ ] Expected Value per $1
- [ ] Confidence rating (LOW/MED/HIGH/STRONG)

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
