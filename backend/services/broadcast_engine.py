"""
Broadcast Engine — AI Commentary Script Templates & Trigger Rules

Manages bilingual (EN/ZH) 10-stage broadcast scripts for live match commentary.
Provides a trigger rules engine that evaluates live match data and returns
prioritised broadcast messages with cooldown management.
"""

import time
import logging
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Stage identifiers
# ---------------------------------------------------------------------------
STAGES = [
    "PRE_MATCH",
    "KICKOFF",
    "TEMPO_BUILD",
    "SIGNAL_PENDING",
    "SIGNAL_CONFIRM",
    "SIGNAL_COOLDOWN",
    "GOAL",
    "LATE_GAME",
    "FINAL_WINDOW",
    "POST_MATCH",
]

# ---------------------------------------------------------------------------
# 10-Stage bilingual script templates
# Each stage maps to {"en": [...], "zh": [...]} with multiple variants.
# Templates use {placeholders} filled at render time.
# ---------------------------------------------------------------------------
TEMPLATES: dict[str, dict[str, list[str]]] = {
    # Stage 1 — Pre-match opening
    "PRE_MATCH": {
        "en": [
            "Pre-match analysis ready. {home} versus {away}, {league}. "
            "Pre-match lambda at {lambda_pre:.2f}. Model monitoring initiated.",
            "Model loaded for {home} vs {away} ({league}). "
            "Baseline lambda {lambda_pre:.2f}. Awaiting kickoff.",
        ],
        "zh": [
            "赛前分析就绪。{home} 对阵 {away}，{league}。"
            "赛前Lambda {lambda_pre:.2f}。模型监控已启动。",
            "模型已加载：{home} vs {away}（{league}）。"
            "基准Lambda {lambda_pre:.2f}。等待开球。",
        ],
    },

    # Stage 2 — Kickoff monitoring
    "KICKOFF": {
        "en": [
            "Match underway. Initial lambda {lambda_live:.2f}. "
            "Monitoring tempo and xG velocity.",
            "Kickoff confirmed. Lambda {lambda_live:.2f}. "
            "All sensors active — tracking shots, tempo, and market movement.",
        ],
        "zh": [
            "比赛开始。初始Lambda {lambda_live:.2f}。"
            "正在监控比赛节奏与xG速率。",
            "开球确认。Lambda {lambda_live:.2f}。"
            "全指标监控中——射门、节奏、市场动态。",
        ],
    },

    # Stage 3 — Tempo accumulation (15-35 min)
    "TEMPO_BUILD": {
        "en": [
            "Tempo building at minute {minute}. Current tempo index {tempo:.0f}. "
            "Lambda adjusted to {lambda_live:.2f}.",
            "Minute {minute}: tempo index climbing to {tempo:.0f}. "
            "Live lambda now {lambda_live:.2f}.",
        ],
        "zh": [
            "第{minute}分钟，节奏正在累积。当前节奏指数{tempo:.0f}。"
            "Lambda修正至{lambda_live:.2f}。",
            "第{minute}分钟：节奏指数攀升至{tempo:.0f}。"
            "实时Lambda {lambda_live:.2f}。",
        ],
    },

    # Stage 4 — Signal pending (suspense)
    "SIGNAL_PENDING": {
        "en": [
            "Potential opportunity detected. Edge building at {edge:.1f}%. "
            "Model evaluating line {line}.",
            "Edge approaching threshold at {edge:.1f}%. "
            "Line {line} under evaluation. Awaiting confirmation.",
        ],
        "zh": [
            "检测到潜在机会。边际值正在构建，当前{edge:.1f}%。"
            "模型正在评估{line}盘口。",
            "边际值趋近阈值，当前{edge:.1f}%。"
            "盘口{line}评估中，等待确认。",
        ],
    },

    # Stage 5 — Signal confirm
    "SIGNAL_CONFIRM": {
        "en": [
            "Signal confirmed on line {line}. Edge {edge:.1f}%, "
            "model probability {model_prob:.1f}%. Signal locked.",
            "Confirmed: line {line} triggered. Edge {edge:.1f}%, "
            "model confidence {model_prob:.1f}%. Locked in.",
        ],
        "zh": [
            "信号已确认，盘口{line}。边际值{edge:.1f}%，"
            "模型概率{model_prob:.1f}%。信号已锁定。",
            "确认：盘口{line}触发。边际值{edge:.1f}%，"
            "模型置信度{model_prob:.1f}%。已锁定。",
        ],
    },

    # Stage 6 — Signal lock + cooldown
    "SIGNAL_COOLDOWN": {
        "en": [
            "Signal locked. Cooldown active, {cooldown}s remaining. "
            "Next evaluation pending.",
            "Holding signal. {cooldown}s cooldown in effect. "
            "Model will re-evaluate after cooldown expires.",
        ],
        "zh": [
            "信号已锁定。冷却中，剩余{cooldown}秒。"
            "等待下次评估。",
            "信号保持中。冷却{cooldown}秒生效中。"
            "冷却结束后模型将重新评估。",
        ],
    },

    # Stage 7 — Goal trigger + recalc
    "GOAL": {
        "en": [
            "Goal scored! Score now {score}. "
            "Model recalculating lambda. New lambda {lambda_live:.2f}.",
            "GOAL! Updated score: {score}. "
            "Lambda recalculated to {lambda_live:.2f}. All models refreshing.",
        ],
        "zh": [
            "进球！比分{score}。"
            "模型正在重算Lambda。最新Lambda {lambda_live:.2f}。",
            "进球！最新比分：{score}。"
            "Lambda重算为{lambda_live:.2f}。全部模型刷新中。",
        ],
    },

    # Stage 8 — Late game (60 min+)
    "LATE_GAME": {
        "en": [
            "Entering late game phase, minute {minute}. "
            "Lambda remaining {lambda_rem:.2f}. {tempo_note}",
            "Late game — minute {minute}. Remaining lambda {lambda_rem:.2f}. "
            "{tempo_note}",
        ],
        "zh": [
            "进入比赛后段，第{minute}分钟。"
            "剩余Lambda {lambda_rem:.2f}。{tempo_note}",
            "比赛后段——第{minute}分钟。"
            "剩余Lambda {lambda_rem:.2f}。{tempo_note}",
        ],
    },

    # Stage 9 — Final window (80 min+)
    "FINAL_WINDOW": {
        "en": [
            "Final scoring window. Minute {minute}, "
            "lambda remaining {lambda_rem:.2f}. "
            "Any goal now significantly impacts model.",
            "Final window active — minute {minute}. "
            "Remaining lambda {lambda_rem:.2f}. Maximum sensitivity.",
        ],
        "zh": [
            "最后进球窗口。第{minute}分钟，"
            "剩余Lambda {lambda_rem:.2f}。"
            "此刻任何进球将显著影响模型。",
            "最终窗口——第{minute}分钟。"
            "剩余Lambda {lambda_rem:.2f}。模型灵敏度最大化。",
        ],
    },

    # Stage 10 — Post-match summary
    "POST_MATCH": {
        "en": [
            "Match complete. Final score {score}. "
            "Peak lambda reached {peak_lambda:.2f}. "
            "Best edge was {best_edge:.1f}%. Lambda accuracy: {accuracy}.",
            "Full time. {score}. Peak lambda {peak_lambda:.2f}, "
            "best edge {best_edge:.1f}%. Accuracy rating: {accuracy}.",
        ],
        "zh": [
            "比赛结束。最终比分{score}。"
            "峰值Lambda达到{peak_lambda:.2f}。"
            "最佳边际值{best_edge:.1f}%。Lambda准确度：{accuracy}。",
            "终场。{score}。峰值Lambda {peak_lambda:.2f}，"
            "最佳边际值{best_edge:.1f}%。准确度评级：{accuracy}。",
        ],
    },
}


