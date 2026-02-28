/**
 * v1.1 Payload Mapper
 * Maps snake_case backend payload → frontend UI fields
 * Single source of truth for data transformation
 */

export function mapPayload(raw) {
  if (!raw || !raw.match) return null;

  const m = raw.match;
  const p = raw.probability || {};
  const s = raw.stats || {};
  const q = raw.quant || {};
  const mk = raw.market || {};
  const uc = raw.uncertainty || {};
  const ex = raw.explain || {};
  const rp = raw.report || {};
  const mt = raw.meta || {};

  return {
    // Meta
    meta: {
      matchId: mt.match_id,
      source: mt.source || {},
      lastUpdateTs: mt.last_update_ts || 0,
      dataDelaySec: mt.data_delay_sec || 0,
      health: mt.health || "OK",
      seq: mt.seq || 0,
    },

    // Match info
    minute: m.minute || 0,
    half: m.half || "H1",
    score: m.score ? m.score.split("-").map(Number) : [0, 0],
    home: { code: m.home?.code || "HOM", name: m.home?.name || "Home", nameCn: m.home?.name_cn || "" },
    away: { code: m.away?.code || "AWY", name: m.away?.name || "Away", nameCn: m.away?.name_cn || "" },
    league: m.league || "",
    round: m.round || "",

    // Probability
    probability: { home: p.home || 0, draw: p.draw || 0, away: p.away || 0 },
    delta: { home: p.delta_home || 0, draw: p.delta_draw || 0, away: p.delta_away || 0 },
    confidence: p.model_confidence || 0,

    // Market
    market: mk.implied_prob ? {
      implied: mk.implied_prob,
      edge: mk.edge,
      odds: mk.odds,
    } : null,

    // Stats
    stats: {
      shots: s.shots || [0, 0],
      shotsOn: s.shots_on_target || [0, 0],
      shotsOff: s.shots_off_target || [0, 0],
      xg: s.xg || [0, 0],
      dangerAtk: s.dangerous_attacks || [0, 0],
      corners: s.corners || [0, 0],
      possession: s.possession || [50, 50],
      passAcc: s.pass_accuracy || [80, 80],
      fouls: s.fouls || [0, 0],
      yellows: s.yellow_cards || [0, 0],
      reds: s.red_cards || [0, 0],
      offsides: s.offsides || [0, 0],
      saves: s.saves || [0, 0],
    },

    // Events
    events: (raw.events || []).map(e => ({
      id: e.id,
      minute: e.minute,
      type: e.type,
      team: e.team,
      text: e.text,
    })),

    // Quant
    quant: {
      pressure: q.pressure_index || 50,
      momentum: q.momentum_score || 0,
      volatility: q.volatility_index || 0.5,
      riskConcede: q.risk_of_concede || 30,
      goalWindow: q.expected_goal_window_min
        ? `${q.expected_goal_window_min[0]}-${q.expected_goal_window_min[1]}`
        : "LOW",
      modelVariance: q.model_variance || 0.1,
      xgDelta: q.xg_delta || 0,
    },

    // Uncertainty
    uncertainty: uc.ci95_home ? {
      ci95Home: uc.ci95_home,
      ci95Draw: uc.ci95_draw,
      ci95Away: uc.ci95_away,
      brierRolling: uc.brier_rolling_20m,
      sharpness: uc.sharpness,
      mcRuns: uc.mc_runs,
    } : null,

    // Explain
    explain: ex.summary ? {
      summary: ex.summary,
      topFactors: ex.top_factors || [],
    } : null,

    // Report
    report: {
      halfTimeReady: rp.half_time_ready || false,
      fullTimeReady: rp.full_time_ready || false,
    },

    // Total Goals (O/U engine)
    totalGoals: mapTotalGoals(raw.total_goals),

    // Score Matrix (Poisson correct score)
    scoreMatrix: mapScoreMatrix(raw.score_matrix),

    // Value Bet (EV scanner)
    valueBet: mapValueBet(raw.total_goals?.value_bet),

    // Goal Window detection
    goalWindow: mapGoalWindow(raw.goal_window),

    // Risk Panel
    risk: mapRisk(raw.risk),

    // Line Movement
    lineMovement: mapLineMovement(raw.line_movement),

    // Post-Match Summary
    postMatch: mapPostMatch(raw.post_match),

    // Signal Control (semi-automatic confirmation)
    signalControl: mapSignalControl(raw.signal_control),

    // Performance / Track Record
    performance: mapPerformance(raw.performance),

    // Broadcast (AI Voice Commentary)
    broadcast: mapBroadcast(raw.broadcast),

    // Prediction History (historical accuracy)
    predictionHistory: mapPredictionHistory(raw.prediction_history),

    // Pre-Match Recommendation
    preMatchRec: mapPreMatchRec(raw.pre_match_rec),

    // Model Stats (backtest results)
    modelStats: mapModelStats(raw.model_stats),
  };
}

