"""
Download xG data from Understat.com
Extracts match-level xG for major leagues (2014-2025)
"""
import json
import re
import urllib.request
import csv
import os
import time
import ssl

# Disable SSL verification for scraping
ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "understat")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LEAGUES = {
    "EPL": "EPL",
    "La_liga": "La_Liga",
    "Bundesliga": "Bundesliga",
    "Serie_A": "Serie_A",
    "Ligue_1": "Ligue_1",
}

# Seasons available on Understat (2014/15 to 2024/25)
SEASONS = list(range(2014, 2026))


def fetch_page(url: str) -> str:
    """Fetch a page with retries."""
    for attempt in range(3):
        try:
            req = urllib.request.Request(url, headers={
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
            })
            with urllib.request.urlopen(req, context=ctx, timeout=30) as resp:
                return resp.read().decode("utf-8")
        except Exception as e:
            print(f"  Attempt {attempt+1} failed: {e}")
            if attempt < 2:
                time.sleep(3)
    return ""


def extract_dates_data(html: str) -> list:
    """Extract datesData JSON from Understat page source."""
    # Understat embeds data as: var datesData = JSON.parse('...')
    pattern = r"datesData\s*=\s*JSON\.parse\('(.+?)'\)"
    match = re.search(pattern, html)
    if not match:
        return []

    raw = match.group(1)
    # Understat uses hex escapes
    raw = raw.encode().decode("unicode_escape")
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return []


def download_league_season(league: str, season: int) -> list:
    """Download all matches for a league/season from Understat."""
    url = f"https://understat.com/league/{league}/{season}"
    print(f"  Fetching {league} {season}/{season+1}...")

    html = fetch_page(url)
    if not html:
        print(f"  Failed to fetch {url}")
        return []

    matches = extract_dates_data(html)
    if not matches:
        print(f"  No data found for {league} {season}")
        return []

    results = []
    for m in matches:
        try:
            results.append({
                "league": league,
                "season": f"{season}/{season+1}",
                "date": m.get("datetime", ""),
                "home_team": m.get("h", {}).get("title", ""),
                "away_team": m.get("a", {}).get("title", ""),
                "home_goals": int(m.get("goals", {}).get("h", 0)),
                "away_goals": int(m.get("goals", {}).get("a", 0)),
                "home_xg": float(m.get("xG", {}).get("h", 0)),
                "away_xg": float(m.get("xG", {}).get("a", 0)),
                "result": m.get("result", ""),
                "is_finished": m.get("isResult", False),
            })
        except (ValueError, TypeError, KeyError):
            continue

    return results


def main():
    all_data = []

    for league_key, league_name in LEAGUES.items():
        print(f"\n{'='*50}")
        print(f"Downloading {league_name}...")
        print(f"{'='*50}")

        league_data = []
        for season in SEASONS:
            matches = download_league_season(league_key, season)
            if matches:
                league_data.extend(matches)
                print(f"  → {len(matches)} matches")
            time.sleep(1)  # Rate limiting

        # Save per-league CSV
        if league_data:
            outfile = os.path.join(OUTPUT_DIR, f"{league_name.lower()}_xg.csv")
            fieldnames = ["league", "season", "date", "home_team", "away_team",
                         "home_goals", "away_goals", "home_xg", "away_xg",
                         "result", "is_finished"]
            with open(outfile, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(league_data)
            print(f"\nSaved {len(league_data)} matches to {outfile}")
            all_data.extend(league_data)

    # Save combined CSV
    if all_data:
        combined = os.path.join(OUTPUT_DIR, "all_leagues_xg.csv")
        fieldnames = ["league", "season", "date", "home_team", "away_team",
                     "home_goals", "away_goals", "home_xg", "away_xg",
                     "result", "is_finished"]
        with open(combined, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)
        print(f"\n{'='*50}")
        print(f"Total: {len(all_data)} matches saved to {combined}")
        print(f"{'='*50}")


if __name__ == "__main__":
    main()
