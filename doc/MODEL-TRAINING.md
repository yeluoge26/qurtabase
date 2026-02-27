# Model Training Requirements & Next Steps

> Current state: Calibrated XGBoost trained on 3000 **simulated** matches
> Goal: Production model trained on **real historical data**

---

## Current Model Summary

| Item | Current | Issue |
|------|---------|-------|
| Training data | 3000 simulated matches | Fake — random distribution, no real patterns |
| Features | 13 (odds, Elo, stats, xG) | Correct features, but values are synthetic |
| CV Accuracy | ~47% (LR baseline) | Meaningless on fake data |
| Brier Score | Not tracked | Must add |
| Calibration | Not verified | Must add |
| sklearn version | 1.8.0 (local) vs 1.6.1 (Docker) | Causes unpickle warnings |

**Bottom line**: The model architecture and code are production-ready. The data is not.

---

## What You Need to Do

### Step 1: Download Real Training Data (10 minutes)

Download CSVs from [football-data.co.uk](https://www.football-data.co.uk/englandm.php):

```bash
mkdir -p backend/training/data/real

# EPL — last 10 seasons
for season in 2425 2324 2223 2122 2021 1920 1819 1718 1617 1516; do
  curl -o backend/training/data/real/epl_${season}.csv \
    "https://www.football-data.co.uk/mmz4281/${season}/E0.csv"
done

# Optional: Championship, La Liga, Bundesliga, Serie A, Ligue 1
# E1=Championship, SP1=LaLiga, D1=Bundesliga, I1=SerieA, F1=Ligue1
```

Each CSV contains (~380 rows/season for EPL):
- `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR` — match results
- `HS, AS, HST, AST, HC, AC` — shots, shots on target, corners
- `B365H, B365D, B365A` — Bet365 odds
- `BWH, BWD, BWA, PSH, PSD, PSA` — more bookmaker odds

**Expected total: ~3,800 EPL matches (10 seasons)**

### Step 2: Add Elo Ratings (30 minutes)

The simulated data had random Elo. Real Elo ratings need to be computed:

**Option A — Compute from results** (recommended):
```python
# Start all teams at 1500, update after each match
# K-factor = 20, home advantage = 65
# Code already exists in generate_data.py pattern
```

**Option B — Download pre-computed**:
- [clubelo.com](http://clubelo.com/) provides daily Elo for all major leagues
- [eloratings.net](https://www.eloratings.net/) for international

### Step 3: Add xG Data (Optional, 1 hour)

football-data.co.uk CSVs don't include xG. Options:

| Source | Method | Coverage |
|--------|--------|----------|
| [Understat](https://understat.com/) | Web scraping | EPL, La Liga, Bundesliga, Serie A, Ligue 1 (2014+) |
| [FBref](https://fbref.com/) | Web scraping | All major leagues (2017+) |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | Free JSON | Selected matches only |

If no xG: set `Home_xG = Away_xG = 0` and the model will rely on odds + Elo + stats features (still strong).

### Step 4: Retrain with Real Data (15 minutes)

Update `backend/training/train.py` to load real CSVs:

```python
import glob
import pandas as pd

# Load all real CSVs
files = glob.glob("data/real/epl_*.csv")
dfs = [pd.read_csv(f, encoding="latin-1") for f in files]
df = pd.concat(dfs, ignore_index=True)

# Ensure columns exist
required = ["B365H", "B365D", "B365A", "HS", "AS", "HST", "AST", "HC", "AC", "FTR"]
df = df.dropna(subset=required)

print(f"Training on {len(df)} real matches")
```

### Step 5: Fix sklearn Version Mismatch

The Docker image uses `scikit-learn==1.6.1` while local training used `1.8.0`. Fix:

**Option A** — Pin version in requirements.txt:
```
scikit-learn==1.8.0
```

**Option B** — Retrain inside Docker:
```bash
docker exec -it qurtabase-backend-1 python -c "
from training.train import *
# Will save models with matching sklearn version
"
```

### Step 6: Add Proper Evaluation Metrics

The current pipeline only reports accuracy. Must add:

```python
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.calibration import calibration_curve

# Brier Score (per-class, lower = better)
# For 3-class, compute per-class OVR Brier
for i, label in enumerate(["Away", "Draw", "Home"]):
    y_binary = (y_test == i).astype(int)
    brier = brier_score_loss(y_binary, y_proba[:, i])
    print(f"Brier ({label}): {brier:.4f}")

# Log Loss (overall, lower = better)
ll = log_loss(y_test, y_proba)
print(f"LogLoss: {ll:.4f}")

# Calibration curve
for i, label in enumerate(["Away", "Draw", "Home"]):
    y_binary = (y_test == i).astype(int)
    fraction_pos, mean_predicted = calibration_curve(
        y_binary, y_proba[:, i], n_bins=10
    )
    # Plot or log these values
```

**Target metrics on real data:**
| Metric | Baseline (odds-only) | Target (XGBoost) |
|--------|---------------------|-------------------|
| Accuracy | ~52% | >50% |
| Brier Score (avg) | ~0.20 | <0.22 |
| LogLoss | ~0.98 | <0.95 |
| Calibration error | <3% per bin | <5% per bin |

---

## Feature Engineering Improvements

### Current Features (13)
```
odds_implied_home, odds_implied_draw, odds_implied_away  (from B365 odds)
home_elo, away_elo                                        (Elo ratings)
home_shots, away_shots, home_sot, away_sot               (shot stats)
home_xg, away_xg                                          (expected goals)
home_corners, away_corners                                (corners)
```

### Recommended Additions
```
# Form features (rolling window of last 5 matches)
home_form_points_5      # Points earned in last 5 (W=3, D=1, L=0)
away_form_points_5
home_goals_scored_5     # Goals scored in last 5
home_goals_conceded_5
away_goals_scored_5
away_goals_conceded_5

# Head-to-head
h2h_home_wins_5        # Home team wins in last 5 H2H meetings
h2h_draws_5

# Market consensus (average multiple bookmakers)
avg_odds_home          # Average across Bet365, BetWay, Pinnacle
avg_odds_draw
avg_odds_away
odds_spread            # Max - Min odds (market disagreement)

# Contextual
is_derby               # Local derby flag (manual list)
days_since_last_match  # Fixture congestion
```

### Feature Importance Expected Ranking
1. **Odds-implied probabilities** (strongest predictor by far)
2. **Elo ratings difference**
3. **Recent form (5-match)**
4. **H2H record**
5. **xG stats** (if available)
6. **Shot stats**
7. **Corners** (weakest)

---

## Model Architecture Options

### Current: Single Calibrated XGBoost
- Works well as baseline
- CalibratedClassifierCV improves probability estimates

### Recommended: Ensemble
```python
from sklearn.ensemble import VotingClassifier
from lightgbm import LGBMClassifier

ensemble = VotingClassifier(
    estimators=[
        ("xgb", XGBClassifier(...)),
        ("lgbm", LGBMClassifier(...)),
        ("lr", LogisticRegression(multi_class="multinomial")),
    ],
    voting="soft",
    weights=[0.5, 0.3, 0.2],
)
```

### Future: Neural Network
- Only worthwhile with 10,000+ matches
- TabNet or simple MLP with dropout
- Unlikely to beat XGBoost on tabular data this small

---

## Cross-Validation Strategy

**Current**: Standard 5-fold CV (has data leakage — future matches can appear in training)

**Required**: Time-based split
```python
from sklearn.model_selection import TimeSeriesSplit

# Sort by date first!
df = df.sort_values("Date")

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    # Train and evaluate
```

This prevents the model from "seeing the future" during training.

---

## Continuous Learning Pipeline (Future)

```
Daily (post-match):
  1. Collect actual results for today's matches
  2. Compare with model predictions → update track record
  3. Store new match data in training set

Weekly:
  1. Retrain model on updated dataset
  2. Compare new model vs current (Brier, LogLoss)
  3. If improved: deploy new model (save .pkl)
  4. If worse: keep current model

Monthly:
  1. Feature importance review
  2. Add/remove features based on contribution
  3. Hyperparameter optimization (Optuna)
  4. Full evaluation report
```

---

## Quick Start: Retrain Now

```bash
cd backend/training

# 1. Download real data
mkdir -p data/real
for s in 2425 2324 2223 2122 2021 1920 1819 1718 1617 1516; do
  curl -o data/real/epl_${s}.csv \
    "https://www.football-data.co.uk/mmz4281/${s}/E0.csv"
done

# 2. Verify data
python -c "
import pandas as pd, glob
files = glob.glob('data/real/*.csv')
for f in files:
    df = pd.read_csv(f, encoding='latin-1')
    print(f'{f}: {len(df)} rows, cols: {list(df.columns[:10])}')
"

# 3. Update train.py to use real data (see Step 4 above)

# 4. Retrain
python train.py

# 5. Copy model to production
cp models/trained/model_calibrated.pkl ../../models/trained/

# 6. Rebuild Docker
cd ../..
docker compose up --build -d backend
```

---

## Summary: Priority Actions

| Priority | Action | Effort | Impact |
|----------|--------|--------|--------|
| **P0** | Download real EPL CSVs (10 seasons) | 10 min | Foundational |
| **P0** | Compute Elo ratings from results | 30 min | Key feature |
| **P0** | Retrain and evaluate (Brier + LogLoss) | 15 min | Baseline quality |
| **P1** | Add form features (rolling 5-match) | 1 hour | +2-3% accuracy |
| **P1** | Time-based cross-validation | 30 min | Correct evaluation |
| **P1** | Fix sklearn version mismatch | 5 min | Remove warnings |
| **P2** | Scrape xG from Understat/FBref | 2 hours | Marginal improvement |
| **P2** | Ensemble (XGBoost + LightGBM + LR) | 1 hour | +1-2% accuracy |
| **P3** | Continuous learning pipeline | 1 day | Long-term quality |