function mapTotalGoals(tg) {
  if (!tg) return null;
  return {
    lambda_pre: tg.lambda_pre ?? 0,
    lambda_live: tg.lambda_live ?? 0,
    lambda_remaining: tg.lambda_remaining ?? 0,
    lambda_market: tg.lambda_market ?? 0,
    line: tg.line ?? 2.5,
    model_prob_over: tg.model_prob_over ?? 0,
    market_prob_over: tg.market_prob_over ?? 0,
    final_prob_over: tg.final_prob_over ?? 0,
    final_prob_under: tg.final_prob_under ?? 0,
    edge: tg.edge ?? 0,
    signal: tg.signal || "NO SIGNAL",
    signal_level: tg.signal_level ?? 0,
    tempo_index: tg.tempo_index ?? 50,
    tempo_raw: tg.tempo_raw ?? 0,
    game_state_factor: tg.game_state_factor ?? 1.0,
    red_card_factor: tg.red_card_factor ?? 1.0,
    in_cooldown: tg.in_cooldown ?? false,
    cooldown_remaining_sec: tg.cooldown_remaining_sec ?? 0,
    confidence: tg.confidence ?? null,
    ci95: tg.ci95 ?? null,
    scanner: mapScanner(tg.scanner),
  };
}

function mapScanner(scanner) {
  if (!scanner || !Array.isArray(scanner)) return null;
  return scanner.map(row => ({
    line: row.line ?? 0,
    over_prob: row.over_prob ?? 0,
    under_prob: row.under_prob ?? 0,
    market_over_prob: row.market_over_prob ?? null,
    edge: row.edge ?? null,
    is_active: row.is_active ?? false,
  }));
}

function mapGoalWindow(gw) {
  if (!gw) return null;
  return {
    active: gw.active ?? false,
    confidence: gw.confidence ?? 0,
    estimated_duration_min: gw.estimated_duration_min || "",
    elapsed_sec: gw.elapsed_sec ?? 0,
    tempo_c: gw.tempo_c ?? 0,
    lambda_rate: gw.lambda_rate ?? 0,
  };
}

function mapRisk(r) {
  if (!r) return null;
  return {
    model_variance: r.model_variance ?? 0,
    signal_stability: r.signal_stability ?? 100,
    market_volatility: r.market_volatility || "Medium",
    drawdown_guard: r.drawdown_guard || "Active",
  };
}

function mapLineMovement(lm) {
  if (!lm) return null;
  return {
    current_line: lm.current_line ?? 2.5,
    previous_line: lm.previous_line ?? 2.5,
    over_odds: lm.over_odds ?? 1.90,
    over_odds_prev: lm.over_odds_prev ?? 1.90,
    under_odds: lm.under_odds ?? 1.90,
    direction: lm.direction || "NEUTRAL",
    pressure: lm.pressure || "NEUTRAL",
  };
}

function mapSignalControl(sc) {
  if (!sc) return null;
  return {
    state: sc.state || "idle",
    line: sc.line ?? 0,
    model_prob: sc.model_prob ?? 0,
    market_prob: sc.market_prob ?? 0,
    edge: sc.edge ?? 0,
    confirmed_at: sc.confirmed_at ?? null,
    cooldown_remaining: sc.cooldown_remaining ?? 0,
  };
}

function mapPostMatch(pm) {
  if (!pm) return null;
  return {
    active: pm.active ?? false,
    pre_lambda: pm.pre_lambda ?? 0,
    final_goals: pm.final_goals ?? 0,
    final_score: pm.final_score || "0-0",
    peak_lambda: pm.peak_lambda ?? 0,
    best_edge: pm.best_edge ?? 0,
    avg_lambda: pm.avg_lambda ?? 0,
    lambda_accuracy: pm.lambda_accuracy || "MISS",
    total_updates: pm.total_updates ?? 0,
  };
}

