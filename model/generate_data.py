"""
generate_data.py
生成模拟历史比赛数据 (用于演示训练流程)

生产环境中，你应该从以下来源下载真实数据：
  - https://www.football-data.co.uk/englandm.php  (免费 CSV)
  - https://github.com/martj42/international_results  (国际赛)
  - https://fbref.com  (含 xG)
  - https://understat.com  (含 xG)
"""

import pandas as pd
import numpy as np

np.random.seed(42)

N = 3000  # 约8个赛季的英超数据量

teams = [
    "Arsenal", "Chelsea", "Liverpool", "Man City", "Man United",
    "Tottenham", "Newcastle", "Aston Villa", "Brighton", "West Ham",
    "Crystal Palace", "Fulham", "Wolves", "Bournemouth", "Brentford",
    "Everton", "Nottingham", "Leicester", "Southampton", "Ipswich",
]

rows = []
for i in range(N):
    ht, at = np.random.choice(teams, 2, replace=False)

    # 模拟 Elo 评分
    home_elo = np.random.normal(1500, 150)
    away_elo = np.random.normal(1500, 150)
    elo_diff = home_elo - away_elo

    # 基于 Elo 差 + 主场优势生成比分
    home_strength = 1.4 + elo_diff / 800  # 主场进球期望 ~1.4
    away_strength = 1.1 - elo_diff / 1000  # 客场进球期望 ~1.1
    home_strength = max(0.3, min(3.0, home_strength))
    away_strength = max(0.3, min(2.5, away_strength))

    hg = np.random.poisson(home_strength)
    ag = np.random.poisson(away_strength)

    # 结果标签
    if hg > ag:
        ftr = "H"
    elif hg == ag:
        ftr = "D"
    else:
        ftr = "A"

    # 模拟赔率 (含水位 margin ~6%)
    margin = 1.06
    p_h = max(0.05, 0.45 + elo_diff / 1500 + np.random.normal(0, 0.05))
    p_a = max(0.05, 0.30 - elo_diff / 1500 + np.random.normal(0, 0.05))
    p_d = max(0.05, 1 - p_h - p_a)
    total = p_h + p_d + p_a
    p_h, p_d, p_a = p_h / total, p_d / total, p_a / total

    odds_h = round(margin / p_h, 2)
    odds_d = round(margin / p_d, 2)
    odds_a = round(margin / p_a, 2)

    # 模拟比赛统计
    hs = np.random.poisson(13)  # 主队射门
    as_ = np.random.poisson(10)
    hst = np.random.poisson(5)  # 射正
    ast = np.random.poisson(4)
    hc = np.random.poisson(5)   # 角球
    ac = np.random.poisson(4)
    hf = np.random.poisson(11)  # 犯规
    af = np.random.poisson(12)
    hy = np.random.poisson(1.5) # 黄牌
    ay = np.random.poisson(1.8)
    hr = 1 if np.random.random() < 0.04 else 0  # 红牌
    ar = 1 if np.random.random() < 0.04 else 0

    # 模拟 xG (更接近真实进球但有噪声)
    home_xg = round(max(0, home_strength + np.random.normal(0, 0.3)), 2)
    away_xg = round(max(0, away_strength + np.random.normal(0, 0.3)), 2)

    rows.append({
        "Date": f"2024-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}",
        "HomeTeam": ht,
        "AwayTeam": at,
        "FTHG": hg,       # 全场主队进球
        "FTAG": ag,        # 全场客队进球
        "FTR": ftr,        # 全场结果 H/D/A
        "HS": hs,          # 主队射门
        "AS": as_,         # 客队射门
        "HST": hst,        # 主队射正
        "AST": ast,        # 客队射正
        "HC": hc,          # 主队角球
        "AC": ac,          # 客队角球
        "HF": hf,          # 主队犯规
        "AF": af,
        "HY": hy,          # 主队黄牌
        "AY": ay,
        "HR": hr,          # 主队红牌
        "AR": ar,
        "B365H": odds_h,   # Bet365 主胜赔率
        "B365D": odds_d,   # Bet365 平局赔率
        "B365A": odds_a,   # Bet365 客胜赔率
        "HomeElo": round(home_elo),
        "AwayElo": round(away_elo),
        "Home_xG": home_xg,
        "Away_xG": away_xg,
    })

df = pd.DataFrame(rows)
df.to_csv("data/matches.csv", index=False)
print(f"✅ 生成 {len(df)} 条比赛数据 → data/matches.csv")
print(f"   结果分布: H={sum(df.FTR=='H')}, D={sum(df.FTR=='D')}, A={sum(df.FTR=='A')}")
print(f"   平均赔率: H={df.B365H.mean():.2f}, D={df.B365D.mean():.2f}, A={df.B365A.mean():.2f}")
print(df.head(3).to_string())
