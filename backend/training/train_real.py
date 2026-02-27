"""
train_real.py — Training Pipeline for Real Football Data

Loads 60 CSVs from football-data.co.uk (6 leagues x 10 seasons)
plus xG data from Understat. Computes Elo ratings, rolling form,
merges xG, and trains multi-class prediction models.

Uses TIME-BASED cross-validation (data sorted by date, no future leakage).

Run:
  cd backend
  python training/train_real.py
"""

import os
import sys
import json
import time
import warnings

import pandas as pd
import numpy as np
from sklearn.model_selection import TimeSeriesSplit
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, log_loss, brier_score_loss,
    classification_report, confusion_matrix,
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import joblib

warnings.filterwarnings("ignore")

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import (
    build_prematch_features, build_labels,
    compute_elo_ratings, compute_rolling_form,
    merge_xg_data, FILENAME_TO_DIV,
)


# ---------------------------------------------------------------------------
# Data Loading
# ---------------------------------------------------------------------------
def load_all_real_data(data_dir: str) -> pd.DataFrame:
    """Load all real CSV files from football-data.co.uk."""
    all_dfs = []
    files = sorted(os.listdir(data_dir))

    for fname in files:
        if not fname.endswith(".csv"):
            continue
        fpath = os.path.join(data_dir, fname)
        try:
            df = pd.read_csv(fpath, encoding="latin-1")
        except Exception as e:
            print(f"  WARNING: Failed to read {fname}: {e}")
            continue

        # Skip empty files or files without required columns
        required = {"Date", "HomeTeam", "AwayTeam", "FTHG", "FTAG", "FTR"}
        if not required.issubset(df.columns):
            print(f"  WARNING: {fname} missing required columns, skipping")
            continue

        # Drop rows with no result
        df = df.dropna(subset=["FTR"])
        df = df[df["FTR"].isin(["H", "D", "A"])]

        # Determine league from filename
        prefix = fname.split("_")[0]
        div_code = FILENAME_TO_DIV.get(prefix, "")
        df["Div"] = df["Div"] if "Div" in df.columns else div_code
        df["source_file"] = fname

        # Extract season from filename (e.g., "epl_2425" -> "2024/2025")
        season_code = fname.replace(".csv", "").split("_")[-1]
        df["season_code"] = season_code

        all_dfs.append(df)
        print(f"  Loaded {fname}: {len(df)} matches")

    if not all_dfs:
        raise ValueError("No data files loaded!")

    combined = pd.concat(all_dfs, ignore_index=True)
    print(f"\n  Total matches loaded: {len(combined)}")
    return combined


def parse_dates(df: pd.DataFrame) -> pd.DataFrame:
    """Parse dates from football-data.co.uk format (DD/MM/YYYY or DD/MM/YY)."""
    df = df.copy()

    # Try multiple date formats
    dates = pd.to_datetime(df["Date"], format="%d/%m/%Y", errors="coerce")
    mask_na = dates.isna()
    if mask_na.any():
        dates[mask_na] = pd.to_datetime(
            df.loc[mask_na, "Date"], format="%d/%m/%y", errors="coerce"
        )

    # Last resort: let pandas infer
    mask_na2 = dates.isna()
    if mask_na2.any():
        dates[mask_na2] = pd.to_datetime(
            df.loc[mask_na2, "Date"], dayfirst=True, errors="coerce"
        )

    df["Date_parsed"] = dates

    # Drop rows with unparseable dates
    n_bad = df["Date_parsed"].isna().sum()
    if n_bad > 0:
        print(f"  WARNING: {n_bad} rows with unparseable dates, dropping")
        df = df.dropna(subset=["Date_parsed"])

    return df


def load_xg_data(xg_path: str) -> pd.DataFrame:
    """Load xG data from Understat CSV."""
    if not os.path.exists(xg_path):
        print(f"  WARNING: xG file not found at {xg_path}")
        return pd.DataFrame()

    xg = pd.read_csv(xg_path)
    print(f"  Loaded xG data: {len(xg)} matches")
    print(f"  Leagues: {xg['league'].unique()}")
    return xg


