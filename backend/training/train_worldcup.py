"""
train_worldcup.py — World Cup Training Pipeline

Integrates World Cup and international football data into the existing
training pipeline. Computes international Elo ratings from 49K+ matches,
merges 2022 xG data, handles neutral venues, and trains models.

Data sources:
  - intl_results.csv (martj42): 49K international matches for Elo
  - matches.csv (Fjelstul): 1,248 World Cup matches (1930-2022)
  - FIFA-World-Cup-1930-2022-All-Match-Dataset.csv: 964 men's WC matches
  - Fifa_WC_2022_Match_data_xG.csv: 64 matches with xG stats

Run:
  cd backend
  python training/train_worldcup.py
"""

import os
import sys
import json
import time
import warnings

import pandas as pd
import numpy as np
from collections import defaultdict
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, log_loss, brier_score_loss,
    classification_report,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import joblib

warnings.filterwarnings("ignore")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import build_labels


# ---------------------------------------------------------------------------
# International Elo Rating System (neutral venue aware)
# ---------------------------------------------------------------------------
def compute_intl_elo(df: pd.DataFrame, k: float = 30, home_adv: float = 100,
                     initial_elo: float = 1500) -> dict:
    """
    Compute international Elo ratings from full match history.

    Uses larger K-factor (30) and home_adv (100) for international football
    where variance is higher. Neutral venues get home_adv=0.

    Returns dict of {team_name: current_elo}.
    """
    elo = defaultdict(lambda: initial_elo)

    for _, row in df.iterrows():
        ht = row["home_team"]
        at = row["away_team"]
        hs = row["home_score"]
        as_ = row["away_score"]
        neutral = row.get("neutral", False)

        h_elo = elo[ht]
        a_elo = elo[at]

        # Neutral venue: no home advantage
        adv = 0 if neutral else home_adv

        # Expected scores
        exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + adv)) / 400))
        exp_a = 1.0 - exp_h

        # Actual scores
        if hs > as_:
            actual_h, actual_a = 1.0, 0.0
        elif hs < as_:
            actual_h, actual_a = 0.0, 1.0
        else:
            actual_h, actual_a = 0.5, 0.5

        # Goal difference multiplier (FIFA-style)
        gd = abs(hs - as_)
        if gd <= 1:
            gd_mult = 1.0
        elif gd == 2:
            gd_mult = 1.5
        else:
            gd_mult = (11 + gd) / 8

        # Update Elo
        elo[ht] += k * gd_mult * (actual_h - exp_h)
        elo[at] += k * gd_mult * (actual_a - exp_a)

    return dict(elo)


def compute_intl_elo_with_history(intl_df: pd.DataFrame, wc_df: pd.DataFrame,
                                  k: float = 30, home_adv: float = 100,
                                  initial_elo: float = 1500) -> pd.DataFrame:
    """
    Compute Elo for each World Cup match using the full international history.

    Process all matches chronologically. For WC matches, record pre-match Elo.
    """
    elo = defaultdict(lambda: initial_elo)

    # Build a set of WC match keys for quick lookup
    wc_keys = set()
    wc_elo_map = {}  # (date, home, away) -> (home_elo, away_elo)

    for _, row in wc_df.iterrows():
        key = (str(row["Date_parsed"].date()), row["HomeTeam"], row["AwayTeam"])
        wc_keys.add(key)

    # Process ALL international matches chronologically
    for _, row in intl_df.iterrows():
        ht = row["home_team"]
        at = row["away_team"]
        hs = row["home_score"]
        as_ = row["away_score"]
        neutral = row.get("neutral", False)
        date_str = str(row["date"])

        h_elo = elo[ht]
        a_elo = elo[at]

        # Check if this is a WC match we care about
        key = (date_str, ht, at)
        if key in wc_keys:
            wc_elo_map[key] = (h_elo, a_elo)

        # Neutral venue: no home advantage
        adv = 0 if neutral else home_adv

        # Expected scores
        exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + adv)) / 400))
        exp_a = 1.0 - exp_h

        # Actual scores
        if hs > as_:
            actual_h, actual_a = 1.0, 0.0
        elif hs < as_:
            actual_h, actual_a = 0.0, 1.0
        else:
            actual_h, actual_a = 0.5, 0.5

        # Goal difference multiplier
        gd = abs(hs - as_)
        if gd <= 1:
            gd_mult = 1.0
        elif gd == 2:
            gd_mult = 1.5
        else:
            gd_mult = (11 + gd) / 8

        elo[ht] += k * gd_mult * (actual_h - exp_h)
        elo[at] += k * gd_mult * (actual_a - exp_a)

    # Map Elo back to WC dataframe
    home_elos = []
    away_elos = []
    for _, row in wc_df.iterrows():
        key = (str(row["Date_parsed"].date()), row["HomeTeam"], row["AwayTeam"])
        if key in wc_elo_map:
            h_e, a_e = wc_elo_map[key]
        else:
            # Fallback: use current team Elo (less accurate)
            h_e = elo.get(row["HomeTeam"], initial_elo)
            a_e = elo.get(row["AwayTeam"], initial_elo)
        home_elos.append(h_e)
        away_elos.append(a_e)

    wc_df = wc_df.copy()
    wc_df["HomeElo"] = home_elos
    wc_df["AwayElo"] = away_elos
    return wc_df


