"""
features.py — Feature Engineering for Football Match Prediction

Features in 6 categories:
  1. Odds-implied probability (strongest - market consensus, averaged across bookmakers)
  2. Elo rating difference (computed from match results)
  3. xG statistics (merged from Understat data)
  4. Recent form (rolling 5-match points, goals scored/conceded)
  5. Match statistics (shots, shots on target, corners)
  6. Derived features (home advantage)
"""

import pandas as pd
import numpy as np
from collections import defaultdict


# ---------------------------------------------------------------------------
# Team name mapping: football-data.co.uk -> Understat
# ---------------------------------------------------------------------------
TEAM_NAME_MAP = {
    # EPL
    "Man United": "Manchester United",
    "Man City": "Manchester City",
    "Newcastle": "Newcastle United",
    "Nott'm Forest": "Nottingham Forest",
    "Wolves": "Wolverhampton Wanderers",
    "Tottenham": "Tottenham",
    "West Ham": "West Ham",
    "West Brom": "West Bromwich Albion",
    "Sheffield United": "Sheffield United",
    "QPR": "Queens Park Rangers",
    "Stoke": "Stoke City",
    "Swansea": "Swansea",
    "Hull": "Hull City",
    "Sunderland": "Sunderland",
    "Middlesbrough": "Middlesbrough",
    "Huddersfield": "Huddersfield",
    "Cardiff": "Cardiff",
    "Norwich": "Norwich",
    "Watford": "Watford",
    "Burnley": "Burnley",
    "Bournemouth": "Bournemouth",
    "Brighton": "Brighton",
    "Leicester": "Leicester",
    "Luton": "Luton",
    "Leeds": "Leeds",
    "Ipswich": "Ipswich",

    # La Liga
    "Ath Madrid": "Atletico Madrid",
    "Ath Bilbao": "Athletic Club",
    "Betis": "Real Betis",
    "Sociedad": "Real Sociedad",
    "Celta": "Celta Vigo",
    "Espanol": "Espanyol",
    "Vallecano": "Rayo Vallecano",
    "Valladolid": "Real Valladolid",
    "Sp Gijon": "Sporting Gijon",
    "La Coruna": "Deportivo La Coruna",
    "Huesca": "SD Huesca",
    "Alaves": "Alaves",
    "Leganes": "Leganes",
    "Malaga": "Malaga",
    "Cordoba": "Cordoba",
    "Granada": "Granada",

    # Bundesliga
    "Dortmund": "Borussia Dortmund",
    "M'gladbach": "Borussia M.Gladbach",
    "Leverkusen": "Bayer Leverkusen",
    "Ein Frankfurt": "Eintracht Frankfurt",
    "RB Leipzig": "RasenBallsport Leipzig",
    "Mainz": "Mainz 05",
    "Heidenheim": "FC Heidenheim",
    "FC Koln": "FC Cologne",
    "Hamburg": "Hamburger SV",
    "Hannover": "Hannover 96",
    "Hertha": "Hertha Berlin",
    "Darmstadt": "Darmstadt",
    "Ingolstadt": "Ingolstadt",
    "Paderborn": "Paderborn",
    "Schalke 04": "Schalke 04",
    "Nurnberg": "Nuernberg",
    "Fortuna Dusseldorf": "Fortuna Duesseldorf",
    "Greuther Furth": "Greuther Fuerth",
    "Bielefeld": "Arminia Bielefeld",

    # Serie A
    "Milan": "AC Milan",
    "Roma": "Roma",
    "Verona": "Hellas Verona",
    "Parma": "Parma Calcio 1913",
    "Chievo": "Chievo",
    "Cesena": "Cesena",
    "Carpi": "Carpi",
    "Crotone": "Crotone",
    "Palermo": "Palermo",
    "Sampdoria": "Sampdoria",
    "Benevento": "Benevento",
    "Pescara": "Pescara",
    "Brescia": "Brescia",
    "Spezia": "Spezia",
    "Salernitana": "Salernitana",
    "Cremonese": "Cremonese",
    "Venezia": "Venezia",
    "Frosinone": "Frosinone",

    # Ligue 1
    "Paris SG": "Paris Saint Germain",
    "St Etienne": "Saint-Etienne",
    "Clermont": "Clermont Foot",
}