# ---------------------------------------------------------------------------
# Evaluation
# ---------------------------------------------------------------------------
def evaluate_timeseries(name, model, X, y, dates, n_splits=5):
    """Evaluate model using time-series cross-validation (no future leakage)."""
    print(f"\n{'='*65}")
    print(f"  Model: {name}")
    print(f"{'='*65}")

    tscv = TimeSeriesSplit(n_splits=n_splits)

    fold_acc = []
    fold_ll = []
    fold_brier_h = []
    fold_brier_d = []
    fold_brier_a = []

    for fold_idx, (train_idx, test_idx) in enumerate(tscv.split(X)):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model.fit(X_train, y_train)
        y_pred = model.predict(X_test)
        y_proba = model.predict_proba(X_test)

        acc = accuracy_score(y_test, y_pred)
        ll = log_loss(y_test, y_proba, labels=[0, 1, 2])

        # Brier scores per class
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

    print(f"\n  Mean Accuracy:    {np.mean(fold_acc):.4f} +/- {np.std(fold_acc):.4f}")
    print(f"  Mean Log Loss:    {np.mean(fold_ll):.4f} +/- {np.std(fold_ll):.4f}")
    print(f"  Mean Brier (H):   {np.mean(fold_brier_h):.4f}")
    print(f"  Mean Brier (D):   {np.mean(fold_brier_d):.4f}")
    print(f"  Mean Brier (A):   {np.mean(fold_brier_a):.4f}")
    print(f"  Mean Brier (avg): {np.mean(fold_brier_h + fold_brier_d + fold_brier_a):.4f}")

    # Now train on ALL data for the final model
    print(f"\n  Training final model on all {len(X)} samples...")
    model.fit(X, y)

    # Print classification report on full data (train set - just for reference)
    y_pred_all = model.predict(X)
    y_proba_all = model.predict_proba(X)
    target_names = ["Away(0)", "Draw(1)", "Home(2)"]
    print(f"\n  Classification Report (full train set, for reference):")
    print(classification_report(y, y_pred_all, target_names=target_names, digits=3))

    cm = confusion_matrix(y, y_pred_all)
    print(f"  Confusion Matrix:")
    print(f"            Pred_A  Pred_D  Pred_H")
    for i, label in enumerate(["Real_A", "Real_D", "Real_H"]):
        print(f"     {label}  {cm[i][0]:6d}  {cm[i][1]:6d}  {cm[i][2]:6d}")

    results = {
        "mean_accuracy": np.mean(fold_acc),
        "std_accuracy": np.std(fold_acc),
        "mean_logloss": np.mean(fold_ll),
        "mean_brier_home": np.mean(fold_brier_h),
        "mean_brier_draw": np.mean(fold_brier_d),
        "mean_brier_away": np.mean(fold_brier_a),
    }

    return model, results