# ---------------------------------------------------------------------------
# World Cup Data Loading
# ---------------------------------------------------------------------------
# Team name normalization: intl_results.csv names -> football-data/Fjelstul names
INTL_TEAM_NORMALIZE = {
    "United States": "United States",
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "IR Iran": "Iran",
    "China PR": "China",
    "Côte d'Ivoire": "Ivory Coast",
    "Türkiye": "Turkey",
    "Czechia": "Czech Republic",
    "Eswatini": "Swaziland",
    "Congo DR": "DR Congo",
}

# Fjelstul matches.csv team names -> standard names
FJELSTUL_TEAM_NORMALIZE = {
    "United States": "United States",
    "Korea Republic": "South Korea",
    "Korea DPR": "North Korea",
    "Soviet Union": "Soviet Union",
    "Yugoslavia": "Yugoslavia",
    "West Germany": "West Germany",
    "East Germany": "East Germany",
    "Czechoslovakia": "Czechoslovakia",
    "Dutch East Indies": "Dutch East Indies",
    "FR Yugoslavia": "FR Yugoslavia",
    "Serbia and Montenegro": "Serbia and Montenegro",
}


def load_fjelstul_matches(fpath: str) -> pd.DataFrame:
    """Load Fjelstul matches.csv and convert to standard format."""
    df = pd.read_csv(fpath)

    # Filter men's WC only
    df = df[df["tournament_name"].str.contains("Men", na=False)].copy()

    # Parse dates
    df["Date_parsed"] = pd.to_datetime(df["match_date"])

    # Standardize columns
    df["HomeTeam"] = df["home_team_name"].map(
        lambda x: FJELSTUL_TEAM_NORMALIZE.get(x, x)
    )
    df["AwayTeam"] = df["away_team_name"].map(
        lambda x: FJELSTUL_TEAM_NORMALIZE.get(x, x)
    )
    df["FTHG"] = pd.to_numeric(df["home_team_score"], errors="coerce")
    df["FTAG"] = pd.to_numeric(df["away_team_score"], errors="coerce")

    # Result
    df["FTR"] = df.apply(
        lambda r: "H" if r["FTHG"] > r["FTAG"]
        else ("A" if r["FTHG"] < r["FTAG"] else "D"),
        axis=1,
    )

    # World Cup matches are mostly neutral venue (except host nation)
    df["neutral"] = True
    df["is_knockout"] = df["knockout_stage"].astype(bool)
    df["stage"] = df["stage_name"]
    df["tournament"] = "FIFA World Cup"
    df["Div"] = "WC"

    # Drop invalid rows
    df = df.dropna(subset=["FTHG", "FTAG", "Date_parsed"])

    return df.sort_values("Date_parsed").reset_index(drop=True)


