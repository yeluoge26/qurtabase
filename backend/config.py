import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    # Server
    HOST: str = os.getenv("HOST", "0.0.0.0")
    PORT: int = int(os.getenv("PORT", "8000"))

    # 纳米数据 Nami Data (sportnanoapi.com) — primary live data source
    NAMI_USER: str = os.getenv("NAMI_USER", "")
    NAMI_SECRET: str = os.getenv("NAMI_SECRET", "")
    NAMI_API_BASE: str = "https://open.sportnanoapi.com/api/v5/football"

    # AllSportsApi (allsportsapi.com) — fallback live data source
    ALLSPORTS_API_KEY: str = os.getenv("ALLSPORTS_API_KEY", "")

    # SportMonks Football API (v3)
    SPORTMONKS_API_KEY: str = os.getenv("SPORTMONKS_API_KEY", "")
    SPORTMONKS_API_BASE: str = "https://api.sportmonks.com/v3/football"

    # Legacy: API-Football (kept for backward compat)
    FOOTBALL_API_KEY: str = os.getenv("FOOTBALL_API_KEY", "")
    FOOTBALL_API_BASE: str = "https://v3.football.api-sports.io"

    # Odds API (the-odds-api.com)
    ODDS_API_KEY: str = os.getenv("ODDS_API_KEY", "")
    ODDS_API_BASE: str = "https://api.the-odds-api.com/v4"

    # Redis
    REDIS_URL: str = os.getenv("REDIS_URL", "redis://localhost:6379")

    # Model
    MODEL_PATH: str = os.getenv("MODEL_PATH", "models/trained/model_calibrated.pkl")
    MODEL_META_PATH: str = os.getenv("MODEL_META_PATH", "models/trained/model_meta.json")

    # Refresh intervals (seconds)
    WS_PUSH_INTERVAL: float = 2.0
    API_FETCH_INTERVAL: float = 30.0
    ODDS_FETCH_INTERVAL: float = 60.0

    # Demo mode — when no live data source is configured
    @property
    def has_nami(self) -> bool:
        return bool(self.NAMI_USER and self.NAMI_SECRET)

    @property
    def demo_mode(self) -> bool:
        return not self.NAMI_USER and not self.ALLSPORTS_API_KEY and not self.SPORTMONKS_API_KEY and not self.FOOTBALL_API_KEY

    @property
    def live_source(self) -> str:
        """Return the name of the primary live data source."""
        if self.NAMI_USER:
            return "NamiData"
        if self.ALLSPORTS_API_KEY:
            return "AllSportsApi"
        if self.SPORTMONKS_API_KEY:
            return "SportMonks"
        if self.FOOTBALL_API_KEY:
            return "API-Football"
        return "Demo"

    @property
    def has_odds(self) -> bool:
        return bool(self.ODDS_API_KEY)


settings = Settings()
