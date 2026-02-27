"""
train.py — Model Training Pipeline

Architecture: Two-stage
  1. Pre-Match Model: XGBoost multi-class -> initial P(H/D/A)
  2. Live Update: Poisson dynamic adjustment -> real-time P(H/D/A)

Run:
  cd backend
  python training/generate_data.py  # Generate data (or use real CSV)
  python training/train.py          # Train model
"""

import os
import sys
import json
import warnings

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import accuracy_score, log_loss, classification_report, confusion_matrix, brier_score_loss
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import joblib

warnings.filterwarnings("ignore")

# Add parent dir to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from features import build_prematch_features, build_labels


def evaluate_model(name, model, X, y, cv=5):
    """Evaluate model with football-relevant metrics."""
    print(f"\n{'='*60}")
    print(f"  Model: {name}")
    print(f"{'='*60}")

    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

    acc_scores = cross_val_score(model, X, y, cv=skf, scoring="accuracy")
    ll_scores = cross_val_score(model, X, y, cv=skf, scoring="neg_log_loss")

    print(f"\n  Cross-validation ({cv}-fold):")
    print(f"     Accuracy:  {acc_scores.mean():.4f} +/- {acc_scores.std():.4f}")
    print(f"     Log Loss:  {-ll_scores.mean():.4f} +/- {ll_scores.std():.4f}")

    model.fit(X, y)
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)

    print(f"\n  Classification Report (train):")
    target_names = ["Away(A)", "Draw(D)", "Home(H)"]
    print(classification_report(y, y_pred, target_names=target_names, digits=3))

    print(f"  Confusion Matrix:")
    cm = confusion_matrix(y, y_pred)
    print(f"            Pred_A  Pred_D  Pred_H")
    for i, label in enumerate(["Real_A", "Real_D", "Real_H"]):
        print(f"     {label}  {cm[i][0]:6d}  {cm[i][1]:6d}  {cm[i][2]:6d}")

    print(f"\n  Brier Score (calibration, lower is better):")
    for i, label in enumerate(target_names):
        bs = brier_score_loss((y == i).astype(int), y_proba[:, i])
        print(f"     {label}: {bs:.4f}")

    return model


def main():
    print("=" * 60)
    print("  AI Football Quant Terminal - Model Training")
    print("=" * 60)

    # Find data file
    data_paths = [
        "training/data/matches.csv",
        "../model/matches.csv",
    ]
    data_path = None
    for p in data_paths:
        if os.path.exists(p):
            data_path = p
            break

    if not data_path:
        print("\nNo data found. Generating simulated data...")
        exec(open("training/generate_data.py").read())
        data_path = "training/data/matches.csv"

    print(f"\nLoading data from {data_path}...")
    df = pd.read_csv(data_path)
    print(f"   Samples: {len(df)}")
    print(f"   Results: H={sum(df.FTR=='H')} ({sum(df.FTR=='H')/len(df)*100:.1f}%)"
          f"  D={sum(df.FTR=='D')} ({sum(df.FTR=='D')/len(df)*100:.1f}%)"
          f"  A={sum(df.FTR=='A')} ({sum(df.FTR=='A')/len(df)*100:.1f}%)")

    # Feature engineering
    print("\nBuilding features...")
    X_df = build_prematch_features(df)
    y = build_labels(df)

    mask = X_df.notna().all(axis=1)
    X_df = X_df[mask]
    y = y[mask.values]

    X = X_df.values
    feature_names = list(X_df.columns)
    print(f"   Features: {len(feature_names)}")
    print(f"   Feature list: {feature_names}")
    print(f"   Valid samples: {len(X)}")

    # Train models
    print("\n\nTraining models...\n")

    # Baseline: Logistic Regression
    model_lr = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(max_iter=2000, C=1.0, solver="lbfgs")),
    ])
    model_lr = evaluate_model("Logistic Regression (baseline)", model_lr, X, y)

    # Main: XGBoost
    model_xgb = XGBClassifier(
        n_estimators=500, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        gamma=0.1, reg_alpha=0.1, reg_lambda=1.0,
        eval_metric="mlogloss", random_state=42, verbosity=0,
    )
    model_xgb = evaluate_model("XGBoost (main)", model_xgb, X, y)

    # Production: Calibrated XGBoost
    base_cal = XGBClassifier(
        n_estimators=500, max_depth=4, learning_rate=0.05,
        subsample=0.8, colsample_bytree=0.8, min_child_weight=3,
        eval_metric="mlogloss", random_state=42, verbosity=0,
    )
    model_cal = CalibratedClassifierCV(base_cal, cv=5, method="isotonic")
    model_cal = evaluate_model("XGBoost + Calibration (production)", model_cal, X, y)

    # Feature importance
    if hasattr(model_xgb, "feature_importances_"):
        print(f"\n{'='*60}")
        print(f"  Feature Importance")
        print(f"{'='*60}\n")
        importances = model_xgb.feature_importances_
        pairs = sorted(zip(feature_names, importances), key=lambda x: -x[1])
        for name, imp in pairs:
            bar = "#" * int(imp / max(importances) * 30)
            print(f"  {name:25s}  {imp:.4f}  {bar}")

    # Save models
    os.makedirs("models/trained", exist_ok=True)
    print(f"\n\nSaving models...")

    joblib.dump(model_xgb, "models/trained/model_xgb.pkl")
    print(f"   models/trained/model_xgb.pkl")

    joblib.dump(model_cal, "models/trained/model_calibrated.pkl")
    print(f"   models/trained/model_calibrated.pkl")

    joblib.dump(model_lr, "models/trained/model_logistic.pkl")
    print(f"   models/trained/model_logistic.pkl")

    meta = {
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "n_classes": 3,
        "class_names": ["Away", "Draw", "Home"],
        "class_mapping": {"A": 0, "D": 1, "H": 2},
    }
    with open("models/trained/model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"   models/trained/model_meta.json")

    # Quick inference test
    print(f"\n\nInference test:")
    test_sample = X[0:1]
    proba = model_cal.predict_proba(test_sample)[0]
    print(f"   Input features: {test_sample[0][:4]}...")
    print(f"   Predicted: A={proba[0]*100:.1f}% | D={proba[1]*100:.1f}% | H={proba[2]*100:.1f}%")

    print(f"\n{'='*60}")
    print(f"  Training complete!")
    print(f"  Production model: models/trained/model_calibrated.pkl")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