def load_intl_results(fpath: str) -> pd.DataFrame:
    """Load martj42 international results for Elo computation."""
    df = pd.read_csv(fpath)
    df["date"] = pd.to_datetime(df["date"])
    df["home_score"] = pd.to_numeric(df["home_score"], errors="coerce")
    df["away_score"] = pd.to_numeric(df["away_score"], errors="coerce")

    # Normalize neutral venue flag
    if "neutral" in df.columns:
        df["neutral"] = df["neutral"].astype(str).str.upper().isin(["TRUE", "1", "YES"])

    # Normalize team names
    df["home_team"] = df["home_team"].map(
        lambda x: INTL_TEAM_NORMALIZE.get(x, x)
    )
    df["away_team"] = df["away_team"].map(
        lambda x: INTL_TEAM_NORMALIZE.get(x, x)
    )

    df = df.dropna(subset=["home_score", "away_score"])
    df = df.sort_values("date").reset_index(drop=True)

    return df


def load_wc_2022_xg(fpath: str) -> dict:
    """Load 2022 WC xG data. Returns dict of (date, team1, team2) -> (xg1, xg2)."""
    if not os.path.exists(fpath):
        return {}

    # Try multiple encodings
    for enc in ["utf-8", "latin-1", "cp1252"]:
        try:
            df = pd.read_csv(fpath, encoding=enc)
            break
        except (UnicodeDecodeError, Exception):
            continue
    else:
        return {}

    xg_map = {}

    for _, row in df.iterrows():
        try:
            # Parse date (format: 20-Nov-22 or similar)
            date = pd.to_datetime(row["date"], dayfirst=True)
            t1 = str(row["1"]).strip().upper()
            t2 = str(row["2"]).strip().upper()
            xg1 = float(row["1_xg"])
            xg2 = float(row["2_xg"])
            xg_map[(date.date(), t1, t2)] = (xg1, xg2)
        except Exception:
            continue

    return xg_map


# WC 2022 team name mapping (xG CSV uses uppercase abbreviations)
WC2022_TEAM_MAP = {
    "QATAR": "Qatar", "ECUADOR": "Ecuador", "ENGLAND": "England",
    "IRAN": "Iran", "SENEGAL": "Senegal", "NETHERLANDS": "Netherlands",
    "USA": "United States", "WALES": "Wales", "ARGENTINA": "Argentina",
    "SAUDI ARABIA": "Saudi Arabia", "DENMARK": "Denmark", "TUNISIA": "Tunisia",
    "MEXICO": "Mexico", "POLAND": "Poland", "FRANCE": "France",
    "AUSTRALIA": "Australia", "MOROCCO": "Morocco", "CROATIA": "Croatia",
    "GERMANY": "Germany", "JAPAN": "Japan", "SPAIN": "Spain",
    "COSTA RICA": "Costa Rica", "BELGIUM": "Belgium", "CANADA": "Canada",
    "SWITZERLAND": "Switzerland", "CAMEROON": "Cameroon",
    "URUGUAY": "Uruguay", "SOUTH KOREA": "South Korea",
    "PORTUGAL": "Portugal", "GHANA": "Ghana", "BRAZIL": "Brazil",
    "SERBIA": "Serbia",
}


def merge_wc_xg(wc_df: pd.DataFrame, xg_map: dict) -> pd.DataFrame:
    """Merge 2022 xG data into WC dataframe."""
    wc_df = wc_df.copy()
    home_xg = []
    away_xg = []

    for _, row in wc_df.iterrows():
        date = row["Date_parsed"].date()
        ht = row["HomeTeam"].upper()
        at = row["AwayTeam"].upper()

        # Try direct match
        found = False
        for (d, t1, t2), (x1, x2) in xg_map.items():
            if d == date:
                # Map team names
                t1_std = WC2022_TEAM_MAP.get(t1, t1).upper()
                t2_std = WC2022_TEAM_MAP.get(t2, t2).upper()
                if (ht == t1_std and at == t2_std):
                    home_xg.append(x1)
                    away_xg.append(x2)
                    found = True
                    break
                elif (ht == t2_std and at == t1_std):
                    home_xg.append(x2)
                    away_xg.append(x1)
                    found = True
                    break

        if not found:
            home_xg.append(0.0)
            away_xg.append(0.0)

    wc_df["Home_xG"] = home_xg
    wc_df["Away_xG"] = away_xg
    return wc_df


