"""
Total Goals Over/Under Engine — λ_live

Real-time computation of λ_total_live for O/U probability estimation.
Based on: Pre-match intensity + Live tempo/chance quality + Game state + Red cards + Market calibration.
"""

import math


class TotalGoalsEngine:
    """Compute live total goals intensity (λ) and Over/Under probabilities."""

    # Pre-match defaults
    DEFAULT_LAMBDA_PRE = 2.70  # Average total goals per match
    DEFAULT_VSOT_PRE = 0.10    # Average SOT per minute (league baseline)
    DEFAULT_VDA_PRE = 0.55     # Average dangerous attacks per minute

    # Tempo weights (weighted geometric mean)
    W_XG = 0.60
    W_SOT = 0.25
    W_DA = 0.15

    # Game state parameters
    ALPHA = 0.14   # Game state influence strength
    BETA = 0.9     # Game state steepness

    # Red card parameters
    GAMMA = 0.14   # Red card influence strength

    # Market calibration
    ETA = 0.25     # Shrinkage toward market (0 = pure model, 1 = pure market)

    # Signal thresholds
    SIGNAL_THRESHOLDS = [
        {"level": "HIGH",   "edge": 0.08, "tempo": 78},
        {"level": "STRONG", "edge": 0.06, "tempo": 70},
        {"level": "SIGNAL", "edge": 0.04, "tempo": 60},
    ]

    # Signal cooldown tracking
    GOAL_COOLDOWN = 180    # seconds after goal
    SIGNAL_COOLDOWN = 120  # seconds after signal trigger

    def __init__(self):
        self._last_signal_ts = 0
        self._last_goal_ts = 0
        self._last_goals_total = 0

    @staticmethod
    def _sigmoid(x: float) -> float:
        return 1.0 / (1.0 + math.exp(-x))

    @staticmethod
    def _clip(v: float, lo: float, hi: float) -> float:
        return max(lo, min(hi, v))

    @staticmethod
    def _poisson_pmf(k: int, lam: float) -> float:
        if lam <= 0:
            return 1.0 if k == 0 else 0.0
        return math.exp(-lam) * (lam ** k) / math.factorial(k)

    def compute(self, live_state: dict, odds_ou: dict | None = None, now_ts: float = 0) -> dict:
        """
        Compute λ_total_live and O/U probabilities.

        Args:
            live_state: {
                minute, home_goals, away_goals,
                home_xg, away_xg,
                home_shots_on_target, away_shots_on_target,
                home_dangerous_attacks, away_dangerous_attacks,
                home_red, away_red,
                lambda_pre (optional),
            }
            odds_ou: {
                "line": 2.5,
                "over_odds": 1.85,
                "under_odds": 2.05,
            } or None
            now_ts: current timestamp for cooldown tracking

        Returns: dict with all O/U engine outputs
        """
        t = max(1, live_state.get("minute", 0))
        hg = live_state.get("home_goals", 0)
        ag = live_state.get("away_goals", 0)
        goals_so_far = hg + ag
        score_diff = hg - ag

        xg_t = live_state.get("home_xg", 0) + live_state.get("away_xg", 0)
        sot_t = live_state.get("home_shots_on_target", 0) + live_state.get("away_shots_on_target", 0)
        da_t = live_state.get("home_dangerous_attacks", 0) + live_state.get("away_dangerous_attacks", 0)
        rc_h = live_state.get("home_red", 0)
        rc_a = live_state.get("away_red", 0)
        rc_diff = rc_h - rc_a

        lam_pre = live_state.get("lambda_pre", self.DEFAULT_LAMBDA_PRE)

        # ── 1. Remaining time coefficient ──
        r = max(90 - t, 1)
        tau_nl = (r / 90) ** 0.85

        # ── 2. Tempo factor ──
        vxg = xg_t / max(t, 1)
        vxg_pre = lam_pre / 90
        Rxg = self._clip(vxg / max(vxg_pre, 1e-6), 0.4, 2.2)

        vsot = sot_t / max(t, 1)
        Rsot = self._clip(vsot / max(self.DEFAULT_VSOT_PRE, 1e-6), 0.5, 1.8)

        vda = da_t / max(t, 1)
        Rda = self._clip(vda / max(self.DEFAULT_VDA_PRE, 1e-6), 0.5, 1.8)

        Tempo = math.exp(
            self.W_XG * math.log(Rxg)
            + self.W_SOT * math.log(Rsot)
            + self.W_DA * math.log(Rda)
        )
        Tempo_c = self._clip(Tempo, 0.6, 1.7)

        # ── 3. Game state factor ──
        s_t = self._sigmoid((t - 55) / 8)
        G = 1 + self.ALPHA * math.tanh(self.BETA * (-score_diff)) * s_t

        # ── 4. Red card factor ──
        u_dt = 0.6 + 0.4 * self._sigmoid((t - 45) / 10)
        R_raw = 1 + self.GAMMA * math.tanh(-rc_diff) * u_dt
        R_c = self._clip(R_raw, 0.75, 1.25)

        # ── 5. λ_total_live ──
        lam_rem_pre = lam_pre * tau_nl
        lam_rem_live = lam_rem_pre * Tempo_c * G * R_c
        lam_total_live = goals_so_far + lam_rem_live

        # ── 6. Over/Under probabilities ──
        line = 2.5  # Default line
        if odds_ou:
            line = odds_ou.get("line", 2.5)

        # P(total > line) = 1 - P(remaining_goals <= floor(line) - goals_so_far)
        remaining_needed = max(0, math.floor(line) - goals_so_far)
        # Use Poisson CDF for remaining goals
        p_under_model = sum(
            self._poisson_pmf(k, lam_rem_live)
            for k in range(remaining_needed + 1)
        )
        p_over_model = 1.0 - p_under_model
        p_over_model = self._clip(p_over_model, 0.01, 0.99)

        # ── 7. Market calibration ──
        p_mkt_over = None
        if odds_ou and odds_ou.get("over_odds") and odds_ou.get("under_odds"):
            raw_over = 1.0 / odds_ou["over_odds"]
            raw_under = 1.0 / odds_ou["under_odds"]
            total_margin = raw_over + raw_under
            p_mkt_over = raw_over / total_margin
            p_mkt_over = self._clip(p_mkt_over, 0.01, 0.99)

        if p_mkt_over is not None:
            p_final = (1 - self.ETA) * p_over_model + self.ETA * p_mkt_over
        else:
            p_final = p_over_model

        # Market lambda (implied from market odds if available)
        lam_mkt = None
        if p_mkt_over is not None and line == 2.5:
            # Approximate: solve for λ where P(X > 2.5) = p_mkt_over
            # Use bisection method
            lam_mkt = self._estimate_lambda_from_over_prob(p_mkt_over, goals_so_far, line)

        # ── 8. Tempo index (0-100 scale) ──
        tempo_index = round(100 * self._clip((Tempo_c - 0.6) / (1.7 - 0.6), 0, 1))

        # ── 9. Edge & Signal ──
        edge = round((p_final - (p_mkt_over or p_final)) * 100, 2)

        # Cooldown check
        if now_ts > 0:
            if goals_so_far > self._last_goals_total:
                self._last_goal_ts = now_ts
                self._last_goals_total = goals_so_far
            in_cooldown = (
                (now_ts - self._last_goal_ts < self.GOAL_COOLDOWN and self._last_goal_ts > 0)
                or (now_ts - self._last_signal_ts < self.SIGNAL_COOLDOWN and self._last_signal_ts > 0)
            )
        else:
            in_cooldown = False

        signal = "NO SIGNAL"
        signal_level = 0
        if not in_cooldown:
            for threshold in self.SIGNAL_THRESHOLDS:
                if edge / 100 >= threshold["edge"] and tempo_index >= threshold["tempo"]:
                    signal = f"BUY OVER {line}"
                    signal_level = {"SIGNAL": 1, "STRONG": 2, "HIGH": 3}[threshold["level"]]
                    if now_ts > 0:
                        self._last_signal_ts = now_ts
                    break

        # Cooldown remaining
        cooldown_remaining = 0
        if in_cooldown and now_ts > 0:
            cd_goal = max(0, self.GOAL_COOLDOWN - (now_ts - self._last_goal_ts)) if self._last_goal_ts > 0 else 0
            cd_signal = max(0, self.SIGNAL_COOLDOWN - (now_ts - self._last_signal_ts)) if self._last_signal_ts > 0 else 0
            cooldown_remaining = max(cd_goal, cd_signal)

        # ── 10. O/U Scanner (multi-line) ──
        scanner = self.scan_lines(
            lambda_live=lam_total_live,
            market_line=line,
            market_over_prob=p_mkt_over * 100 if p_mkt_over is not None else None,
        )

        return {
            # Core λ values
            "lambda_pre": round(lam_pre, 2),
            "lambda_live": round(lam_total_live, 2),
            "lambda_remaining": round(lam_rem_live, 2),
            "lambda_market": round(lam_mkt, 2) if lam_mkt else None,

            # O/U probabilities
            "line": line,
            "model_prob_over": round(p_over_model * 100, 2),
            "market_prob_over": round(p_mkt_over * 100, 2) if p_mkt_over else None,
            "final_prob_over": round(p_final * 100, 2),
            "final_prob_under": round((1 - p_final) * 100, 2),

            # Edge & Signal
            "edge": edge,
            "signal": signal,
            "signal_level": signal_level,  # 0=none, 1=signal, 2=strong, 3=high

            # Tempo & factors
            "tempo_index": tempo_index,
            "tempo_raw": round(Tempo_c, 3),
            "game_state_factor": round(G, 3),
            "red_card_factor": round(R_c, 3),

            # Cooldown
            "in_cooldown": in_cooldown,
            "cooldown_remaining_sec": round(cooldown_remaining),

            # Scanner (multi-line O/U)
            "scanner": scanner,
        }

    def _poisson_over_prob(self, lam_remaining: float, goals_so_far: int, line: float) -> float:
        """
        Compute P(total > line) using Poisson CDF on remaining goals.
        Handles integer and half-integer lines.
        """
        if line % 1 == 0.5:
            # Standard half-integer line (e.g. 2.5, 3.5): over iff remaining > line - goals
            remaining_needed = max(0, math.floor(line) - goals_so_far)
            p_under = sum(
                self._poisson_pmf(k, lam_remaining)
                for k in range(remaining_needed + 1)
            )
            return self._clip(1.0 - p_under, 0.01, 0.99)
        elif line % 1 == 0.0:
            # Whole number line (e.g. 2.0, 3.0): push on exact
            remaining_needed = max(0, int(line) - goals_so_far)
            p_under = sum(
                self._poisson_pmf(k, lam_remaining)
                for k in range(remaining_needed)
            )
            p_exact = self._poisson_pmf(remaining_needed, lam_remaining) if remaining_needed >= 0 else 0.0
            # Over = strictly above: 1 - P(X < line - gSoFar) - P(X == line - gSoFar)
            # For push (Asian whole line): half win/half lose, but we report raw over prob
            p_over = 1.0 - p_under - p_exact
            return self._clip(p_over, 0.01, 0.99)
        elif line % 1 == 0.25 or line % 1 == 0.75:
            # Quarter lines (e.g. 2.25, 2.75): split between two adjacent half/whole lines
            lo_line = line - 0.25
            hi_line = line + 0.25
            p_lo = self._poisson_over_prob(lam_remaining, goals_so_far, lo_line)
            p_hi = self._poisson_over_prob(lam_remaining, goals_so_far, hi_line)
            return self._clip(0.5 * p_lo + 0.5 * p_hi, 0.01, 0.99)
        else:
            # Fallback: treat as half-integer
            remaining_needed = max(0, math.floor(line) - goals_so_far)
            p_under = sum(
                self._poisson_pmf(k, lam_remaining)
                for k in range(remaining_needed + 1)
            )
            return self._clip(1.0 - p_under, 0.01, 0.99)

    def scan_lines(self, lambda_live: float, market_line: float = 2.5,
                   market_over_prob: float = None) -> list[dict]:
        """
        Compute O/U probabilities for multiple lines.

        Args:
            lambda_live: Total lambda (goals_so_far + lambda_remaining).
            market_line: The currently active traded line (default 2.5).
            market_over_prob: Market-implied over probability for the active line (or None).

        Returns:
            List of dicts, one per scanned line.
        """
        SCAN_LINES = [1.5, 2.0, 2.25, 2.5, 2.75, 3.0, 3.5]
        results = []

        for ln in SCAN_LINES:
            over_prob = self._poisson_over_prob(lambda_live, 0, ln)
            under_prob = self._clip(1.0 - over_prob, 0.01, 0.99)

            # Market probability: only valid for the active market line
            mkt_over = None
            edge = None
            if market_over_prob is not None and abs(ln - market_line) < 1e-6:
                mkt_over = round(market_over_prob, 2)
                edge = round(over_prob * 100 - mkt_over, 2)

            is_active = abs(ln - market_line) < 1e-6

            results.append({
                "line": ln,
                "over_prob": round(over_prob * 100, 2),
                "under_prob": round(under_prob * 100, 2),
                "market_over_prob": mkt_over,
                "edge": edge,
                "is_active": is_active,
            })

        return results

    def _estimate_lambda_from_over_prob(self, p_over: float, goals_so_far: int, line: float) -> float:
        """Estimate λ_remaining from market over probability using bisection."""
        remaining_needed = max(0, math.floor(line) - goals_so_far)
        lo, hi = 0.01, 8.0
        for _ in range(50):
            mid = (lo + hi) / 2
            p_under = sum(self._poisson_pmf(k, mid) for k in range(remaining_needed + 1))
            if 1 - p_under < p_over:
                lo = mid
            else:
                hi = mid
        return goals_so_far + (lo + hi) / 2