# ---------------------------------------------------------------------------
# Main
# ---------------------------------------------------------------------------
def main():
    t_start = time.time()

    print("=" * 65)
    print("  Football Prediction - Real Data Training Pipeline")
    print("=" * 65)

    # Paths
    base_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.dirname(base_dir)
    real_data_dir = os.path.join(base_dir, "data", "real")
    xg_path = os.path.join(base_dir, "data", "understat", "all_leagues_xg.csv")
    models_dir = os.path.join(backend_dir, "models", "trained")

    # 1. Load all real data
    print(f"\n[1/6] Loading real match data from {real_data_dir}...")
    df = load_all_real_data(real_data_dir)

    # 2. Parse dates and sort
    print(f"\n[2/6] Parsing dates and sorting chronologically...")
    df = parse_dates(df)
    df = df.sort_values("Date_parsed").reset_index(drop=True)
    print(f"  Date range: {df['Date_parsed'].min()} to {df['Date_parsed'].max()}")

    # Result distribution
    n_total = len(df)
    n_h = (df["FTR"] == "H").sum()
    n_d = (df["FTR"] == "D").sum()
    n_a = (df["FTR"] == "A").sum()
    print(f"  Results: H={n_h} ({n_h/n_total*100:.1f}%)  "
          f"D={n_d} ({n_d/n_total*100:.1f}%)  "
          f"A={n_a} ({n_a/n_total*100:.1f}%)")

    # League breakdown
    print(f"\n  Matches by league:")
    for div, count in df["Div"].value_counts().sort_index().items():
        print(f"    {div}: {count}")

    # 3. Compute Elo ratings
    print(f"\n[3/6] Computing Elo ratings (K=20, home_adv=65)...")
    df = compute_elo_ratings(df, k=20, home_adv=65, initial_elo=1500)
    print(f"  Elo range: {df['HomeElo'].min():.0f} to {df['HomeElo'].max():.0f}")
    print(f"  Sample Elo (last 5 matches):")
    for _, row in df.tail(5).iterrows():
        print(f"    {row['HomeTeam']:20s} ({row['HomeElo']:.0f}) vs "
              f"{row['AwayTeam']:20s} ({row['AwayElo']:.0f})")

    # 4. Load and merge xG data
    print(f"\n[4/6] Loading and merging xG data...")
    xg_df = load_xg_data(xg_path)
    df = merge_xg_data(df, xg_df)
    n_xg = (df["Home_xG"] > 0).sum()
    print(f"  Matches with xG data: {n_xg}/{len(df)} ({n_xg/len(df)*100:.1f}%)")

    # 5. Compute rolling form
    print(f"\n[5/6] Computing rolling form features (window=5)...")
    df = compute_rolling_form(df, window=5)

    # 6. Build features
    print(f"\n[6/6] Building feature matrix...")
    X_df = build_prematch_features(df)
    y = build_labels(df)

    # Drop rows with NaN features
    mask = X_df.notna().all(axis=1)
    n_dropped = (~mask).sum()
    X_df = X_df[mask]
    y = y[mask.values]
    dates = df.loc[mask, "Date_parsed"].values

    X = X_df.values.astype(np.float64)
    feature_names = list(X_df.columns)

    print(f"  Features ({len(feature_names)}): {feature_names}")
    print(f"  Valid samples: {len(X)} (dropped {n_dropped} with NaN)")
    print(f"  Feature matrix shape: {X.shape}")

    # Quick stats on features
    print(f"\n  Feature statistics:")
    for i, fname in enumerate(feature_names):
        vals = X[:, i]
        print(f"    {fname:30s}  mean={np.mean(vals):8.4f}  "
              f"std={np.std(vals):8.4f}  "
              f"min={np.min(vals):8.4f}  max={np.max(vals):8.4f}")

    # Convert dates for splitting
    dates_dt = pd.to_datetime(dates)

    # -----------------------------------------------------------------------
    # Train models with TimeSeriesSplit
    # -----------------------------------------------------------------------
    print(f"\n\n{'#'*65}")
    print(f"  TRAINING MODELS (TimeSeriesSplit, 5 folds)")
    print(f"{'#'*65}")

    all_results = {}

    # Model 1: Logistic Regression (baseline)
    model_lr = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=2000, C=1.0, solver="lbfgs",
        )),
    ])
    model_lr, res_lr = evaluate_timeseries(
        "Logistic Regression (baseline)", model_lr, X, y, dates_dt
    )
    all_results["logistic"] = res_lr

    # Model 2: XGBoost
    model_xgb = XGBClassifier(
        n_estimators=500,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
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
        n_estimators=500,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        gamma=0.1,
        reg_alpha=0.1,
        reg_lambda=1.0,
        eval_metric="mlogloss",
        random_state=42,
        verbosity=0,
        n_jobs=-1,
    )
    model_cal = CalibratedClassifierCV(base_cal, cv=5, method="isotonic")
    model_cal, res_cal = evaluate_timeseries(
        "XGBoost + Calibration (production)", model_cal, X, y, dates_dt
    )
    all_results["calibrated"] = res_cal

    # -----------------------------------------------------------------------
    # Feature Importance (from uncalibrated XGBoost)
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
    # Summary comparison
    # -----------------------------------------------------------------------
    print(f"\n\n{'='*65}")
    print(f"  MODEL COMPARISON SUMMARY")
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
    print(f"\n\nSaving models to {models_dir}...")

    joblib.dump(model_xgb, os.path.join(models_dir, "model_xgb.pkl"))
    print(f"  model_xgb.pkl")

    joblib.dump(model_cal, os.path.join(models_dir, "model_calibrated.pkl"))
    print(f"  model_calibrated.pkl")

    joblib.dump(model_lr, os.path.join(models_dir, "model_logistic.pkl"))
    print(f"  model_logistic.pkl")

    # Save model metadata
    meta = {
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "n_classes": 3,
        "class_names": ["Away", "Draw", "Home"],
        "class_mapping": {"A": 0, "D": 1, "H": 2},
        "training_data": {
            "n_matches": len(X),
            "n_leagues": 6,
            "n_seasons": 10,
            "date_range": [
                str(dates_dt.min()),
                str(dates_dt.max()),
            ],
        },
        "evaluation": all_results,
    }
    meta_path = os.path.join(models_dir, "model_meta.json")
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2)
    print(f"  model_meta.json")

    # -----------------------------------------------------------------------
    # Quick inference test
    # -----------------------------------------------------------------------
    print(f"\n\nInference test (last match in dataset):")
    test_sample = X[-1:]
    proba = model_cal.predict_proba(test_sample)[0]
    last_row = df.iloc[-1]
    print(f"  Match: {last_row['HomeTeam']} vs {last_row['AwayTeam']} "
          f"({last_row['Date_parsed'].strftime('%Y-%m-%d')})")
    print(f"  Actual result: {last_row['FTR']}")
    print(f"  Predicted: A={proba[0]*100:.1f}% | D={proba[1]*100:.1f}% | H={proba[2]*100:.1f}%")

    elapsed = time.time() - t_start
    print(f"\n{'='*65}")
    print(f"  Training complete! ({elapsed:.1f}s)")
    print(f"  Production model: {os.path.join(models_dir, 'model_calibrated.pkl')}")
    print(f"{'='*65}")


if __name__ == "__main__":
    main()