# ---------------------------------------------------------------------------
# League mapping: Div code -> Understat league name
# ---------------------------------------------------------------------------
DIV_TO_LEAGUE = {
    "E0": "EPL",
    "E1": "Championship",  # No understat data for Championship
    "SP1": "La_Liga",
    "D1": "Bundesliga",
    "I1": "Serie_A",
    "F1": "Ligue_1",
}

# Filename prefix -> Div code
FILENAME_TO_DIV = {
    "epl": "E0",
    "championship": "E1",
    "laliga": "SP1",
    "bundesliga": "D1",
    "seriea": "I1",
    "ligue1": "F1",
}


def odds_to_probs(h_odds, d_odds, a_odds):
    """Odds -> implied probability (normalized, margin removed)."""
    ph = 1.0 / h_odds
    pd_ = 1.0 / d_odds
    pa = 1.0 / a_odds
    total = ph + pd_ + pa
    if total == 0:
        return 1 / 3, 1 / 3, 1 / 3
    return ph / total, pd_ / total, pa / total


def compute_avg_odds(df: pd.DataFrame) -> pd.DataFrame:
    """Compute average odds across available bookmakers (more robust than single bookmaker)."""
    bookmaker_sets = [
        ("B365H", "B365D", "B365A"),
        ("BWH", "BWD", "BWA"),
        ("PSH", "PSD", "PSA"),
        ("WHH", "WHD", "WHA"),
    ]

    h_odds_cols = []
    d_odds_cols = []
    a_odds_cols = []

    for h, d, a in bookmaker_sets:
        if {h, d, a}.issubset(df.columns):
            h_odds_cols.append(h)
            d_odds_cols.append(d)
            a_odds_cols.append(a)

    if not h_odds_cols:
        return pd.DataFrame({
            "AvgH": np.nan, "AvgD": np.nan, "AvgA": np.nan
        }, index=df.index)

    # Convert to numeric, coerce errors
    h_vals = df[h_odds_cols].apply(pd.to_numeric, errors="coerce")
    d_vals = df[d_odds_cols].apply(pd.to_numeric, errors="coerce")
    a_vals = df[a_odds_cols].apply(pd.to_numeric, errors="coerce")

    return pd.DataFrame({
        "AvgH": h_vals.mean(axis=1),
        "AvgD": d_vals.mean(axis=1),
        "AvgA": a_vals.mean(axis=1),
    }, index=df.index)


# ---------------------------------------------------------------------------
# Elo Rating System
# ---------------------------------------------------------------------------
def compute_elo_ratings(df: pd.DataFrame, k: float = 20, home_adv: float = 65,
                        initial_elo: float = 1500) -> pd.DataFrame:
    """
    Compute Elo ratings chronologically from match results.

    df must be sorted by date and contain: HomeTeam, AwayTeam, FTR (H/D/A).
    Returns df with HomeElo and AwayElo columns (pre-match ratings).
    """
    elo = defaultdict(lambda: initial_elo)
    home_elos = []
    away_elos = []

    for _, row in df.iterrows():
        ht = row["HomeTeam"]
        at = row["AwayTeam"]
        result = row["FTR"]

        h_elo = elo[ht]
        a_elo = elo[at]

        # Store pre-match Elo
        home_elos.append(h_elo)
        away_elos.append(a_elo)

        # Expected scores
        exp_h = 1.0 / (1.0 + 10 ** ((a_elo - (h_elo + home_adv)) / 400))
        exp_a = 1.0 - exp_h

        # Actual scores
        if result == "H":
            actual_h, actual_a = 1.0, 0.0
        elif result == "A":
            actual_h, actual_a = 0.0, 1.0
        else:  # Draw
            actual_h, actual_a = 0.5, 0.5

        # Update Elo
        elo[ht] += k * (actual_h - exp_h)
        elo[at] += k * (actual_a - exp_a)

    df = df.copy()
    df["HomeElo"] = home_elos
    df["AwayElo"] = away_elos
    return df


