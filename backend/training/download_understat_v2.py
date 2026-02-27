"""
Download xG data from Understat.com using the understat Python package.
Extracts match-level xG for major leagues (2014-2025)
"""
import asyncio
import csv
import os
import sys
import aiohttp
from understat import Understat

OUTPUT_DIR = os.path.join(os.path.dirname(__file__), "data", "understat")
os.makedirs(OUTPUT_DIR, exist_ok=True)

LEAGUES = ["EPL", "La_Liga", "Bundesliga", "Serie_A", "Ligue_1"]
SEASONS = list(range(2014, 2026))


async def main():
    all_data = []
    league_counts = {}

    async with aiohttp.ClientSession() as session:
        understat = Understat(session)

        for league in LEAGUES:
            league_data = []
            print(f"\n{'='*50}")
            print(f"Downloading {league}...")
            print(f"{'='*50}")

            for season in SEASONS:
                try:
                    results = await understat.get_league_results(league, season)
                    for m in results:
                        league_data.append({
                            "league": league,
                            "season": f"{season}/{season+1}",
                            "date": m.get("datetime", ""),
                            "home_team": m["h"]["title"],
                            "away_team": m["a"]["title"],
                            "home_goals": m["goals"]["h"],
                            "away_goals": m["goals"]["a"],
                            "home_xg": float(m["xG"]["h"]),
                            "away_xg": float(m["xG"]["a"]),
                        })
                    print(f"  {league} {season}/{season+1}: {len(results)} matches")
                except Exception as e:
                    print(f"  {league} {season}/{season+1}: Error - {e}")

            # Save per-league CSV
            if league_data:
                outfile = os.path.join(OUTPUT_DIR, f"{league.lower()}_xg.csv")
                fieldnames = list(league_data[0].keys())
                with open(outfile, "w", newline="", encoding="utf-8") as f:
                    writer = csv.DictWriter(f, fieldnames=fieldnames)
                    writer.writeheader()
                    writer.writerows(league_data)
                print(f"  Saved {len(league_data)} matches to {outfile}")
                league_counts[league] = len(league_data)
                all_data.extend(league_data)

    # Save combined CSV
    if all_data:
        outfile = os.path.join(OUTPUT_DIR, "all_leagues_xg.csv")
        fieldnames = list(all_data[0].keys())
        with open(outfile, "w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(all_data)

        print(f"\n{'='*50}")
        print(f"SUMMARY")
        print(f"{'='*50}")
        for league, count in league_counts.items():
            print(f"  {league}: {count} matches")
        print(f"  {'─'*30}")
        print(f"  Total: {len(all_data)} matches")
        print(f"\nSaved to {outfile}")
        print(f"{'='*50}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
