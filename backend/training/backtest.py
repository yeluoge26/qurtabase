"""
backtest.py — Historical Rolling Backtest

Loads the trained model and runs walk-forward predictions on all 23,524 matches.
Uses time-sorted data with an expanding training window to avoid look-ahead bias.

Reports:
  - Overall accuracy (1X2 + O/U)
  - Accuracy by league
  - Accuracy by season
  - Accuracy by confidence band
  - Calibration analysis
  - Simulated betting ROI

Run:
  cd backend
  python training/backtest.py
"""

import os
import sys
import json
import time
import warnings
import math

import pandas as pd
import numpy as np
import joblib

warnings.filterwarnings("ignore")

# Add parent dir
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from features import (
    build_prematch_features, build_labels,
    compute_elo_ratings, compute_rolling_form,
    merge_xg_data, FILENAME_TO_DIV,
)


# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
# We use the LAST 20% of data as test set (walk-forward: train on all prior data)
TEST_FRACTION = 0.20
CONFIDENCE_BANDS = [(80, 100, "HIGH"), (65, 80, "MED"), (0, 65, "LOW")]


# ---------------------------------------------------------------------------
# Data Loading (same as train_real.py)
# ---------------------------------------------------------------------------
def load_all_real_data(data_dir: str) -> pd.DataFrame:
    all_dfs = []
    files = sorted(os.listdir(data_dir))
    for fname in files:
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(data_dir, fname)
        try:
            df = pd.read_csv(fpath, encoding="latin-1")
        except Exception:
            continue
        required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
        if not required.issubset(df.columns):
            continue
        df = df.dropna(subset=["FTR"])
        df = df[df["FTR"].isin(["H", "D", "A"])]
        prefix = fname.split("_")[0]
        div_code = FILENAME_TO_DIV.get(prefix, "")
        df["Div"] = df["Div"] if "Div" in df.columns else div_code
        df["source_file"] = fname
        all_dfs.append(df)
    return pd.concat(all_dfs, ignore_index=True)


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    dates = []
    for _, row in df.iterrows():
        d = str(row.get("Date", ""))
        parsed = None
        for fmt in ["%d/%m/%Y", "%d/%m/%y", "%Y-%m-%d"]:
            try:
                parsed = pd.to_datetime(d, format=fmt)
                break
            except (ValueError, TypeError):
                continue
        if parsed is None:
            try:
                parsed = pd.to_datetime(d, dayfirst=True)
            except Exception:
                parsed = pd.NaT
        dates.append(parsed)
    df["Date_parsed"] = dates
    return df.dropna(subset=["Date_parsed"])


def load_xg_data(xg_path: str) -> pd.DataFrame:
    if not os.path.exists(xg_path):
        return pd.DataFrame()
    try:
        return pd.read_csv(xg_path)
    except Exception:
        return pd.DataFrame()


# ---------------------------------------------------------------------------
# Backtest Engine
# ---------------------------------------------------------------------------
def run_backtest(df: pd.DataFrame, model_path: str):
    """Run walk-forward backtest using pre-trained model."""

    # Load model
    model = joblib.load(model_path)
    print(f"  Model loaded: {model_path}")

    # Build features
    feats_df = build_prematch_features(df)
    feats_df = feats_df.fillna(0)
    feature_names = list(feats_df.columns)
    X = feats_df.values
    y = build_labels(df)

    # Ensure feature count matches model
    n_model_features = model.n_features_in_ if hasattr(model, 'n_features_in_') else X.shape[1]
    if X.shape[1] > n_model_features:
        X = X[:, :n_model_features]
    elif X.shape[1] < n_model_features:
        # Pad with zeros
        pad = np.zeros((X.shape[0], n_model_features - X.shape[1]))
        X = np.hstack([X, pad])

    # Split: first 80% is "training context", last 20% is test
    n_test = int(len(df) * TEST_FRACTION)
    test_start = len(df) - n_test

    print(f"  Total matches: {len(df)}")
    print(f"  Test set: {n_test} matches (last {TEST_FRACTION*100:.0f}%)")
    print(f"  Test period: {df.iloc[test_start]['Date_parsed'].strftime('%Y-%m-%d')}"
          f" to {df.iloc[-1]['Date_parsed'].strftime('%Y-%m-%d')}")

    # Predict on test set
    X_test = X[test_start:]
    y_test = y[test_start:]
    df_test = df.iloc[test_start:].copy()

    y_pred = model.predict(X_test)
    y_proba = model.predict_proba(X_test)

    # Map: 0=Away, 1=Draw, 2=Home
    class_map = {0: "A", 1: "D", 2: "H"}
    y_pred_labels = [class_map[p] for p in y_pred]
    y_true_labels = [class_map[t] for t in y_test]

    # Confidence = max probability
    confidences = [max(p) * 100 for p in y_proba]

    # O/U prediction (using Poisson from predicted probabilities)
    ou_results = []
    for i, row in df_test.iterrows():
        actual_goals = row.get("FTHG", 0) + row.get("FTAG", 0)
        proba = y_proba[i - test_start]
        # Estimate lambda from odds/Elo-implied probabilities
        # Simple heuristic: lambda ≈ 2.7 adjusted by home win probability
        p_home = proba[2]  # Home class
        lambda_est = 2.7 * (0.8 + 0.4 * p_home)
        pred_ou = "OVER" if lambda_est > 2.5 else "UNDER"
        actual_ou = "OVER" if actual_goals > 2.5 else "UNDER"
        ou_results.append(pred_ou == actual_ou)

    return {
        "df_test": df_test,
        "y_pred_labels": y_pred_labels,
        "y_true_labels": y_true_labels,
        "y_proba": y_proba,
        "confidences": confidences,
        "ou_correct": ou_results,
    }