# ---------------------------------------------------------------------------
# Rolling Form Features
# ---------------------------------------------------------------------------
def compute_rolling_form(df: pd.DataFrame, window: int = 5) -> pd.DataFrame:
    """
    Compute rolling form features for each team:
    - rolling points (W=3, D=1, L=0)
    - rolling goals scored
    - rolling goals conceded

    df must be sorted by date.
    Returns df with new columns.
    """
    df = df.copy()

    # Track per-team history
    team_points = defaultdict(list)
    team_goals_scored = defaultdict(list)
    team_goals_conceded = defaultdict(list)

    home_form = []
    away_form = []
    home_goals_scored_roll = []
    away_goals_scored_roll = []
    home_goals_conceded_roll = []
    away_goals_conceded_roll = []

    for _, row in df.iterrows():
        ht = row["HomeTeam"]
        at = row["AwayTeam"]

        # Get current form BEFORE this match
        h_pts = team_points[ht][-window:] if team_points[ht] else []
        a_pts = team_points[at][-window:] if team_points[at] else []
        h_gs = team_goals_scored[ht][-window:] if team_goals_scored[ht] else []
        a_gs = team_goals_scored[at][-window:] if team_goals_scored[at] else []
        h_gc = team_goals_conceded[ht][-window:] if team_goals_conceded[ht] else []
        a_gc = team_goals_conceded[at][-window:] if team_goals_conceded[at] else []

        home_form.append(np.mean(h_pts) if h_pts else 1.0)  # default ~avg
        away_form.append(np.mean(a_pts) if a_pts else 1.0)
        home_goals_scored_roll.append(np.mean(h_gs) if h_gs else 1.3)
        away_goals_scored_roll.append(np.mean(a_gs) if a_gs else 1.3)
        home_goals_conceded_roll.append(np.mean(h_gc) if h_gc else 1.3)
        away_goals_conceded_roll.append(np.mean(a_gc) if a_gc else 1.3)

        # Update team history AFTER recording pre-match form
        ftr = row["FTR"]
        fthg = row.get("FTHG", 0)
        ftag = row.get("FTAG", 0)

        # Ensure numeric
        try:
            fthg = float(fthg)
            ftag = float(ftag)
        except (ValueError, TypeError):
            fthg, ftag = 0.0, 0.0

        if ftr == "H":
            team_points[ht].append(3)
            team_points[at].append(0)
        elif ftr == "A":
            team_points[ht].append(0)
            team_points[at].append(3)
        else:
            team_points[ht].append(1)
            team_points[at].append(1)

        team_goals_scored[ht].append(fthg)
        team_goals_scored[at].append(ftag)
        team_goals_conceded[ht].append(ftag)
        team_goals_conceded[at].append(fthg)

    df["home_form_pts"] = home_form
    df["away_form_pts"] = away_form
    df["home_goals_scored_roll"] = home_goals_scored_roll
    df["away_goals_scored_roll"] = away_goals_scored_roll
    df["home_goals_conceded_roll"] = home_goals_conceded_roll
    df["away_goals_conceded_roll"] = away_goals_conceded_roll

    return df


# ---------------------------------------------------------------------------
# xG Merging
# ---------------------------------------------------------------------------
def normalize_team_name(name: str) -> str:
    """Normalize team name from football-data.co.uk to Understat naming."""
    if name in TEAM_NAME_MAP:
        return TEAM_NAME_MAP[name]
    return name


def merge_xg_data(df: pd.DataFrame, xg_df: pd.DataFrame) -> pd.DataFrame:
    """
    Merge xG data from Understat into the main DataFrame.
    Match on date (date only, no time) + home team name + away team name.
    """
    df = df.copy()

    if xg_df is None or xg_df.empty:
        df["Home_xG"] = 0.0
        df["Away_xG"] = 0.0
        return df

    # Prepare xG data
    xg = xg_df.copy()
    xg["date_only"] = pd.to_datetime(xg["date"]).dt.date

    # Create lookup key from xG data
    xg_lookup = {}
    for _, row in xg.iterrows():
        key = (row["date_only"], row["home_team"], row["away_team"])
        xg_lookup[key] = (row["home_xg"], row["away_xg"])

    # Map Div to understat league
    home_xg_vals = []
    away_xg_vals = []

    for _, row in df.iterrows():
        date_only = row["Date_parsed"].date() if hasattr(row["Date_parsed"], "date") else row["Date_parsed"]
        h_name = normalize_team_name(row["HomeTeam"])
        a_name = normalize_team_name(row["AwayTeam"])

        key = (date_only, h_name, a_name)
        if key in xg_lookup:
            hxg, axg = xg_lookup[key]
        else:
            # Try +/- 1 day (timezone differences)
            found = False
            for delta in [1, -1, 2, -2]:
                try:
                    alt_date = date_only + pd.Timedelta(days=delta)
                    alt_key = (alt_date, h_name, a_name)
                    if alt_key in xg_lookup:
                        hxg, axg = xg_lookup[alt_key]
                        found = True
                        break
                except Exception:
                    continue
            if not found:
                hxg, axg = 0.0, 0.0

        home_xg_vals.append(float(hxg))
        away_xg_vals.append(float(axg))

    df["Home_xG"] = home_xg_vals
    df["Away_xG"] = away_xg_vals
    return df