function mapPerformance(perf) {
  if (!perf) return null;
  return {
    total_signals: perf.total_signals ?? 0,
    wins: perf.wins ?? 0,
    losses: perf.losses ?? 0,
    pending: perf.pending ?? 0,
    roi_pct: perf.roi_pct ?? 0,
    best_edge: perf.best_edge ?? 0,
    avg_edge: perf.avg_edge ?? 0,
    signals: (perf.signals || []).map(s => ({
      id: s.id,
      minute: s.minute ?? 0,
      type: s.type || "OVER",
      line: s.line ?? 2.5,
      edge: s.edge ?? 0,
      model_prob: s.model_prob ?? 0,
      result: s.result || "pending",
      timestamp: s.timestamp ?? 0,
    })),
  };
}

function mapBroadcast(b) {
  if (!b) return null;
  return {
    text: b.text || "",
    stage: b.stage || "",
    priority: b.priority || "normal",
    timestamp: b.timestamp || 0,
    speaking: b.speaking ?? false,
    cooldown_remaining: b.cooldown_remaining ?? 0,
  };
}

function mapScoreMatrix(sm) {
  if (!sm) return null;
  return {
    matrix: sm.matrix || [],
    top3: sm.top3 || [],
    homeLambda: sm.home_lambda ?? 0,
    awayLambda: sm.away_lambda ?? 0,
  };
}

function mapPredictionHistory(ph) {
  if (!ph) return null;
  return {
    totalMatches: ph.total_matches ?? 0,
    correct1x2: ph.correct_1x2 ?? 0,
    accuracy1x2Pct: ph.accuracy_1x2_pct ?? 0,
    correctOu: ph.correct_ou ?? 0,
    accuracyOuPct: ph.accuracy_ou_pct ?? 0,
    avgConfidence: ph.avg_confidence ?? 0,
    avgBrier: ph.avg_brier ?? 0,
    streak: ph.streak ?? 0,
    byConfidence: ph.by_confidence ?? {},
    recent5: (ph.recent_5 || []).map(r => ({
      match: r.match || "",
      correct: r.correct ?? false,
      type: r.type || "1X2",
    })),
  };
}

function mapPreMatchRec(pm) {
  if (!pm) return null;
  return {
    active: pm.active ?? false,
    recommendation1x2: pm.recommendation_1x2 || "",
    probabilities: pm.probabilities ?? { home: 0, draw: 0, away: 0 },
    ouRecommendation: pm.ou_recommendation || "",
    ouLine: pm.ou_line ?? 2.5,
    probOver: pm.prob_over ?? 0,
    probUnder: pm.prob_under ?? 0,
    lambdaTotal: pm.lambda_total ?? 0,
    confidence: pm.confidence ?? 0,
    keyFactors: (pm.key_factors || []).map(f => ({
      factor: f.factor || "",
      team: f.team || "",
      value: f.value || "",
      direction: f.direction || "neutral",
    })),
    source: pm.source || "ELO",
  };
}

function mapModelStats(ms) {
  if (!ms) return null;
  return {
    total: ms.total ?? 0,
    testPeriod: ms.test_period || "",
    accuracy1x2: ms.accuracy_1x2 ?? 0,
    accuracyOu: ms.accuracy_ou ?? 0,
    meanBrier: ms.mean_brier ?? 0,
    avgConfidence: ms.avg_confidence ?? 0,
    byLeague: ms.by_league ?? {},
    byConfidence: ms.by_confidence ?? {},
    roi: ms.roi ? {
      bets: ms.roi.bets ?? 0,
      staked: ms.roi.staked ?? 0,
      returned: ms.roi.returned ?? 0,
      roiPct: ms.roi.roi_pct ?? 0,
    } : null,
    streak: ms.streak ? {
      maxWin: ms.streak.max_win ?? 0,
      maxLoss: ms.streak.max_loss ?? 0,
    } : null,
  };
}

function mapValueBet(vb) {
  if (!vb) return null;
  return {
    evOver: vb.ev_over ?? 0,
    evUnder: vb.ev_under ?? 0,
    bestSide: vb.best_side || "OVER",
    bestEv: vb.best_ev ?? 0,
    confidence: vb.confidence || "LOW",
    isValue: vb.is_value ?? false,
    line: vb.line ?? 2.5,
  };
}
