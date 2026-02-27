"""
train.py — 模型训练
Football Match Prediction Model Training Pipeline

模型架构: 两段式
  1. 赛前模型 (Pre-Match): XGBoost 多分类 → 初始 P(H/D/A)
  2. 赛中修正 (Live Update): Poisson 动态调整 → 实时 P(H/D/A)

运行:
  cd football-model
  python generate_data.py   # 生成数据 (或用真实 CSV)
  python train.py           # 训练模型
"""

import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score, StratifiedKFold
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    accuracy_score, log_loss, classification_report,
    confusion_matrix, brier_score_loss
)
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from xgboost import XGBClassifier
import joblib
import json
import warnings
warnings.filterwarnings("ignore")

from features import build_prematch_features, build_labels


def evaluate_model(name, model, X, y, cv=5):
    """
    评估模型 — 用足球预测最重要的指标
    
    关键指标:
    - Accuracy: 基础准确率
    - Log Loss: 概率校准度 (越低越好, 最重要!)
    - Brier Score: 概率准确度 (越低越好)
    """
    print(f"\n{'='*60}")
    print(f"  模型评估: {name}")
    print(f"{'='*60}")

    skf = StratifiedKFold(n_splits=cv, shuffle=True, random_state=42)

    # 交叉验证
    acc_scores = cross_val_score(model, X, y, cv=skf, scoring="accuracy")
    ll_scores = cross_val_score(model, X, y, cv=skf, scoring="neg_log_loss")

    print(f"\n  📊 交叉验证 ({cv}-fold):")
    print(f"     Accuracy:  {acc_scores.mean():.4f} ± {acc_scores.std():.4f}")
    print(f"     Log Loss:  {-ll_scores.mean():.4f} ± {ll_scores.std():.4f}")

    # 训练并在全数据上评估 (展示用)
    model.fit(X, y)
    y_pred = model.predict(X)
    y_proba = model.predict_proba(X)

    print(f"\n  📋 分类报告 (训练集):")
    target_names = ["客胜(A)", "平局(D)", "主胜(H)"]
    print(classification_report(y, y_pred, target_names=target_names, digits=3))

    print(f"  📉 混淆矩阵:")
    cm = confusion_matrix(y, y_pred)
    print(f"            预测A  预测D  预测H")
    for i, label in enumerate(["实际A", "实际D", "实际H"]):
        print(f"     {label}  {cm[i][0]:5d}  {cm[i][1]:5d}  {cm[i][2]:5d}")

    # Brier Score (每个类别)
    print(f"\n  🎯 Brier Score (概率校准度, 越低越好):")
    for i, label in enumerate(target_names):
        bs = brier_score_loss((y == i).astype(int), y_proba[:, i])
        print(f"     {label}: {bs:.4f}")

    return model


def train_baseline_logistic(X, y):
    """
    基线模型: Logistic Regression
    快速、可解释、不容易过拟合
    """
    model = Pipeline([
        ("scaler", StandardScaler()),
        ("clf", LogisticRegression(
            max_iter=2000,
            C=1.0,
            solver="lbfgs",
        ))
    ])
    return evaluate_model("Logistic Regression (基线)", model, X, y)


def train_xgboost(X, y):
    """
    主模型: XGBoost
    表格数据最强模型之一，适合足球预测
    """
    model = XGBClassifier(
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
    )
    return evaluate_model("XGBoost (主模型)", model, X, y)


def train_calibrated_xgboost(X, y):
    """
    校准后的 XGBoost
    
    为什么需要校准?
    XGBoost 的概率输出往往不够"准确"——比如它输出 70% 的比赛，
    实际上可能只有 65% 的胜率。Calibration 修正这个偏差。
    
    对于博彩分析，概率校准度比准确率更重要!
    """
    base = XGBClassifier(
        n_estimators=500,
        max_depth=4,
        learning_rate=0.05,
        subsample=0.8,
        colsample_bytree=0.8,
        min_child_weight=3,
        eval_metric="mlogloss",
        random_state=42,
        verbosity=0,
    )
    model = CalibratedClassifierCV(base, cv=5, method="isotonic")
    return evaluate_model("XGBoost + Calibration (生产模型)", model, X, y)