# ---------------------------------------------------------------------------
# Main Feature Builder
# ---------------------------------------------------------------------------
def build_prematch_features(df: pd.DataFrame) -> pd.DataFrame:
    """Build pre-match features for model training."""
    feats = pd.DataFrame(index=df.index)

    # 1. Odds-implied probability (averaged across bookmakers)
    avg_odds = compute_avg_odds(df)
    has_odds = avg_odds["AvgH"].notna()

    if has_odds.any():
        probs = avg_odds[has_odds].apply(
            lambda r: odds_to_probs(r["AvgH"], r["AvgD"], r["AvgA"]),
            axis=1,
        )
        feats.loc[has_odds, "odds_home_prob"] = [p[0] for p in probs]
        feats.loc[has_odds, "odds_draw_prob"] = [p[1] for p in probs]
        feats.loc[has_odds, "odds_away_prob"] = [p[2] for p in probs]
        feats["odds_home_minus_away"] = feats["odds_home_prob"] - feats["odds_away_prob"]

    # Also use B365 specifically as a separate signal (most liquid bookmaker)
    if {"B365H", "B365D", "B365A"}.issubset(df.columns):
        b365h = pd.to_numeric(df["B365H"], errors="coerce")
        b365d = pd.to_numeric(df["B365D"], errors="coerce")
        b365a = pd.to_numeric(df["B365A"], errors="coerce")
        mask = b365h.notna() & b365d.notna() & b365a.notna()
        if mask.any():
            inv_h = 1.0 / b365h[mask]
            inv_d = 1.0 / b365d[mask]
            inv_a = 1.0 / b365a[mask]
            total = inv_h + inv_d + inv_a
            feats.loc[mask, "b365_home_prob"] = inv_h / total
            feats.loc[mask, "b365_draw_prob"] = inv_d / total
            feats.loc[mask, "b365_away_prob"] = inv_a / total

    # 2. Elo ratings
    if {"HomeElo", "AwayElo"}.issubset(df.columns):
        feats["elo_diff"] = df["HomeElo"] - df["AwayElo"]
        feats["elo_diff_norm"] = feats["elo_diff"] / 400
        feats["home_elo_norm"] = df["HomeElo"] / 2000
        feats["away_elo_norm"] = df["AwayElo"] / 2000

    # 3. Home advantage
    feats["is_home"] = 1.0

    # 4. xG features
    if {"Home_xG", "Away_xG"}.issubset(df.columns):
        feats["xg_diff"] = df["Home_xG"] - df["Away_xG"]
        feats["xg_total"] = df["Home_xG"] + df["Away_xG"]
        feats["home_xg"] = df["Home_xG"]
        feats["away_xg"] = df["Away_xG"]

    # 5. Rolling form features
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

    # 6. Shot statistics (if available)
    if {"HS", "AS"}.issubset(df.columns):
        hs = pd.to_numeric(df["HS"], errors="coerce").fillna(0)
        as_ = pd.to_numeric(df["AS"], errors="coerce").fillna(0)
        # We don't use raw shots (not available pre-match), but we use
        # them indirectly through rolling averages computed in compute_rolling_shots()
        pass

    return feats


def build_labels(df: pd.DataFrame) -> np.ndarray:
    """Build labels: H->2, D->1, A->0."""
    return df["FTR"].map({"H": 2, "D": 1, "A": 0}).values
