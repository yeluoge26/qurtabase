"""
Generate simulated historical match data for demo/training.

In production, download real data from:
  - https://www.football-data.co.uk/englandm.php
  - https://fbref.com
  - https://understat.com
"""

import pandas as pd
import numpy as np
import os

np.random.seed(42)

N = 3000  # ~8 seasons of EPL data

teams = [
    "Arsenal", "Chelsea", "Liverpool", "Man City", "Man United",
    "Tottenham", "Newcastle", "Aston Villa", "Brighton", "West Ham",
    "Crystal Palace", "Fulham", "Wolves", "Bournemouth", "Brentford",
    "Everton", "Nottingham", "Leicester", "Southampton", "Ipswich",
]

rows = []
for i in range(N):
    ht, at = np.random.choice(teams, 2, replace=False)

    home_elo = np.random.normal(1500, 150)
    away_elo = np.random.normal(1500, 150)
    elo_diff = home_elo - away_elo

    home_strength = max(0.3, min(3.0, 1.4 + elo_diff / 800))
    away_strength = max(0.3, min(2.5, 1.1 - elo_diff / 1000))

    hg = np.random.poisson(home_strength)
    ag = np.random.poisson(away_strength)

    if hg > ag:
        ftr = "H"
    elif hg == ag:
        ftr = "D"
    else:
        ftr = "A"

    margin = 1.06
    p_h = max(0.05, 0.45 + elo_diff / 1500 + np.random.normal(0, 0.05))
    p_a = max(0.05, 0.30 - elo_diff / 1500 + np.random.normal(0, 0.05))
    p_d = max(0.05, 1 - p_h - p_a)
    total = p_h + p_d + p_a
    p_h, p_d, p_a = p_h / total, p_d / total, p_a / total

    odds_h = round(margin / p_h, 2)
    odds_d = round(margin / p_d, 2)
    odds_a = round(margin / p_a, 2)

    home_xg = round(max(0, home_strength + np.random.normal(0, 0.3)), 2)
    away_xg = round(max(0, away_strength + np.random.normal(0, 0.3)), 2)

    rows.append({
        "Date": f"2024-{np.random.randint(1,13):02d}-{np.random.randint(1,29):02d}",
        "HomeTeam": ht, "AwayTeam": at,
        "FTHG": hg, "FTAG": ag, "FTR": ftr,
        "HS": np.random.poisson(13), "AS": np.random.poisson(10),
        "HST": np.random.poisson(5), "AST": np.random.poisson(4),
        "HC": np.random.poisson(5), "AC": np.random.poisson(4),
        "HF": np.random.poisson(11), "AF": np.random.poisson(12),
        "HY": np.random.poisson(1.5), "AY": np.random.poisson(1.8),
        "HR": 1 if np.random.random() < 0.04 else 0,
        "AR": 1 if np.random.random() < 0.04 else 0,
        "B365H": odds_h, "B365D": odds_d, "B365A": odds_a,
        "HomeElo": round(home_elo), "AwayElo": round(away_elo),
        "Home_xG": home_xg, "Away_xG": away_xg,
    })

df = pd.DataFrame(rows)

# Ensure output directory exists
os.makedirs("training/data", exist_ok=True)
df.to_csv("training/data/matches.csv", index=False)

print(f"Generated {len(df)} match records -> training/data/matches.csv")
print(f"  Results: H={sum(df.FTR=='H')}, D={sum(df.FTR=='D')}, A={sum(df.FTR=='A')}")
print(f"  Avg odds: H={df.B365H.mean():.2f}, D={df.B365D.mean():.2f}, A={df.B365A.mean():.2f}")