# ---------------------------------------------------------------------------
# Broadcast result helper
# ---------------------------------------------------------------------------
@dataclass
class BroadcastMessage:
    """A single broadcast message produced by the trigger rules engine."""
    text: str
    stage: str
    priority: str  # "critical" | "normal"

    def to_dict(self) -> dict:
        return {"text": self.text, "stage": self.stage, "priority": self.priority}


# ---------------------------------------------------------------------------
# BroadcastEngine
# ---------------------------------------------------------------------------
class BroadcastEngine:
    """
    AI Commentary Broadcast Engine.

    Manages 10-stage bilingual script templates, evaluates trigger rules
    against live match data, and enforces cooldown windows to prevent
    broadcast spam.
    """

    # Cooldown durations (seconds)
    GLOBAL_COOLDOWN = 90       # non-critical broadcasts
    GOAL_COOLDOWN = 60         # post-goal cooldown
    RED_CARD_COOLDOWN = 30     # post-red-card cooldown

    def __init__(self):
        self._last_broadcast_ts: float = 0.0
        self._last_goal_ts: float = 0.0
        self._last_red_card_ts: float = 0.0

        # State tracking for one-shot triggers
        self._last_goal_count: int = 0
        self._last_red_count: int = 0
        self._late_game_triggered: bool = False
        self._final_window_triggered: bool = False

        # Track previous lambda_total for shift detection
        self._prev_lambda_total: float | None = None

        # Template variant index (cycles through variants)
        self._variant_idx: int = 0

    # ------------------------------------------------------------------
    # Template rendering
    # ------------------------------------------------------------------

    def get_template(self, stage: str, lang: str = "en", **kwargs) -> str:
        """
        Render a template for the given stage and language.

        Args:
            stage: One of the STAGES constants (e.g. "GOAL", "KICKOFF").
            lang:  "en" or "zh".
            **kwargs: Placeholder values to fill into the template.

        Returns:
            Formatted string.  Returns a fallback message if the stage
            or language is unknown, or if placeholder data is missing.
        """
        stage_upper = stage.upper()
        if stage_upper not in TEMPLATES:
            logger.warning("Unknown broadcast stage: %s", stage)
            return f"[{stage_upper}] Broadcast unavailable."

        lang_lower = lang.lower()
        variants = TEMPLATES[stage_upper].get(lang_lower)
        if not variants:
            # Fall back to English
            variants = TEMPLATES[stage_upper].get("en", [])
            if not variants:
                return f"[{stage_upper}] No template available."

        # Cycle through variants
        variant = variants[self._variant_idx % len(variants)]
        self._variant_idx += 1

        try:
            return variant.format(**kwargs)
        except KeyError as exc:
            logger.warning(
                "Missing placeholder %s for stage %s; returning raw template",
                exc, stage_upper,
            )
            return variant

    # ------------------------------------------------------------------
    # Cooldown management
    # ------------------------------------------------------------------

    def can_broadcast(self, priority: str = "normal") -> bool:
        """
        Check whether a broadcast is permitted under cooldown rules.

        Args:
            priority: "critical" bypasses cooldown; "normal" respects it.

        Returns:
            True if the broadcast may proceed.
        """
        if priority == "critical":
            return True

        now = time.time()

        # Global non-critical cooldown
        if now - self._last_broadcast_ts < self.GLOBAL_COOLDOWN:
            return False

        # Post-goal cooldown — block normal messages briefly after a goal
        if now - self._last_goal_ts < self.GOAL_COOLDOWN:
            return False

        # Post-red-card cooldown
        if now - self._last_red_card_ts < self.RED_CARD_COOLDOWN:
            return False

        return True

    def record_broadcast(self) -> None:
        """Record the current time as the last broadcast timestamp."""
        self._last_broadcast_ts = time.time()

    # ------------------------------------------------------------------
    # Reset
    # ------------------------------------------------------------------

    def reset(self) -> None:
        """Reset all state for a new match."""
        self._last_broadcast_ts = 0.0
        self._last_goal_ts = 0.0
        self._last_red_card_ts = 0.0
        self._last_goal_count = 0
        self._last_red_count = 0
        self._late_game_triggered = False
        self._final_window_triggered = False
        self._prev_lambda_total = None
        self._variant_idx = 0

    # ------------------------------------------------------------------
    # Trigger rules engine
    # ------------------------------------------------------------------

    def evaluate_triggers(
        self,
        match_data: dict,
        lang: str = "en",
    ) -> list[dict]:
        """
        Evaluate trigger rules against live match data and return a list
        of broadcast messages that should be emitted.

        Rules are evaluated in strict priority order.  Critical triggers
        (goals, red cards) always fire; normal triggers respect cooldown.

        Args:
            match_data: Dict with keys such as:
                minute, score, home, away, league,
                lambda_live, lambda_pre, lambda_total,
                edge, tempo, signal_state,
                line, model_prob, cooldown,
                lambda_rem, tempo_note,
                peak_lambda, best_edge, accuracy,
                home_goals, away_goals,
                home_red, away_red,
                events (list of event dicts), etc.
            lang: "en" or "zh".

        Returns:
            List of dicts: [{"text": str, "stage": str, "priority": str}, ...]
        """
        results: list[BroadcastMessage] = []
        now = time.time()

        # Snapshot cooldown eligibility once at the start of this evaluation.
        # All normal-priority triggers discovered in a single call share the
        # same cooldown gate so they can co-fire (e.g. LATE_GAME + LAMBDA_SHIFT).
        # The broadcast timestamp is recorded once at the end if any trigger fired.
        normal_allowed = self.can_broadcast("normal")

        # ── Extract fields with safe defaults ─────────────────────────
        minute = match_data.get("minute", 0)
        home_goals = match_data.get("home_goals", 0)
        away_goals = match_data.get("away_goals", 0)
        total_goals = home_goals + away_goals
        score = match_data.get("score", f"{home_goals}-{away_goals}")

        home_red = match_data.get("home_red", 0)
        away_red = match_data.get("away_red", 0)
        total_red = home_red + away_red

        edge = match_data.get("edge", 0.0) or 0.0
        tempo = match_data.get("tempo", 50.0) or 50.0
        signal_state = match_data.get("signal_state", "")
        lambda_live = match_data.get("lambda_live", 2.70)
        lambda_pre = match_data.get("lambda_pre", 2.70)
        lambda_total = match_data.get("lambda_total", lambda_live)
        lambda_rem = match_data.get("lambda_rem", 0.0)

        line = match_data.get("line", "O/U 2.5")
        model_prob = match_data.get("model_prob", 0.0)
        cooldown_remaining = match_data.get("cooldown", 0)
        tempo_note = match_data.get("tempo_note", "")

        home = match_data.get("home", "Home")
        away = match_data.get("away", "Away")
        league = match_data.get("league", "")

        peak_lambda = match_data.get("peak_lambda", 0.0)
        best_edge = match_data.get("best_edge", 0.0)
        accuracy = match_data.get("accuracy", "N/A")

        # Shared template kwargs — all placeholders available for any stage
        tpl_kwargs = dict(
            minute=minute, score=score,
            home=home, away=away, league=league,
            lambda_live=lambda_live, lambda_pre=lambda_pre,
            lambda_rem=lambda_rem,
            edge=edge, tempo=tempo,
            line=line, model_prob=model_prob,
            cooldown=cooldown_remaining,
            tempo_note=tempo_note,
            peak_lambda=peak_lambda, best_edge=best_edge,
            accuracy=accuracy,
        )

        had_normal = False  # track whether any normal trigger fired

        # ── Rule 1: GOAL (critical, mandatory) ───────────────────────
        if total_goals > self._last_goal_count:
            text = self.get_template("GOAL", lang, **tpl_kwargs)
            results.append(BroadcastMessage(text=text, stage="GOAL", priority="critical"))
            self._last_goal_count = total_goals
            self._last_goal_ts = now

        # ── Rule 2: RED_CARD (critical, mandatory) ────────────────────
        if total_red > self._last_red_count:
            if lang.lower() == "zh":
                text = (
                    f"红牌！当前红牌数 {total_red}。"
                    f"模型正在重新评估比赛走势。Lambda {lambda_live:.2f}。"
                )
            else:
                text = (
                    f"Red card issued! Total red cards now {total_red}. "
                    f"Model re-evaluating match dynamics. Lambda {lambda_live:.2f}."
                )
            results.append(BroadcastMessage(text=text, stage="RED_CARD", priority="critical"))
            self._last_red_count = total_red
            self._last_red_card_ts = now

        # ── Rule 3: EDGE_HIGH (edge >= 6%) ────────────────────────────
        if edge >= 6.0 and normal_allowed:
            if signal_state == "confirmed":
                text = self.get_template("SIGNAL_CONFIRM", lang, **tpl_kwargs)
                stage = "SIGNAL_CONFIRM"
            else:
                text = self.get_template("SIGNAL_PENDING", lang, **tpl_kwargs)
                stage = "SIGNAL_PENDING"
            results.append(BroadcastMessage(text=text, stage=stage, priority="normal"))
            had_normal = True

        # ── Rule 4: EDGE_BUILDING (4% <= edge < 6%) ──────────────────
        elif 4.0 <= edge < 6.0 and normal_allowed:
            text = self.get_template("SIGNAL_PENDING", lang, **tpl_kwargs)
            results.append(BroadcastMessage(text=text, stage="SIGNAL_PENDING", priority="normal"))
            had_normal = True

        # ── Rule 5: LAMBDA_SHIFT (λ_total change > 8%) ───────────────
        if self._prev_lambda_total is not None and self._prev_lambda_total > 0:
            lambda_change_pct = abs(lambda_total - self._prev_lambda_total) / self._prev_lambda_total * 100
            if lambda_change_pct > 8.0 and normal_allowed:
                if lang.lower() == "zh":
                    text = (
                        f"模型显著波动。Lambda从 {self._prev_lambda_total:.2f} "
                        f"变动至 {lambda_total:.2f}（变动{lambda_change_pct:.1f}%）。"
                    )
                else:
                    text = (
                        f"Significant model fluctuation. Lambda shifted from "
                        f"{self._prev_lambda_total:.2f} to {lambda_total:.2f} "
                        f"({lambda_change_pct:.1f}% change)."
                    )
                results.append(BroadcastMessage(text=text, stage="LAMBDA_SHIFT", priority="normal"))
                had_normal = True
        self._prev_lambda_total = lambda_total

        # ── Rule 6: TEMPO_HIGH (tempo > 70) ───────────────────────────
        if tempo > 70 and normal_allowed:
            if lang.lower() == "zh":
                text = f"高节奏区域。节奏指数 {tempo:.0f}，第{minute}分钟。进球概率提升。"
            else:
                text = (
                    f"High tempo zone. Tempo index {tempo:.0f} at minute {minute}. "
                    f"Elevated goal probability."
                )
            results.append(BroadcastMessage(text=text, stage="TEMPO_HIGH", priority="normal"))
            had_normal = True

        # ── Rule 7: LATE_GAME (minute >= 60, once) ────────────────────
        if minute >= 60 and not self._late_game_triggered and normal_allowed:
            text = self.get_template("LATE_GAME", lang, **tpl_kwargs)
            results.append(BroadcastMessage(text=text, stage="LATE_GAME", priority="normal"))
            self._late_game_triggered = True
            had_normal = True

        # ── Rule 8: FINAL_WINDOW (minute >= 80, once) ─────────────────
        if minute >= 80 and not self._final_window_triggered and normal_allowed:
            text = self.get_template("FINAL_WINDOW", lang, **tpl_kwargs)
            results.append(BroadcastMessage(text=text, stage="FINAL_WINDOW", priority="normal"))
            self._final_window_triggered = True
            had_normal = True

        # ── Record broadcast timestamp once if anything fired ─────────
        if results:
            self.record_broadcast()

        return [msg.to_dict() for msg in results]