# ---------------------------------------------------------------------------
# Rolling Form (International — uses full intl history)
# ---------------------------------------------------------------------------
def compute_intl_rolling_form(wc_df: pd.DataFrame, intl_df: pd.DataFrame,
                              window: int = 10) -> pd.DataFrame:
    """
    Compute rolling form for WC teams from their full international history.
    Uses window=10 (more matches for international to compensate for gaps).
    """
    # Build team history from all international matches
    team_points = defaultdict(list)
    team_goals_scored = defaultdict(list)
    team_goals_conceded = defaultdict(list)
    team_dates = defaultdict(list)

    for _, row in intl_df.iterrows():
        ht = row["home_team"]
        at = row["away_team"]
        hs = int(row["home_score"])
        as_ = int(row["away_score"])
        date = row["date"]

        if hs > as_:
            team_points[ht].append((date, 3))
            team_points[at].append((date, 0))
        elif hs < as_:
            team_points[ht].append((date, 0))
            team_points[at].append((date, 3))
        else:
            team_points[ht].append((date, 1))
            team_points[at].append((date, 1))

        team_goals_scored[ht].append((date, hs))
        team_goals_scored[at].append((date, as_))
        team_goals_conceded[ht].append((date, as_))
        team_goals_conceded[at].append((date, hs))

    # For each WC match, look up form BEFORE match date
    wc_df = wc_df.copy()
    home_form = []
    away_form = []
    home_gs = []
    away_gs = []
    home_gc = []
    away_gc = []

    for _, row in wc_df.iterrows():
        match_date = row["Date_parsed"]
        ht = row["HomeTeam"]
        at = row["AwayTeam"]

        # Home team form
        h_pts = [p for d, p in team_points.get(ht, []) if d < match_date]
        a_pts = [p for d, p in team_points.get(at, []) if d < match_date]

        home_form.append(np.mean(h_pts[-window:]) if h_pts else 1.5)
        away_form.append(np.mean(a_pts[-window:]) if a_pts else 1.5)

        h_g = [g for d, g in team_goals_scored.get(ht, []) if d < match_date]
        a_g = [g for d, g in team_goals_scored.get(at, []) if d < match_date]
        home_gs.append(np.mean(h_g[-window:]) if h_g else 1.3)
        away_gs.append(np.mean(a_g[-window:]) if a_g else 1.3)

        h_c = [g for d, g in team_goals_conceded.get(ht, []) if d < match_date]
        a_c = [g for d, g in team_goals_conceded.get(at, []) if d < match_date]
        home_gc.append(np.mean(h_c[-window:]) if h_c else 1.3)
        away_gc.append(np.mean(a_c[-window:]) if a_c else 1.3)

    wc_df["home_form_pts"] = home_form
    wc_df["away_form_pts"] = away_form
    wc_df["home_goals_scored_roll"] = home_gs
    wc_df["away_goals_scored_roll"] = away_gs
    wc_df["home_goals_conceded_roll"] = home_gc
    wc_df["away_goals_conceded_roll"] = away_gc

    return wc_df