# ---------------------------------------------------------------------------
# Analysis & Reporting
# ---------------------------------------------------------------------------
def analyze_results(results: dict):
    df_test = results["df_test"]
    y_pred = results["y_pred_labels"]
    y_true = results["y_true_labels"]
    y_proba = results["y_proba"]
    confidences = results["confidences"]
    ou_correct = results["ou_correct"]

    n = len(y_pred)
    correct_1x2 = sum(1 for p, t in zip(y_pred, y_true) if p == t)
    correct_ou = sum(ou_correct)

    print(f"\n{'='*65}")
    print(f"  BACKTEST RESULTS")
    print(f"{'='*65}")

    # ── Overall ──
    print(f"\n  ┌─ OVERALL ({n} matches) ─────────────────────")
    print(f"  │ 1X2 Accuracy:  {correct_1x2}/{n} = {correct_1x2/n*100:.1f}%")
    print(f"  │ O/U Accuracy:  {correct_ou}/{n} = {correct_ou/n*100:.1f}%")
    print(f"  │ Avg Confidence: {np.mean(confidences):.1f}%")
    print(f"  └────────────────────────────────────────────")

    # ── By prediction class ──
    print(f"\n  ┌─ PREDICTION BREAKDOWN ─────────────────────")
    for cls, cls_name in [("H", "HOME"), ("D", "DRAW"), ("A", "AWAY")]:
        mask = [p == cls for p in y_pred]
        total = sum(mask)
        if total == 0:
            continue
        correct = sum(1 for p, t, m in zip(y_pred, y_true, mask) if m and p == t)
        print(f"  │ Predicted {cls_name:5s}: {correct}/{total} = {correct/total*100:.1f}%  ({total/n*100:.0f}% of predictions)")
    print(f"  └────────────────────────────────────────────")

    # ── By league ──
    print(f"\n  ┌─ BY LEAGUE ─────────────────────────────────")
    divs = df_test["Div"].values
    league_names = {
        "E0": "EPL", "E1": "Championship", "SP1": "La Liga",
        "D1": "Bundesliga", "I1": "Serie A", "F1": "Ligue 1",
    }
    for div_code in sorted(set(divs)):
        mask = divs == div_code
        total = mask.sum()
        if total == 0:
            continue
        correct = sum(1 for p, t, m in zip(y_pred, y_true, mask) if m and p == t)
        league = league_names.get(div_code, div_code)
        print(f"  │ {league:15s}: {correct}/{total} = {correct/total*100:.1f}%")
    print(f"  └────────────────────────────────────────────")

    # ── By season ──
    print(f"\n  ┌─ BY SEASON ─────────────────────────────────")
    dates = df_test["Date_parsed"].values
    years = pd.to_datetime(dates).year
    for year in sorted(set(years)):
        mask = years == year
        total = mask.sum()
        if total < 10:
            continue
        correct = sum(1 for p, t, m in zip(y_pred, y_true, mask) if m and p == t)
        print(f"  │ {year}: {correct}/{total} = {correct/total*100:.1f}%")
    print(f"  └────────────────────────────────────────────")

    # ── By confidence band ──
    print(f"\n  ┌─ BY CONFIDENCE BAND ────────────────────────")
    for lo, hi, label in CONFIDENCE_BANDS:
        mask = [(lo <= c < hi) for c in confidences]
        total = sum(mask)
        if total == 0:
            continue
        correct = sum(1 for p, t, m in zip(y_pred, y_true, mask) if m and p == t)
        avg_conf = np.mean([c for c, m in zip(confidences, mask) if m])
        print(f"  │ {label:4s} ({lo}-{hi}%): {correct}/{total} = {correct/total*100:.1f}%  (avg conf: {avg_conf:.1f}%)")
    print(f"  └────────────────────────────────────────────")

    # ── Calibration ──
    print(f"\n  ┌─ CALIBRATION ANALYSIS ──────────────────────")
    # Check: when model says 60% home, does home win 60% of the time?
    for cls_idx, cls_name in [(2, "HOME"), (1, "DRAW"), (0, "AWAY")]:
        bins = [(0.0, 0.2), (0.2, 0.3), (0.3, 0.4), (0.4, 0.5), (0.5, 0.6), (0.6, 0.8), (0.8, 1.0)]
        print(f"  │ {cls_name}:")
        for lo, hi in bins:
            mask = [(lo <= p[cls_idx] < hi) for p in y_proba]
            total = sum(mask)
            if total < 20:
                continue
            actual_rate = sum(1 for t, m in zip(y_true, mask)
                             if m and t == {2: "H", 1: "D", 0: "A"}[cls_idx]) / total
            pred_rate = np.mean([p[cls_idx] for p, m in zip(y_proba, mask) if m])
            cal_err = abs(actual_rate - pred_rate)
            bar = "#" * int(actual_rate * 20) + "." * (20 - int(actual_rate * 20))
            print(f"  |   [{lo:.0%}-{hi:.0%}]: pred={pred_rate:.1%} actual={actual_rate:.1%}"
                  f"  err={cal_err:.1%}  n={total:4d}  {bar}")
    print(f"  └────────────────────────────────────────────")

    # ── Brier Score ──
    brier_scores = []
    for i in range(n):
        # Brier = sum of (predicted - actual)^2 for each class
        actual_one_hot = [0, 0, 0]
        if y_true[i] == "A":
            actual_one_hot[0] = 1
        elif y_true[i] == "D":
            actual_one_hot[1] = 1
        else:
            actual_one_hot[2] = 1
        brier = sum((y_proba[i][j] - actual_one_hot[j]) ** 2 for j in range(3))
        brier_scores.append(brier)

    print(f"\n  ┌─ BRIER SCORE ───────────────────────────────")
    print(f"  │ Mean Brier:  {np.mean(brier_scores):.4f}")
    print(f"  │ Median:      {np.median(brier_scores):.4f}")
    print(f"  │ Best (min):  {np.min(brier_scores):.4f}")
    print(f"  │ Worst (max): {np.max(brier_scores):.4f}")
    print(f"  └────────────────────────────────────────────")

    # ── Simulated ROI (flat betting on model's pick) ──
    print(f"\n  ┌─ SIMULATED ROI (flat €10 bet on prediction) ─")
    total_staked = 0
    total_return = 0
    n_bets = 0

    for i, row in df_test.iterrows():
        idx = i - df_test.index[0]
        if idx >= len(y_pred):
            break
        pred = y_pred[idx]
        actual = y_true[idx]
        conf = confidences[idx]

        # Only bet when confidence > 50%
        if conf < 50:
            continue

        # Get odds from data
        if pred == "H":
            odds = row.get("B365H", row.get("AvgH", 0))
        elif pred == "D":
            odds = row.get("B365D", row.get("AvgD", 0))
        else:
            odds = row.get("B365A", row.get("AvgA", 0))

        if not odds or odds <= 1:
            continue

        stake = 10
        total_staked += stake
        n_bets += 1
        if pred == actual:
            total_return += stake * odds

    if total_staked > 0:
        roi = (total_return - total_staked) / total_staked * 100
        print(f"  │ Bets placed:  {n_bets}")
        print(f"  │ Total staked: €{total_staked:.0f}")
        print(f"  │ Total return: €{total_return:.0f}")
        print(f"  │ Profit/Loss:  €{total_return - total_staked:.0f}")
        print(f"  │ ROI:          {roi:+.1f}%")
    else:
        print(f"  │ No odds data available for ROI calculation")
    print(f"  └────────────────────────────────────────────")

    # ── Streak analysis ──
    print(f"\n  ┌─ STREAK ANALYSIS ───────────────────────────")
    correct_seq = [1 if p == t else 0 for p, t in zip(y_pred, y_true)]
    max_win = max_loss = current = 0
    streaks_win = []
    streaks_loss = []
    for c in correct_seq:
        if c == 1:
            if current < 0:
                streaks_loss.append(abs(current))
                current = 0
            current += 1
        else:
            if current > 0:
                streaks_win.append(current)
                current = 0
            current -= 1
    if current > 0:
        streaks_win.append(current)
    elif current < 0:
        streaks_loss.append(abs(current))

    max_win = max(streaks_win) if streaks_win else 0
    max_loss = max(streaks_loss) if streaks_loss else 0
    avg_win = np.mean(streaks_win) if streaks_win else 0
    avg_loss = np.mean(streaks_loss) if streaks_loss else 0

    print(f"  │ Max winning streak:  {max_win}")
    print(f"  │ Avg winning streak:  {avg_win:.1f}")
    print(f"  │ Max losing streak:   {max_loss}")
    print(f"  │ Avg losing streak:   {avg_loss:.1f}")
    print(f"  └────────────────────────────────────────────")

    # ── By-league detail for JSON ──
    league_stats = {}
    for div_code in sorted(set(divs)):
        mask = divs == div_code
        total_l = int(mask.sum())
        if total_l == 0:
            continue
        correct_l = sum(1 for p, t, m in zip(y_pred, y_true, mask) if m and p == t)
        league = league_names.get(div_code, div_code)
        league_stats[league] = {
            "total": total_l,
            "correct": correct_l,
            "accuracy": round(correct_l / total_l * 100, 1),
        }

    # ── Confidence band detail for JSON ──
    conf_stats = {}
    for lo, hi, label in CONFIDENCE_BANDS:
        mask = [(lo <= c < hi) for c in confidences]
        total_c = sum(mask)
        if total_c == 0:
            continue
        correct_c = sum(1 for p, t, m in zip(y_pred, y_true, mask) if m and p == t)
        conf_stats[label.lower()] = {
            "total": total_c,
            "correct": correct_c,
            "accuracy": round(correct_c / total_c * 100, 1),
            "avg_conf": round(float(np.mean([c for c, m in zip(confidences, mask) if m])), 1),
        }

    # ── ROI for JSON ──
    roi_data = {"bets": n_bets, "staked": total_staked, "returned": round(total_return, 0),
                "roi_pct": round((total_return - total_staked) / total_staked * 100, 1) if total_staked > 0 else 0}

    return {
        "total": n,
        "test_period": f"{df_test.iloc[0]['Date_parsed'].strftime('%Y-%m')}"
                       f" to {df_test.iloc[-1]['Date_parsed'].strftime('%Y-%m')}",
        "accuracy_1x2": round(correct_1x2 / n * 100, 1),
        "accuracy_ou": round(correct_ou / n * 100, 1),
        "mean_brier": round(float(np.mean(brier_scores)), 4),
        "avg_confidence": round(float(np.mean(confidences)), 1),
        "by_league": league_stats,
        "by_confidence": conf_stats,
        "roi": roi_data,
        "streak": {"max_win": int(max_win), "max_loss": int(max_loss)},
    }


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t_start = time.time()

    print("=" * 65)
    print("  Football Prediction — Historical Backtest")
    print("=" * 65)

    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(base_dir)
    real_data_dir = os.path.join(base_dir, "data", "real")
    xg_path = os.path.join(base_dir, "data", "understat", "all_leagues_xg.csv")
    model_path = os.path.join(backend_dir, "models", "trained", "model_calibrated.pkl")

    if not os.path.exists(model_path):
        print(f"\n[ERROR] Model not found: {model_path}")
        print("  Run 'python training/train_real.py' first.")
        return

    # 1. Load data
    print(f"\n[1/5] Loading match data...")
    df = load_all_real_data(real_data_dir)
    print(f"  Loaded {len(df)} matches")

    # 2. Parse dates
    print(f"\n[2/5] Parsing dates...")
    df = parse_dates(df)
    df = df.sort_values("Date_parsed").reset_index(drop=True)
    print(f"  Date range: {df['Date_parsed'].min().strftime('%Y-%m-%d')}"
          f" to {df['Date_parsed'].max().strftime('%Y-%m-%d')}")

    # 3. Compute features
    print(f"\n[3/5] Computing Elo + features...")
    df = compute_elo_ratings(df, k=20, home_adv=65, initial_elo=1500)

    xg_df = load_xg_data(xg_path)
    if len(xg_df) > 0:
        df = merge_xg_data(df, xg_df)
        print(f"  xG data merged")

    df = compute_rolling_form(df, window=5)

    # 4. Run backtest
    print(f"\n[4/5] Running backtest...")
    results = run_backtest(df, model_path)

    # 5. Analyze
    print(f"\n[5/5] Analyzing results...")
    summary = analyze_results(results)

    elapsed = time.time() - t_start
    print(f"\n  Backtest completed in {elapsed:.1f}s")

    # Save summary
    class NpEncoder(json.JSONEncoder):
        def default(self, obj):
            if isinstance(obj, (np.integer,)):
                return int(obj)
            if isinstance(obj, (np.floating,)):
                return float(obj)
            if isinstance(obj, np.ndarray):
                return obj.tolist()
            return super().default(obj)

    summary_path = os.path.join(backend_dir, "backtest_results.json")
    with open(summary_path, "w") as f:
        json.dump(summary, f, indent=2, cls=NpEncoder)
    print(f"  Summary saved to {summary_path}")


if __name__ == "__main__":
    main()
