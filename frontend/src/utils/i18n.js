export const LANG = {
  en: {
    // ── Core Layout ──────────────────────────────────────
    stateLabel: "STATE",
    probLabel: "PROBABILITY",
    trendLabel: "TREND",
    statsLabel: "TECHNICAL STATISTICS",
    quantLabel: "QUANT INDICATORS",
    switchLang: "中文",

    // ── Match State ──────────────────────────────────────
    live: "LIVE",
    half: "HALF",
    home: "HOME",
    away: "AWAY",
    delta: "Δ",
    min: "MIN",
    demo: "DEMO",
    connecting: "CONNECTING",
    waitingData: "Waiting for data...",

    // ── Header / System ──────────────────────────────────
    terminalTitle: "AI FOOTBALL QUANT TERMINAL",
    quantTerminal: "QUANT TERMINAL",
    systemOnline: "SYSTEM ONLINE",
    systemOffline: "OFFLINE",
    modelVersion: "MODEL v2.2",
    delay: "DELAY",
    source: "SRC",
    refresh: "REFRESH 2s",

    // ── Tier Labels ──────────────────────────────────────
    free: "FREE",
    pro: "PRO",
    elite: "ELITE",

    // ── Probability ──────────────────────────────────────
    homeWin: "HOME WIN",
    draw: "DRAW",
    awayWin: "AWAY WIN",
    modelConf: "MODEL CONFIDENCE",
    modelVar: "MODEL VARIANCE",
    probTrend: "1X2 PROBABILITY",

    // ── Statistics ───────────────────────────────────────
    shots: "SHOTS",
    shotsOn: "ON TARGET",
    shotsOff: "OFF TARGET",
    xg: "xG",
    dangerAtk: "DANGEROUS ATK",
    corners: "CORNERS",
    possession: "POSSESSION",
    passAcc: "PASS ACCURACY",
    fouls: "FOULS",
    yellows: "YELLOW CARDS",
    reds: "RED CARDS",
    attacks: "ATTACKS",
    saves: "SAVES",
    offsides: "OFFSIDES",
    stat: "STAT",

    // ── Trend Tabs ───────────────────────────────────────
    pressureTrend: "PRESSURE",
    xgTrend: "xG CUMULATIVE",
    lambdaTrend: "λ TOTAL",

    // ── Quant Indicators ─────────────────────────────────
    pressure: "PRESSURE INDEX",
    momentum: "MOMENTUM SHIFT",
    volatility: "VOLATILITY",
    riskConcede: "RISK OF CONCEDE",
    goalWindow: "EXPECTED GOAL WINDOW",
    confInterval: "CONF. INTERVAL",
    xgDelta: "xG DELTA",
    riskIndex: "RISK INDEX",
    ci95Home: "CI95 HOME",
    sharpness: "SHARPNESS",
    brier20: "BRIER 20m",
    mcRuns: "MC RUNS",

    // ── Alert Badges ─────────────────────────────────────
    volSpike: "VOL SPIKE",
    goalWindowBadge: "GOAL WINDOW",
    dataStale: "DATA STALE",

    // ── Disclaimer / Footer ──────────────────────────────
    disclaimer: "DATA VISUALIZATION ONLY — NO MATCH FOOTAGE — QUANT MODEL OUTPUT",
    disclaimerShort: "DATA VISUALIZATION ONLY — NOT FINANCIAL ADVICE",
    copyright: "AI FOOTBALL QUANT TERMINAL v2.0 © 2026 Techspace",
    footerModel: "MODEL XGB+POISSON",

    // ── Half Time ────────────────────────────────────────
    halfTimeSummary: "HT SUMMARY",

    // ── O/U Scanner ──────────────────────────────────────
    ouScanner: "O/U SCANNER",
    multiLine: "MULTI-LINE",
    lineLabel: "LINE",
    overPct: "OVER%",
    edgeLabel: "EDGE",

    // ── Total Goals Engine ───────────────────────────────
    totalGoalsEngine: "TOTAL GOALS ENGINE",
    ouTrading: "O/U TRADING",
    preLambda: "PRE λ",
    liveLambda: "LIVE λ",
    tempoLabel: "TEMPO",
    expLabel: "(EXP 50)",
    modelProb: "Model Prob",
    marketProb: "Market Prob",
    edge: "Edge",
    signal: "SIGNAL",
    nextEvalIn: "NEXT EVAL IN",
    tempoIndex: "TEMPO INDEX",
    pressureIndex: "PRESSURE INDEX",
    gameStateFactor: "GAME STATE FACTOR",
    redCardFactor: "RED CARD FACTOR",
    ci95: "CI95",

    // ── Signal System ────────────────────────────────────
    signalCooldown: "SIGNAL STATUS",
    edgeHeat: "EDGE HEAT",
    modelCycle: "MODEL CYCLE",
    nextEval: "Next Evaluation",
    signalControl: "SIGNAL CONTROL",
    signalReady: "SIGNAL READY",
    signalConfirmed: "SIGNAL CONFIRMED",
    confirm: "CONFIRM",
    reject: "REJECT",
    monitoring: "MONITORING",
    edgeBuilding: "EDGE BUILDING",
    cooldownLabel: "COOLDOWN",
    locked: "Locked — entering cooldown...",
    enterConfirm: "ENTER = CONFIRM | ESC = REJECT",
    over: "OVER",
    under: "UNDER",
    line: "Line",
    model: "Model",
    market: "Market",
    best: "BEST",

    // ── Goal Window ──────────────────────────────────────
    goalWindowLabel: "GOAL WINDOW",
    highGoalWindow: "HIGH GOAL WINDOW",
    estimated: "EST",
    confidence: "CONFIDENCE",
    active: "ACTIVE",

    // ── Line Movement ────────────────────────────────────
    lineMovement: "LINE MOVEMENT",
    overLabel: "Over:",
    pressureLabel: "Pressure:",

    // ── Risk Panel ───────────────────────────────────────
    riskPanel: "RISK PANEL",
    modelVariance: "Model Variance",
    signalStability: "Signal Stability",
    marketVolatility: "Market Volatility",
    drawdownGuard: "Drawdown Guard",

    // ── Model Cycle ──────────────────────────────────────
    monitoringState: "Monitoring",
    evaluatingState: "Evaluating",
    recalcState: "Recalculating",
    recalcLambda: "RECALCULATING λ",
    stateLabel2: "State:",
    volLabel: "Vol:",

    // ── Event Tape / Alerts ──────────────────────────────
    eventTape: "EVENT TAPE",
    lastEvents: "LAST",
    noEventsYet: "NO EVENTS YET",
    goalAlert: "GOAL",
    redCardAlert: "RED CARD",
    probSwing: "PROBABILITY SWING",
    modelRecalc: "MODEL RECALCULATING...",

    // ── Market Edge ──────────────────────────────────────
    marketUnavailable: "MARKET DATA UNAVAILABLE",
    odds: "ODDS",
    mktImplied: "MKT IMPLIED",
    edgeAiMkt: "EDGE (AI-MKT)",

    // ── Explain Panel ────────────────────────────────────
    whyDelta: "WHY Δ",
    factorShotsOnTarget: "SHOTS ON TARGET",
    factorPressure: "PRESSURE INDEX",
    factorGoal: "GOAL SCORED",
    factorRedCard: "RED CARD",
    factorPossession: "POSSESSION",
    factorXgDelta: "xG DELTA",
    factorTimeDecay: "TIME DECAY",

    // ── Report Banner ────────────────────────────────────
    ftReportReady: "FT REPORT READY",
    htReportReady: "HT REPORT READY",
    pressToExport: "— PRESS [R] TO EXPORT",

    // ── Track Record ─────────────────────────────────────
    todayPerformance: "TODAY PERFORMANCE",
    signals: "Signals",
    wins: "Wins",
    losses: "Loss",
    roi: "ROI",
    bestEdge: "Best Edge",

    // ── Post Match ───────────────────────────────────────
    matchSummary: "MATCH SUMMARY",
    finalScore: "FINAL SCORE",
    peakLambda: "Peak λ",
    avgLambda: "Avg λ",
    bestEdgeLabel: "BEST EDGE",
    lambdaAccuracy: "λ ACCURACY",
    updates: "UPDATES",
    exportJson: "EXPORT JSON",
    preLambdaLabel: "Pre λ",
    finalGoalsLabel: "Final Goals",
    accuracyLabel: "Accuracy",
    nextEvalAfterCooldown: "Next evaluation after cooldown",
    multiMatchTerminal: "MULTI-MATCH TERMINAL",

    // ── AI Voice / Broadcast ─────────────────────────────
    aiSpeaking: "AI SPEAKING...",
    aiReady: "AI READY",
    broadcastCooldown: "NEXT",
    stageGoal: "GOAL",
    stageSignal: "SIGNAL",
    stageLatGame: "LATE GAME",
    stagePostMatch: "POST-MATCH",
    stageTempo: "TEMPO",

    // ── Sound Effects ────────────────────────────────────
    soundEffects: "SOUND EFFECTS",
    sfxOn: "SFX ON",
    sfxOff: "SFX OFF",
    soundEnabled: "SOUND",

    // ── Multi-Match / Vote ───────────────────────────────
    multiMatch: "MULTI-MATCH",
    audienceVote: "AUDIENCE VOTE",
    modelVsCrowd: "MODEL vs CROWD",
    aligned: "ALIGNED",
    diverged: "DIVERGED",
    audiencePoll: "AUDIENCE POLL",
    modelVsAudience: "MODEL vs AUDIENCE",
    noActiveMatches: "No active matches",
    votingOpens: "Voting opens at kickoff",
    voteHome: "1  HOME",
    voteDraw: "X  DRAW",
    voteAway: "2  AWAY",
    modelLabel: "MODEL",
    audienceLabel: "AUDIENCE",
    basedOnVotes: "Based on {n} votes",
    vs: "vs",

    // ── Score Matrix ─────────────────────────────────────
    scoreMatrix: "SCORE MATRIX",
    poissonModel: "POISSON MODEL",
    topScores: "TOP 3 MOST LIKELY",
    homeAbbr: "H",
    awayAbbr: "A",

    // ── Value Bet ────────────────────────────────────────
    valueBet: "VALUE BET",
    expectedValue: "EV",
    valueLabel: "VALUE",

    // ── Prediction History ──────────────────────────────
    predictionHistory: "PREDICTION HISTORY",
    accuracy1x2: "1X2 ACCURACY",
    accuracyOu: "O/U ACCURACY",
    correct: "CORRECT",
    streak: "STREAK",
    byConfidence: "BY CONFIDENCE",
    highConf: "HIGH",
    medConf: "MED",
    lowConf: "LOW",
    avgBrier: "AVG BRIER",
    avgConf: "AVG CONF",
    lastNGames: "LAST {n}",
    totalMatches: "TOTAL",

    // ── Pre-Match Analysis ────────────────────────────
    preMatchAnalysis: "PRE-MATCH ANALYSIS",
    recommendation1x2: "1X2 RECOMMENDATION",
    recommendationOu: "O/U RECOMMENDATION",
    keyFactors: "KEY FACTORS",
    eloAdvantage: "ELO ADVANTAGE",
    eloBalanced: "ELO BALANCED",
    expectedGoals: "EXPECTED GOALS",
    marketAligned: "MARKET ALIGNED",
    noMarketData: "NO MARKET DATA",
    modelSource: "SOURCE",

    // ── Model Stats (Backtest) ────────────────────────────
    modelPerformance: "MODEL PERFORMANCE",
    backtestResults: "BACKTEST RESULTS",
    testPeriod: "TEST PERIOD",
    totalSample: "TOTAL SAMPLE",
    simulatedRoi: "SIMULATED ROI",
    roiLabel: "ROI",
    betsPlaced: "BETS PLACED",
    totalStaked: "TOTAL STAKED",
    profit: "PROFIT",
    returned: "RETURNED",
    maxWinStreak: "MAX WIN STREAK",
    maxLossStreak: "MAX LOSS STREAK",
    byLeague: "BY LEAGUE",
    matches: "MATCHES",
    accuracy: "ACCURACY",
    meanBrier: "MEAN BRIER",
    highConfPredictions: "HIGH CONFIDENCE",
    medConfPredictions: "MEDIUM CONFIDENCE",
    lowConfPredictions: "LOW CONFIDENCE",

    // ── Live Status ──────────────────────────────────────
    liveStatus: "LIVE",
    upcoming: "UPCOMING",
    signalLabel: "SIGNAL",
  },
  zh: {
    // ── 核心布局 ─────────────────────────────────────────
    stateLabel: "比赛状态",
    probLabel: "概率面板",
    trendLabel: "走势图",
    statsLabel: "技术统计",
    quantLabel: "量化指标",
    switchLang: "EN",

    // ── 比赛状态 ─────────────────────────────────────────
    live: "直播",
    half: "半场",
    home: "主队",
    away: "客队",
    delta: "Δ",
    min: "分钟",
    demo: "演示",
    connecting: "连接中",
    waitingData: "等待数据中...",

    // ── 顶栏 / 系统 ─────────────────────────────────────
    terminalTitle: "人工智能足球量化终端",
    quantTerminal: "量化终端",
    systemOnline: "系统在线",
    systemOffline: "离线",
    modelVersion: "模型 v2.2",
    delay: "延迟",
    source: "数据源",
    refresh: "刷新 2秒",

    // ── 层级标签 ─────────────────────────────────────────
    free: "免费",
    pro: "专业",
    elite: "精英",

    // ── 概率 ─────────────────────────────────────────────
    homeWin: "主胜",
    draw: "平局",
    awayWin: "客胜",
    modelConf: "模型置信度",
    modelVar: "模型方差",
    probTrend: "胜平负概率",

    // ── 技术统计 ─────────────────────────────────────────
    shots: "射门",
    shotsOn: "射正",
    shotsOff: "射偏",
    xg: "期望进球",
    dangerAtk: "危险进攻",
    corners: "角球",
    possession: "控球率",
    passAcc: "传球成功率",
    fouls: "犯规",
    yellows: "黄牌",
    reds: "红牌",
    attacks: "进攻次数",
    saves: "扑救",
    offsides: "越位",
    stat: "统计",

    // ── 走势标签 ─────────────────────────────────────────
    pressureTrend: "压力指数",
    xgTrend: "累计期望进球",
    lambdaTrend: "λ 总进球",

    // ── 量化指标 ─────────────────────────────────────────
    pressure: "压力指数",
    momentum: "攻防势头",
    volatility: "波动率",
    riskConcede: "失球风险",
    goalWindow: "预期进球窗口",
    confInterval: "置信区间",
    xgDelta: "期望进球差值",
    riskIndex: "风险指数",
    ci95Home: "95%置信区间 主队",
    sharpness: "锐度",
    brier20: "布莱尔评分 20分钟",
    mcRuns: "蒙特卡洛模拟次数",

    // ── 警报徽章 ─────────────────────────────────────────
    volSpike: "波动飙升",
    goalWindowBadge: "进球窗口",
    dataStale: "数据过期",

    // ── 免责 / 页脚 ─────────────────────────────────────
    disclaimer: "仅为数据可视化 — 不含比赛画面 — 量化模型输出",
    disclaimerShort: "仅为数据可视化 — 非投资建议",
    copyright: "人工智能足球量化终端 v2.0 © 2026 Techspace",
    footerModel: "模型 梯度提升+泊松",

    // ── 半场 ─────────────────────────────────────────────
    halfTimeSummary: "半场汇总",

    // ── 大小球扫描 ───────────────────────────────────────
    ouScanner: "大小球扫描",
    multiLine: "多线扫描",
    lineLabel: "盘口",
    overPct: "大球概率",
    edgeLabel: "优势",

    // ── 总进球引擎 ───────────────────────────────────────
    totalGoalsEngine: "总进球引擎",
    ouTrading: "大小球交易",
    preLambda: "赛前 λ",
    liveLambda: "实时 λ",
    tempoLabel: "节奏",
    expLabel: "（期望值 50）",
    modelProb: "模型概率",
    marketProb: "市场概率",
    edge: "优势",
    signal: "信号",
    nextEvalIn: "下次评估",
    tempoIndex: "节奏指数",
    pressureIndex: "压力指数",
    gameStateFactor: "比赛状态系数",
    redCardFactor: "红牌影响系数",
    ci95: "95%置信区间",

    // ── 信号系统 ─────────────────────────────────────────
    signalCooldown: "信号状态",
    edgeHeat: "边际热度",
    modelCycle: "模型周期",
    nextEval: "下次评估",
    signalControl: "信号控制",
    signalReady: "信号就绪",
    signalConfirmed: "信号已确认",
    confirm: "确认",
    reject: "拒绝",
    monitoring: "监控中",
    edgeBuilding: "优势积累中",
    cooldownLabel: "冷却中",
    locked: "已锁定 — 进入冷却...",
    enterConfirm: "回车 = 确认 | ESC = 拒绝",
    over: "大球",
    under: "小球",
    line: "盘口",
    model: "模型",
    market: "市场",
    best: "最佳",

    // ── 进球窗口 ─────────────────────────────────────────
    goalWindowLabel: "进球窗口",
    highGoalWindow: "高概率进球窗口",
    estimated: "预估",
    confidence: "置信度",
    active: "激活",

    // ── 盘口移动 ─────────────────────────────────────────
    lineMovement: "盘口移动",
    overLabel: "大球：",
    pressureLabel: "压力：",

    // ── 风险面板 ─────────────────────────────────────────
    riskPanel: "风险面板",
    modelVariance: "模型方差",
    signalStability: "信号稳定性",
    marketVolatility: "市场波动性",
    drawdownGuard: "回撤保护",

    // ── 模型周期 ─────────────────────────────────────────
    monitoringState: "监控中",
    evaluatingState: "评估中",
    recalcState: "重算中",
    recalcLambda: "重新计算 λ",
    stateLabel2: "状态：",
    volLabel: "波动：",

    // ── 事件流 / 警报 ────────────────────────────────────
    eventTape: "事件流",
    lastEvents: "最新",
    noEventsYet: "暂无事件",
    goalAlert: "进球",
    redCardAlert: "红牌",
    probSwing: "概率剧变",
    modelRecalc: "模型重算中...",

    // ── 市场边际 ─────────────────────────────────────────
    marketUnavailable: "市场数据不可用",
    odds: "赔率",
    mktImplied: "市场隐含概率",
    edgeAiMkt: "优势（模型-市场）",

    // ── 解释面板 ─────────────────────────────────────────
    whyDelta: "变化原因",
    factorShotsOnTarget: "射正次数",
    factorPressure: "压力指数",
    factorGoal: "进球发生",
    factorRedCard: "红牌事件",
    factorPossession: "控球率",
    factorXgDelta: "期望进球差值",
    factorTimeDecay: "时间衰减",

    // ── 报告横幅 ─────────────────────────────────────────
    ftReportReady: "全场报告就绪",
    htReportReady: "半场报告就绪",
    pressToExport: "— 按 [R] 导出",

    // ── 战绩追踪 ─────────────────────────────────────────
    todayPerformance: "今日战绩",
    signals: "信号",
    wins: "命中",
    losses: "失误",
    roi: "回报率",
    bestEdge: "最佳优势",

    // ── 赛后总结 ─────────────────────────────────────────
    matchSummary: "比赛总结",
    finalScore: "最终比分",
    peakLambda: "峰值 λ",
    avgLambda: "平均 λ",
    bestEdgeLabel: "最佳优势",
    lambdaAccuracy: "λ 精准度",
    updates: "更新次数",
    exportJson: "导出数据",
    preLambdaLabel: "赛前 λ",
    finalGoalsLabel: "最终进球",
    accuracyLabel: "精准度",
    nextEvalAfterCooldown: "冷却结束后进行下次评估",
    multiMatchTerminal: "多场监控终端",

    // ── 语音播报 ─────────────────────────────────────────
    aiSpeaking: "语音播报中...",
    aiReady: "语音就绪",
    broadcastCooldown: "下次",
    stageGoal: "进球",
    stageSignal: "信号",
    stageLatGame: "终局阶段",
    stagePostMatch: "赛后分析",
    stageTempo: "节奏变化",

    // ── 音效 ─────────────────────────────────────────────
    soundEffects: "音效",
    sfxOn: "音效开",
    sfxOff: "音效关",
    soundEnabled: "音效",

    // ── 多场监控 / 投票 ──────────────────────────────────
    multiMatch: "多场监控",
    audienceVote: "观众投票",
    modelVsCrowd: "模型对比观众",
    aligned: "一致",
    diverged: "分歧",
    audiencePoll: "观众投票",
    modelVsAudience: "模型对比观众",
    noActiveMatches: "暂无进行中的比赛",
    votingOpens: "开球后开放投票",
    voteHome: "1  主胜",
    voteDraw: "X  平局",
    voteAway: "2  客胜",
    modelLabel: "模型",
    audienceLabel: "观众",
    basedOnVotes: "基于 {n} 票",
    vs: "对阵",

    // ── 比分矩阵 ─────────────────────────────────────────
    scoreMatrix: "比分矩阵",
    poissonModel: "泊松模型",
    topScores: "最可能比分前三",
    homeAbbr: "主",
    awayAbbr: "客",

    // ── 价值投注 ─────────────────────────────────────────
    valueBet: "价值投注",
    expectedValue: "期望值",
    valueLabel: "价值",

    // ── 预测历史 ─────────────────────────────────────────
    predictionHistory: "预测历史",
    accuracy1x2: "胜平负准确率",
    accuracyOu: "大小球准确率",
    correct: "正确",
    streak: "连续",
    byConfidence: "置信度分组",
    highConf: "高",
    medConf: "中",
    lowConf: "低",
    avgBrier: "平均布莱尔",
    avgConf: "平均置信度",
    lastNGames: "近{n}场",
    totalMatches: "总场数",

    // ── 赛前分析 ─────────────────────────────────────────
    preMatchAnalysis: "赛前分析",
    recommendation1x2: "胜平负推荐",
    recommendationOu: "大小球推荐",
    keyFactors: "关键因素",
    eloAdvantage: "ELO优势",
    eloBalanced: "ELO均衡",
    expectedGoals: "预期进球",
    marketAligned: "市场一致",
    noMarketData: "无市场数据",
    modelSource: "数据源",

    // ── 模型统计（回测）────────────────────────────────────
    modelPerformance: "模型表现",
    backtestResults: "回测结果",
    testPeriod: "测试周期",
    totalSample: "样本总量",
    simulatedRoi: "模拟投资回报",
    roiLabel: "回报率",
    betsPlaced: "下注次数",
    totalStaked: "总投入",
    profit: "利润",
    returned: "回收",
    maxWinStreak: "最长连胜",
    maxLossStreak: "最长连败",
    byLeague: "按联赛",
    matches: "场次",
    accuracy: "准确率",
    meanBrier: "平均布莱尔",
    highConfPredictions: "高置信度",
    medConfPredictions: "中置信度",
    lowConfPredictions: "低置信度",

    // ── 直播状态 ─────────────────────────────────────────
    liveStatus: "直播",
    upcoming: "即将开始",
    signalLabel: "信号",
  },
};