def analyze_feature_importance(model, feature_names):
    """分析特征重要性"""
    print(f"\n{'='*60}")
    print(f"  特征重要性 (Feature Importance)")
    print(f"{'='*60}\n")

    # 对于 XGBoost 可以直接获取
    if hasattr(model, "feature_importances_"):
        importances = model.feature_importances_
    elif hasattr(model, "named_steps"):
        clf = model.named_steps.get("clf")
        if hasattr(clf, "coef_"):
            importances = np.abs(clf.coef_).mean(axis=0)
        else:
            return
    else:
        return

    pairs = sorted(zip(feature_names, importances), key=lambda x: -x[1])
    for name, imp in pairs:
        bar = "█" * int(imp / max(importances) * 30)
        print(f"  {name:25s}  {imp:.4f}  {bar}")


def main():
    print("=" * 60)
    print("  AI Football Quant Terminal — 模型训练")
    print("  Model Training Pipeline")
    print("=" * 60)

    # ═══ 1. 加载数据 ═══
    print("\n📂 加载数据...")
    df = pd.read_csv("data/matches.csv")
    print(f"   样本数: {len(df)}")
    print(f"   结果分布: H={sum(df.FTR=='H')} ({sum(df.FTR=='H')/len(df)*100:.1f}%)"
          f"  D={sum(df.FTR=='D')} ({sum(df.FTR=='D')/len(df)*100:.1f}%)"
          f"  A={sum(df.FTR=='A')} ({sum(df.FTR=='A')/len(df)*100:.1f}%)")

    # ═══ 2. 特征工程 ═══
    print("\n🔧 构建特征...")
    X_df = build_prematch_features(df)
    y = build_labels(df)

    # 去除含 NaN 的行
    mask = X_df.notna().all(axis=1)
    X_df = X_df[mask]
    y = y[mask.values]

    X = X_df.values
    feature_names = list(X_df.columns)
    print(f"   特征数: {len(feature_names)}")
    print(f"   特征列表: {feature_names}")
    print(f"   有效样本: {len(X)}")

    # ═══ 3. 训练多个模型对比 ═══
    print("\n\n🏋️ 开始训练模型...")

    # 模型 1: Logistic Regression 基线
    model_lr = train_baseline_logistic(X, y)

    # 模型 2: XGBoost
    model_xgb = train_xgboost(X, y)

    # 模型 3: 校准后 XGBoost (生产用)
    model_cal = train_calibrated_xgboost(X, y)

    # ═══ 4. 特征重要性 ═══
    analyze_feature_importance(model_xgb, feature_names)

    # ═══ 5. 保存模型 ═══
    print(f"\n\n💾 保存模型...")

    joblib.dump(model_xgb, "models/model_xgb.pkl")
    print(f"   ✅ models/model_xgb.pkl")

    joblib.dump(model_cal, "models/model_calibrated.pkl")
    print(f"   ✅ models/model_calibrated.pkl")

    joblib.dump(model_lr, "models/model_logistic.pkl")
    print(f"   ✅ models/model_logistic.pkl")

    # 保存特征列表 (推理时需要)
    meta = {
        "feature_names": feature_names,
        "n_features": len(feature_names),
        "n_classes": 3,
        "class_names": ["Away", "Draw", "Home"],
        "class_mapping": {"A": 0, "D": 1, "H": 2},
    }
    with open("models/model_meta.json", "w") as f:
        json.dump(meta, f, indent=2)
    print(f"   ✅ models/model_meta.json")

    # ═══ 6. 快速推理测试 ═══
    print(f"\n\n🔮 推理测试:")
    test_sample = X[0:1]
    proba = model_cal.predict_proba(test_sample)[0]
    print(f"   输入特征: {test_sample[0][:4]}...")
    print(f"   预测概率: A={proba[0]:.3f}  D={proba[1]:.3f}  H={proba[2]:.3f}")
    print(f"   (客胜 {proba[0]*100:.1f}% | 平局 {proba[1]*100:.1f}% | 主胜 {proba[2]*100:.1f}%)")

    print(f"\n{'='*60}")
    print(f"  ✅ 训练完成!")
    print(f"  生产模型: models/model_calibrated.pkl")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