# ---------------------------------------------------------------------------
# World Cup Feature Builder
# ---------------------------------------------------------------------------
def build_wc_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build features for World Cup matches (no betting odds available)."""
    feats = pd.DataFrame(index=df.index)

    # 1. Elo ratings (primary signal — replaces odds)
    if {"HomeElo", "AwayElo"}.issubset(df.columns):
        feats["elo_diff"] = df["HomeElo"] - df["AwayElo"]
        feats["elo_diff_norm"] = feats["elo_diff"] / 400
        feats["home_elo_norm"] = df["HomeElo"] / 2000
        feats["away_elo_norm"] = df["AwayElo"] / 2000

        # Elo-implied probability (substitute for odds)
        feats["elo_home_prob"] = 1.0 / (1.0 + 10 ** (-feats["elo_diff"] / 400))
        feats["elo_away_prob"] = 1.0 - feats["elo_home_prob"]
        # Elo draw estimate: decreases for mismatches, increases for close matchups
        feats["elo_draw_est"] = 1.0 - abs(feats["elo_home_prob"] - 0.5) * 2

    # 2. Home advantage (neutral flag — most WC matches are neutral)
    if "neutral" in df.columns:
        is_home = (~df["neutral"].astype(bool)).astype(float)
        if is_home.std() > 0:  # only include if non-constant
            feats["is_home"] = is_home

    # 3. xG features
    if {"Home_xG", "Away_xG"}.issubset(df.columns):
        feats["xg_diff"] = df["Home_xG"] - df["Away_xG"]
        feats["xg_total"] = df["Home_xG"] + df["Away_xG"]
        feats["home_xg"] = df["Home_xG"]
        feats["away_xg"] = df["Away_xG"]

    # 4. Rolling form
    if "home_form_pts" in df.columns:
        feats["home_form"] = df["home_form_pts"]
        feats["away_form"] = df["away_form_pts"]
        feats["form_diff"] = df["home_form_pts"] - df["away_form_pts"]
        feats["home_attack"] = df["home_goals_scored_roll"]
        feats["away_attack"] = df["away_goals_scored_roll"]
        feats["home_defense"] = df["home_goals_conceded_roll"]
        feats["away_defense"] = df["away_goals_conceded_roll"]
        feats["attack_diff"] = df["home_goals_scored_roll"] - df["away_goals_scored_roll"]
        feats["defense_diff"] = df["home_goals_conceded_roll"] - df["away_goals_conceded_roll"]

    # 5. Tournament stage features
    if "is_knockout" in df.columns:
        feats["is_knockout"] = df["is_knockout"].astype(float)

    return feats


# ---------------------------------------------------------------------------
# Evaluation (same as train_real.py)
# ---------------------------------------------------------------------------
def evaluate_timeseries(name, model, X, y, dates, n_splits=5):
    """Evaluate with time-series CV. Handles small fold sizes gracefully."""
    import copy

    print(f"\n{'='*65}")
    print(f"  Model: {name}")
    print(f"{'='*65}")

    tscv = TimeSeriesSplit(n_splits=n_splits)

    fold_acc, fold_ll = [], []
    fold_brier_h, fold_brier_d, fold_brier_a = [], [], []

    for fold_idx, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        # Check minimum class count for CalibratedClassifierCV
        try:
            model.fit(X_train, y_train)
        except ValueError as e:
            if "less than" in str(e) and "examples" in str(e):
                print(f"  Fold {fold_idx+1}: SKIPPED (insufficient class examples in train)")
                continue
            raise

        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        acc = accuracy_score(y_test, y_pred)
        ll = log_loss(y_test, y_proba, labels=[0, 1, 2])

        bs_a = brier_score_loss((y_test == 0).astype(int), y_proba[:, 0])
        bs_d = brier_score_loss((y_test == 1).astype(int), y_proba[:, 1])
        bs_h = brier_score_loss((y_test == 2).astype(int), y_proba[:, 2])

        fold_acc.append(acc)
        fold_ll.append(ll)
        fold_brier_h.append(bs_h)
        fold_brier_d.append(bs_d)
        fold_brier_a.append(bs_a)

        date_range = f"{dates[test_idx[0]].strftime('%Y-%m')} to {dates[test_idx[-1]].strftime('%Y-%m')}"
        print(f"  Fold {fold_idx+1}: Acc={acc:.4f}  LogLoss={ll:.4f}  "
              f"Brier(H/D/A)={bs_h:.4f}/{bs_d:.4f}/{bs_a:.4f}  "
              f"[{date_range}, n={len(test_idx)}]")

    if not fold_acc:
        print(f"\n  WARNING: No valid folds — returning untrained model")
        model.fit(X, y)
        return model, {"mean_accuracy": 0, "std_accuracy": 0, "mean_logloss": 0,
                        "mean_brier_home": 0, "mean_brier_draw": 0, "mean_brier_away": 0}

    print(f"\n  Mean Accuracy:    {np.mean(fold_acc):.4f} +/- {np.std(fold_acc):.4f}")
    print(f"  Mean Log Loss:    {np.mean(fold_ll):.4f} +/- {np.std(fold_ll):.4f}")
    print(f"  Mean Brier (avg): {np.mean(fold_brier_h + fold_brier_d + fold_brier_a):.4f}")

    # Train on all data
    print(f"\n  Training final model on all {len(X)} samples...")
    model.fit(X, y)

    results = {
        "mean_accuracy": float(np.mean(fold_acc)),
        "std_accuracy": float(np.std(fold_acc)),
        "mean_logloss": float(np.mean(fold_ll)),
        "mean_brier_home": float(np.mean(fold_brier_h)),
        "mean_brier_draw": float(np.mean(fold_brier_d)),
        "mean_brier_away": float(np.mean(fold_brier_a)),
    }
    return model, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t_start = time.time()

    print("=" * 65)
    print("  World Cup — Training Pipeline")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(base_dir)
    wc_data_dir = os.path.join(base_dir, "data", "worldcup")
    models_dir = os.path.join(backend_dir, "models", "trained")

    # 1. Load international results for Elo computation
    print(f"\n[1/6] Loading international results for Elo history...")
    intl_path = os.path.join(wc_data_dir, "intl_results.csv")
    intl_df = load_intl_results(intl_path)
    print(f"  Loaded {len(intl_df)} international matches")
    print(f"  Date range: {intl_df['date'].min()} to {intl_df['date'].max()}")

    # Filter World Cup matches from intl_results
    wc_intl = intl_df[intl_df["tournament"] == "FIFA World Cup"].copy()
    print(f"  World Cup matches in intl_results: {len(wc_intl)}")

    # 2. Load Fjelstul WC matches (richer metadata)
    print(f"\n[2/6] Loading Fjelstul World Cup matches...")
    fjelstul_path = os.path.join(wc_data_dir, "matches.csv")
    wc_df = load_fjelstul_matches(fjelstul_path)
    print(f"  Loaded {len(wc_df)} men's World Cup matches")
    print(f"  Date range: {wc_df['Date_parsed'].min()} to {wc_df['Date_parsed'].max()}")
    print(f"  Tournaments: {wc_df['Date_parsed'].dt.year.unique()}")

    # Result distribution
    n_total = len(wc_df)
    n_h = (wc_df["FTR"] == "H").sum()
    n_d = (wc_df["FTR"] == "D").sum()
    n_a = (wc_df["FTR"] == "A").sum()
    print(f"  Results: H={n_h} ({n_h/n_total*100:.1f}%)  "
          f"D={n_d} ({n_d/n_total*100:.1f}%)  "
          f"A={n_a} ({n_a/n_total*100:.1f}%)")

    # 3. Compute Elo from full international history
    print(f"\n[3/6] Computing international Elo ratings (K=30, home_adv=100)...")
    print(f"  Processing {len(intl_df)} international matches for Elo...")
    wc_df = compute_intl_elo_with_history(intl_df, wc_df, k=30, home_adv=100)
    print(f"  Elo range in WC: {wc_df['HomeElo'].min():.0f} to {wc_df['HomeElo'].max():.0f}")

    # Show some notable Elo ratings
    print(f"\n  Recent WC matches with Elo:")
    for _, row in wc_df.tail(10).iterrows():
        print(f"    {row['Date_parsed'].strftime('%Y-%m-%d')} "
              f"{row['HomeTeam']:20s} ({row['HomeElo']:.0f}) vs "
              f"{row['AwayTeam']:20s} ({row['AwayElo']:.0f})  "
              f"-> {row['FTR']} ({int(row['FTHG'])}-{int(row['FTAG'])})")

    # 4. Load and merge 2022 xG data
    print(f"\n[4/6] Loading 2022 World Cup xG data...")
    xg_path = os.path.join(wc_data_dir, "Fifa_WC_2022_Match_data_xG.csv")
    xg_map = load_wc_2022_xg(xg_path)
    print(f"  2022 xG records: {len(xg_map)}")
    wc_df = merge_wc_xg(wc_df, xg_map)
    n_xg = (wc_df["Home_xG"] > 0).sum()
    print(f"  Matches with xG: {n_xg}/{len(wc_df)}")

    # 5. Compute rolling form from international history
    print(f"\n[5/6] Computing rolling form features (window=10)...")
    wc_df = compute_intl_rolling_form(wc_df, intl_df, window=10)

    # 6. Build features
    print(f"\n[6/6] Building feature matrix...")
    X_df = build_wc_features(wc_df)
    y = build_labels(wc_df)

    # Drop NaN rows
    mask = X_df.notna().all(axis=1)
    n_dropped = (~mask).sum()
    X_df = X_df[mask]
    y = y[mask.values]
    dates = wc_df.loc[mask, "Date_parsed"].values

    X = X_df.values.astype(np.float64)
    feature_names = list(X_df.columns)

    print(f"  Features ({len(feature_names)}): {feature_names}")
    print(f"  Valid samples: {len(X)} (dropped {n_dropped} with NaN)")
    print(f"  Feature matrix shape: {X.shape}")

    # Feature stats
    print(f"\n  Feature statistics:")
    for i, fname in enumerate(feature_names):
        vals = X[:, i]
        print(f"    {fname:30s}  mean={np.mean(vals):8.4f}  "
              f"std={np.std(vals):8.4f}")

    dates_dt = pd.to_datetime(dates)

    # -----------------------------------------------------------------------
    # Train models
    # -----------------------------------------------------------------------
    print(f"\n\n{'#'*65}")
    print(f"  TRAINING WORLD CUP MODELS (TimeSeriesSplit, 5 folds)")
    print(f"{'#'*65}")

    all_results = {}

    # Model 1: Logistic Regression
    model_lr = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs")),
    ])
    model_lr, res_lr = evaluate_timeseries(
        "Logistic Regression", model_lr, X, y, dates_dt
    )
    all_results["logistic"] = res_lr

    # Model 2: XGBoost
    model_xgb = XGBClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=0.2,
        reg_alpha=0.1,
        reg_lambda=1.5,
        eval_metric="mlogloss",
        random_state=42,
        verbosity=0,
        n_jobs=-1,
    )
    model_xgb, res_xgb = evaluate_timeseries(
        "XGBoost", model_xgb, X, y, dates_dt
    )
    all_results["xgboost"] = res_xgb

    # Model 3: Calibrated XGBoost
    base_cal = XGBClassifier(
        n_estimators=300,
        max_depth=3,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=5,
        gamma=0.2,
        reg_alpha=0.1,
        reg_lambda=1.5,
        eval_metric="mlogloss",
        random_state=42,
        verbosity=0,
        n_jobs=-1,
    )
    model_cal = CalibratedClassifierCV(base_cal, cv=3, method="sigmoid")
    model_cal, res_cal = evaluate_timeseries(
        "XGBoost + Calibration", model_cal, X, y, dates_dt
    )
    all_results["calibrated"] = res_cal

    # -----------------------------------------------------------------------
    # Feature Importance
    # -----------------------------------------------------------------------
    if hasattr(model_xgb, "feature_importances_"):
        print(f"\n\n{'='*65}")
        print(f"  Feature Importance (XGBoost)")
        print(f"{'='*65}\n")
        importances = model_xgb.feature_importances_
        pairs = sorted(zip(feature_names, importances), key=lambda x: -x[1])
        max_imp = max(importances) if max(importances) > 0 else 1
        for rank, (name, imp) in enumerate(pairs, 1):
            bar = "#" * int(imp / max_imp * 40)
            print(f"  {rank:2d}. {name:30s}  {imp:.4f}  {bar}")

    # -----------------------------------------------------------------------
    # Summary
    # -----------------------------------------------------------------------
    print(f"\n\n{'='*65}")
    print(f"  WORLD CUP MODEL COMPARISON SUMMARY")
    print(f"{'='*65}\n")
    print(f"  {'Model':<35s}  {'Accuracy':>8s}  {'LogLoss':>8s}  {'Brier(avg)':>10s}")
    print(f"  {'-'*35}  {'-'*8}  {'-'*8}  {'-'*10}")
    for mname, res in all_results.items():
        avg_brier = (res["mean_brier_home"] + res["mean_brier_draw"] + res["mean_brier_away"]) / 3
        print(f"  {mname:<35s}  {res['mean_accuracy']:>8.4f}  "
              f"{res['mean_logloss']:>8.4f}  {avg_brier:>10.4f}")

    # -----------------------------------------------------------------------
    # Save models
    # -----------------------------------------------------------------------
    os.makedirs(models_dir, exist_ok=True)
    print(f"\n\nSaving World Cup models to {models_dir}...")

    joblib.dump(model_xgb, os.path.join(models_dir, "model_wc_xgb.pkl"))
    print(f"  model_wc_xgb.pkl")

    joblib.dump(model_cal, os.path.join(models_dir, "model_wc_calibrated.pkl"))
    print(f"  model_wc_calibrated.pkl")

    joblib.dump(model_lr, os.path.join(models_dir, "model_wc_logistic.pkl"))
    print(f"  model_wc_logistic.pkl")

    # Save metadata
    meta = {
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "n_classes": 3,
        "class_names": ["Away", "Draw", "Home"],
        "class_mapping": {"A": 0, "D": 1, "H": 2},
        "training_data": {
            "n_wc_matches": len(X),
            "n_intl_matches_for_elo": len(intl_df),
            "date_range": [str(dates_dt.min()), str(dates_dt.max())],
            "source": "FIFA World Cup 1930-2022 + 49K intl Elo",
        },
        "evaluation": all_results,
    }
    meta_path = os.path.join(models_dir, "model_wc_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  model_wc_meta.json")

    # -----------------------------------------------------------------------
    # Inference test
    # -----------------------------------------------------------------------
    print(f"\n\nInference test (last WC match):")
    test_sample = X[-1:]
    proba = model_cal.predict_proba(test_sample)[0]
    last_row = wc_df.iloc[-1]
    print(f"  Match: {last_row['HomeTeam']} vs {last_row['AwayTeam']} "
          f"({last_row['Date_parsed'].strftime('%Y-%m-%d')})")
    print(f"  Actual result: {last_row['FTR']} ({int(last_row['FTHG'])}-{int(last_row['FTAG'])})")
    print(f"  Predicted: A={proba[0]*100:.1f}% | D={proba[1]*100:.1f}% | H={proba[2]*100:.1f}%")
    print(f"  Elo: {last_row['HomeTeam']} ({last_row['HomeElo']:.0f}) vs "
          f"{last_row['AwayTeam']} ({last_row['AwayElo']:.0f})")

    elapsed = time.time() - t_start
    print(f"\n{'='*65}")
    print(f"  World Cup training complete! ({elapsed:.1f}s)")
    print(f"  WC model: {os.path.join(models_dir, 'model_wc_calibrated.pkl')}")
    print(f"{'='*65}")

    # -----------------------------------------------------------------------
    # Also compute and save current international Elo ratings
    # (useful for predicting upcoming WC 2026 matches)
    # -----------------------------------------------------------------------
    print(f"\n\nComputing current international Elo ratings for WC 2026...")
    current_elo = compute_intl_elo(intl_df, k=30, home_adv=100)
    top_teams = sorted(current_elo.items(), key=lambda x: -x[1])[:50]
    print(f"  Top 50 international Elo ratings:")
    for rank, (team, elo_val) in enumerate(top_teams, 1):
        print(f"    {rank:3d}. {team:25s}  {elo_val:.0f}")

    # Save Elo ratings
    elo_path = os.path.join(models_dir, "intl_elo_ratings.json")
    with open(elo_path, "w") as f:
        json.dump({
            "ratings": {t: round(e, 1) for t, e in current_elo.items()},
            "top_50": [{"rank": i+1, "team": t, "elo": round(e, 1)}
                       for i, (t, e) in enumerate(top_teams)],
            "n_matches_processed": len(intl_df),
            "last_match_date": str(intl_df["date"].max()),
        }, f, indent=2)
    print(f"  Saved to {elo_path}")


if __name__ == "__main__":
    main()
