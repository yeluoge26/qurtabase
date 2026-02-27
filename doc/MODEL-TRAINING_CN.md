# 模型训练需求与后续步骤

> 当前状态：校准 XGBoost 基于 3000 场**模拟**比赛训练
> 目标：基于**真实历史数据**训练生产级模型

---

## 当前模型概况

| 项目 | 当前状态 | 问题 |
|------|----------|------|
| 训练数据 | 3000 场模拟比赛 | 假数据——随机分布，无真实规律 |
| 特征 | 13 个（赔率、Elo、统计、xG） | 特征正确，但数值是合成的 |
| 交叉验证准确率 | ~47%（逻辑回归基线） | 在假数据上无意义 |
| Brier Score | 未追踪 | 必须添加 |
| 校准度 | 未验证 | 必须添加 |
| sklearn 版本 | 1.8.0（本地）vs 1.6.1（Docker） | 导致反序列化警告 |

**结论**：模型架构和代码已达到生产就绪状态，但数据不行。

---

## 需要执行的步骤

### 第 1 步：下载真实训练数据（10 分钟）

从 [football-data.co.uk](https://www.football-data.co.uk/englandm.php) 下载 CSV：

```bash
mkdir -p backend/training/data/real

# EPL — 最近 10 个赛季
for season in 2425 2324 2223 2122 2021 1920 1819 1718 1617 1516; do
  curl -o backend/training/data/real/epl_${season}.csv \
    "https://www.football-data.co.uk/mmz4281/${season}/E0.csv"
done

# 可选：英冠、西甲、德甲、意甲、法甲
# E1=英冠, SP1=西甲, D1=德甲, I1=意甲, F1=法甲
```

每个 CSV 包含（EPL 约 380 行/赛季）：
- `Date, HomeTeam, AwayTeam, FTHG, FTAG, FTR` — 比赛结果
- `HS, AS, HST, AST, HC, AC` — 射门、射正、角球
- `B365H, B365D, B365A` — Bet365 赔率
- `BWH, BWD, BWA, PSH, PSD, PSA` — 更多博彩公司赔率

**预计总量：约 3,800 场 EPL 比赛（10 个赛季）**

### 第 2 步：添加 Elo 评分（30 分钟）

模拟数据使用的是随机 Elo，真实 Elo 评分需要计算：

**方案 A — 从比赛结果计算**（推荐）：
```python
# 所有球队初始 Elo 为 1500，每场比赛后更新
# K 因子 = 20，主场优势 = 65
# 代码模式已存在于 generate_data.py 中
```

**方案 B — 下载预计算数据**：
- [clubelo.com](http://clubelo.com/) 提供所有主要联赛的每日 Elo
- [eloratings.net](https://www.eloratings.net/) 提供国际赛事 Elo

### 第 3 步：添加 xG 数据（可选，1 小时）

football-data.co.uk 的 CSV 不包含 xG。可选方案：

| 来源 | 方式 | 覆盖范围 |
|------|------|----------|
| [Understat](https://understat.com/) | 网页爬取 | EPL、西甲、德甲、意甲、法甲（2014+） |
| [FBref](https://fbref.com/) | 网页爬取 | 所有主要联赛（2017+） |
| [StatsBomb Open Data](https://github.com/statsbomb/open-data) | 免费 JSON | 仅限部分比赛 |

如果没有 xG：设置 `Home_xG = Away_xG = 0`，模型将依赖赔率 + Elo + 统计特征（依然有效）。

### 第 4 步：使用真实数据重新训练（15 分钟）

更新 `backend/training/train.py` 以加载真实 CSV：

```python
import glob
import pandas as pd

# 加载所有真实 CSV
files = glob.glob("data/real/epl_*.csv")
dfs = [pd.read_csv(f, encoding="latin-1") for f in files]
df = pd.concat(dfs, ignore_index=True)

# 确保必要列存在
required = ["B365H", "B365D", "B365A", "HS", "AS", "HST", "AST", "HC", "AC", "FTR"]
df = df.dropna(subset=required)

print(f"使用 {len(df)} 场真实比赛进行训练")
```

### 第 5 步：修复 sklearn 版本不匹配

Docker 镜像使用 `scikit-learn==1.6.1`，而本地训练使用 `1.8.0`。修复方法：

**方案 A** — 在 requirements.txt 中锁定版本：
```
scikit-learn==1.8.0
```

**方案 B** — 在 Docker 容器内重新训练：
```bash
docker exec -it qurtabase-backend-1 python -c "
from training.train import *
# 将使用匹配的 sklearn 版本保存模型
"
```

### 第 6 步：添加完善的评估指标

当前流水线仅报告准确率，必须添加：

```python
from sklearn.metrics import brier_score_loss, log_loss
from sklearn.calibration import calibration_curve

# Brier Score（每个类别，越低越好）
# 3 分类问题，计算每个类别的 OVR Brier
for i, label in enumerate(["客胜", "平局", "主胜"]):
    y_binary = (y_test == i).astype(int)
    brier = brier_score_loss(y_binary, y_proba[:, i])
    print(f"Brier ({label}): {brier:.4f}")

# Log Loss（整体，越低越好）
ll = log_loss(y_test, y_proba)
print(f"LogLoss: {ll:.4f}")

# 校准曲线
for i, label in enumerate(["客胜", "平局", "主胜"]):
    y_binary = (y_test == i).astype(int)
    fraction_pos, mean_predicted = calibration_curve(
        y_binary, y_proba[:, i], n_bins=10
    )
    # 绘图或记录这些值
```

**真实数据上的目标指标：**
| 指标 | 基线（仅赔率） | 目标（XGBoost） |
|------|---------------|-----------------|
| 准确率 | ~52% | >50% |
| Brier Score（均值） | ~0.20 | <0.22 |
| LogLoss | ~0.98 | <0.95 |
| 校准误差 | 每 bin <3% | 每 bin <5% |

---

## 特征工程改进

### 当前特征（13 个）
```
odds_implied_home, odds_implied_draw, odds_implied_away  (来自 B365 赔率)
home_elo, away_elo                                        (Elo 评分)
home_shots, away_shots, home_sot, away_sot               (射门统计)
home_xg, away_xg                                          (预期进球)
home_corners, away_corners                                (角球)
```

### 建议新增特征
```
# 近期状态特征（最近 5 场滚动窗口）
home_form_points_5      # 近 5 场得分（胜=3, 平=1, 负=0）
away_form_points_5
home_goals_scored_5     # 近 5 场进球数
home_goals_conceded_5
away_goals_scored_5
away_goals_conceded_5

# 交锋记录
h2h_home_wins_5        # 最近 5 次交锋主队胜场
h2h_draws_5

# 市场共识（多家博彩公司均值）
avg_odds_home          # Bet365、BetWay、Pinnacle 均值
avg_odds_draw
avg_odds_away
odds_spread            # 最大赔率 - 最小赔率（市场分歧度）

# 上下文特征
is_derby               # 同城德比标记（手动维护列表）
days_since_last_match  # 赛程密集度
```

### 预期特征重要性排名
1. **赔率隐含概率**（最强预测因子）
2. **Elo 评分差值**
3. **近期状态（5 场）**
4. **交锋记录**
5. **xG 统计**（如有）
6. **射门统计**
7. **角球**（最弱）

---

## 模型架构选项

### 当前：单一校准 XGBoost
- 作为基线表现良好
- CalibratedClassifierCV 改善概率估计

### 推荐：集成模型
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

### 未来：神经网络
- 仅在 10,000+ 场比赛时才有意义
- TabNet 或带 Dropout 的简单 MLP
- 在这种规模的表格数据上不太可能超越 XGBoost

---

## 交叉验证策略

**当前**：标准 5 折交叉验证（存在数据泄漏——未来比赛可能出现在训练集中）

**应改为**：基于时间的分割
```python
from sklearn.model_selection import TimeSeriesSplit

# 先按日期排序！
df = df.sort_values("Date")

tscv = TimeSeriesSplit(n_splits=5)
for train_idx, test_idx in tscv.split(X):
    X_train, X_test = X[train_idx], X[test_idx]
    y_train, y_test = y[train_idx], y[test_idx]
    # 训练和评估
```

这样可以防止模型在训练时"看到未来"的数据。

---

## 持续学习流水线（未来）

```
每日（赛后）：
  1. 采集当天比赛的实际结果
  2. 与模型预测对比 → 更新战绩追踪
  3. 将新比赛数据存入训练集

每周：
  1. 使用更新后的数据集重新训练模型
  2. 新模型 vs 当前模型对比（Brier、LogLoss）
  3. 如果改进：部署新模型（保存 .pkl）
  4. 如果变差：保留当前模型

每月：
  1. 特征重要性回顾
  2. 根据贡献度增删特征
  3. 超参数优化（Optuna）
  4. 完整评估报告
```

---

## 快速开始：立即重新训练

```bash
cd backend/training

# 1. 下载真实数据
mkdir -p data/real
for s in 2425 2324 2223 2122 2021 1920 1819 1718 1617 1516; do
  curl -o data/real/epl_${s}.csv \
    "https://www.football-data.co.uk/mmz4281/${s}/E0.csv"
done

# 2. 验证数据
python -c "
import pandas as pd, glob
files = glob.glob('data/real/*.csv')
for f in files:
    df = pd.read_csv(f, encoding='latin-1')
    print(f'{f}: {len(df)} 行, 列: {list(df.columns[:10])}')
"

# 3. 更新 train.py 使用真实数据（参见上面第 4 步）

# 4. 重新训练
python train.py

# 5. 复制模型到生产目录
cp models/trained/model_calibrated.pkl ../../models/trained/

# 6. 重建 Docker
cd ../..
docker compose up --build -d backend
```

---

## 总结：优先级行动清单

| 优先级 | 行动 | 工作量 | 影响 |
|--------|------|--------|------|
| **P0** | 下载真实 EPL CSV（10 个赛季） | 10 分钟 | 基础性 |
| **P0** | 从比赛结果计算 Elo 评分 | 30 分钟 | 关键特征 |
| **P0** | 重新训练并评估（Brier + LogLoss） | 15 分钟 | 基线质量 |
| **P1** | 添加近期状态特征（5 场滚动窗口） | 1 小时 | 准确率 +2-3% |
| **P1** | 基于时间的交叉验证 | 30 分钟 | 正确评估 |
| **P1** | 修复 sklearn 版本不匹配 | 5 分钟 | 消除警告 |
| **P2** | 从 Understat/FBref 爬取 xG | 2 小时 | 边际提升 |
| **P2** | 集成模型（XGBoost + LightGBM + LR） | 1 小时 | 准确率 +1-2% |
| **P3** | 持续学习流水线 | 1 天 | 长期质量 |
