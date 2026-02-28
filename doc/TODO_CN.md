# AI 足球量化终端 — 功能清单

> 最后更新: 2026-02-28
> 当前版本: v2.2.0
> 状态说明: [x] 已完成 | [ ] 待开发 | [~] 进行中/部分完成

---

## 阶段 0：基础搭建 (v1.0 核心) — 已完成

### 前端搭建
- [x] React 18 + Vite 项目脚手架
- [x] QuantTerminal.jsx（5 层 UI：状态栏/概率/趋势/统计/量化）
- [x] WebSocket hook（useWebSocket.js）
- [x] 中英双语 i18n
- [x] 深色彭博风主题（IBM Plex Mono 等宽字体）
- [x] SVG Sparkline 趋势图
- [x] 字体加载：IBM Plex Mono + 思源黑体（Google Fonts）*(v1.2)*

### 后端搭建
- [x] FastAPI + WebSocket 服务
- [x] Redis 缓存层
- [x] 连接管理器（ws/manager.py）
- [x] 环境变量配置（.env）
- [x] 健康检查接口（/api/health）

### 模型训练（基线版）
- [x] 特征工程（13 个特征：赔率、Elo、统计、xG）
- [x] 模拟数据生成器（3000 场比赛）
- [x] 训练流水线（逻辑回归、XGBoost、校准 XGBoost）
- [x] 模型序列化（joblib .pkl）
- [x] LivePredictor 含泊松赛中修正

### 部署
- [x] Docker Compose（4 个服务：redis、backend、frontend、nginx）
- [x] Dockerfile.backend（Python 3.11-slim）
- [x] Dockerfile.frontend（Node 20-alpine 构建 + nginx 服务）
- [x] Nginx 反向代理（/、/api/、/ws/）
- [x] 本地部署验证通过

---

## 阶段 1：v1.1 生产版 — 已完成

### v1.1 数据协议
- [x] 统一 JSON Schema（10 个区块）
- [x] snake_case 载荷 + 前端 mapPayload.js 映射器
- [x] Meta 区块：数据来源、延迟、健康状态、序列号
- [x] Delta 由后端计算（per-match state）

### v1.1 WebSocket
- [x] 斐波那契退避重连（3s → 5s → 8s → 13s）
- [x] 单实例管理（防止多连接）
- [x] 从 meta.health 追踪健康状态
- [x] 心跳 ping/pong（15 秒间隔）*(v1.2)*
- [ ] Service Worker / IndexedDB 缓存近期事件

### v1.1 新增组件
- [x] EventTape.jsx（进球/红黄牌/换人/VAR 事件流，最新在前）
- [x] MarketEdge.jsx（赔率、隐含概率、Edge AI-MKT 差值）
- [x] ExplainPanel.jsx（Why Δ 概率变化原因，Top 3 因素含影响条）
- [x] ReportBanner.jsx（半场/全场报告通知横幅）

### v1.1 后端引擎
- [x] market_engine.py（隐含概率 + Edge 计算）
- [x] explain_engine.py（驱动 Delta 的关键因素）
- [x] uncertainty_engine.py（CI95 区间、滚动 Brier、锐度、MC 模拟次数）
- [x] match_state.py（单场状态管理）
- [x] QuantEngine 降级方案（ML 模型不可用时）

### v1.1 管理后台
- [x] 管理 REST API（CRUD：增/查/切换/删比赛）
- [x] 管理 HTML 面板（backend/static/admin.html）
- [x] FastAPI 静态文件挂载（/admin/）
- [x] Nginx 代理 /admin 路由

### v1.1 数据源
- [x] The Odds API 客户端（真实 EPL 赔率已接入）
- [x] SportMonks API 客户端（v3，可升级付费版）
- [x] API-Football 客户端（遗留，保留为备选）
- [x] 真实赔率注入 Demo 模式
- [ ] 升级付费方案以获取 EPL 实时数据
- [ ] API 调用频率限制 / 配额追踪

### v1.1 UI 增强
- [x] Meta 状态栏（DELAY/HEALTH/SOURCE）
- [x] 概率区含 Delta 指示器
- [x] 市场 + Edge 区块（Pro 等级）
- [x] 不确定性区块（Elite 等级）
- [x] VOL SPIKE / GOAL WINDOW / DATA STALE 警告徽章 *(v1.2)*
- [ ] 会员等级门控（模糊/锁定 Pro/Elite 内容）

---

## 阶段 1.5：v1.2 λ_live 引擎 — 已完成

### λ_live 总进球 O/U 引擎
- [x] `total_goals_engine.py`：9 阶段公式（τ → Tempo → G → R → λ → 泊松 → 市场校准 → 信号 → 冷却）
- [x] `TotalGoalsPanel.jsx`：彭博风 O/U 面板（Lambda/LINE/Edge/Signal）
- [x] odds_client.py 获取 O/U totals 市场赔率
- [x] QuantTerminal Lambda 趋势标签页（火花图 + 摘要）
- [x] MicroBars 微型条（节奏/压力/波动率）
- [x] 信号系统：SIGNAL/STRONG/HIGH 含冷却倒计时

### 真实数据训练
- [x] 真实比赛数据：23,533 场（6 联赛 × 10 赛季，football-data.co.uk）
- [x] Understat xG 集成：21,030 场（5 联赛，2014-2026）
- [x] 25 特征流水线：Elo、xG、滚动状态、平均赔率
- [x] TimeSeriesSplit 交叉验证（防止数据泄漏）
- [x] 生产模型：逻辑回归 56.57% 准确率、0.9048 LogLoss

### UI 打磨
- [x] WebSocket 心跳 ping/pong（15秒间隔、5秒超时检测）
- [x] 警告徽章（VOL SPIKE / GOAL WINDOW / DATA STALE）
- [x] 字体加载修复（preconnect + stylesheet）
- [x] 版权水印覆盖层
- [x] 数据延迟合规闪烁（最低 30 秒）
- [x] 免责声明栏："DATA VISUALIZATION ONLY"

---

## 阶段 2：v2.0 直播吸粉功能 — 已完成 *(v2.0)*

### O/U 多盘口扫描器
- [x] 扫描多条盘口线：1.5/2.0/2.25/2.5/2.75/3.0/3.5 *(v2.0)*
- [x] 每条线显示 Edge 值 + Active 标记 *(v2.0)*
- [x] 前端 `OUScanner.jsx` 组件 *(v2.0)*
- [x] 后端：`scan_lines()` 为每条线计算泊松 O/U 概率 *(v2.0)*

### 高进球窗口系统
- [x] 高进球窗口检测（tempo_c≥1.15, λ_rate>0.029）*(v2.0)*
- [x] 倒计时横幅含预计持续时间 *(v2.0)*
- [x] 窗口活跃计时器 *(v2.0)*
- [x] 信心百分比 *(v2.0)*
- [x] 前端 `GoalWindow.jsx` + 后端 `goal_window_engine.py` *(v2.0)*

### 信号冷却显示
- [x] 可见冷却倒计时器（180秒/120秒）*(v2.0)*
- [x] "NEXT EVAL IN xx:xx" 显示 *(v2.0)*
- [x] 信号状态进程：MONITORING → BUILDING → READY → COOLDOWN *(v2.0)*
- [x] Edge 构建动画（"EDGE BUILDING..."）*(v2.0)*

### Edge 热度条
- [x] Edge 值的可视化进度条 *(v2.0)*
- [x] 渐变颜色：中性 → 金色 → 亮金 *(v2.0)*
- [x] 4%/6% 阈值标记 *(v2.0)*

### 模型周期计时器
- [x] "NEXT MODEL UPDATE 00:xx" 倒计时 *(v2.0)*
- [x] 当前状态：Monitoring / Evaluating / Recalculating *(v2.0)*
- [x] 波动率等级指示器 *(v2.0)*
- [x] 进球后重算动画（"MODEL RESET — Recalculating λ..."）*(v2.0)*

---

## 阶段 3：v2.0 市场与风险透明 — 已完成 *(v2.0)*

### 盘口移动监控
- [x] 赔率变动监控（线路变化追踪）*(v2.0)*
- [x] 大小球赔率变化追踪 *(v2.0)*
- [x] 市场压力指示器（OVER/UNDER/NEUTRAL 方向）*(v2.0)*
- [x] 前端 `LineMovement.jsx` 组件 *(v2.0)*

### 风险面板
- [x] 模型方差展示 *(v2.0)*
- [x] 信号稳定性百分比（10 样本滚动）*(v2.0)*
- [x] 市场波动率等级（低/中/高）*(v2.0)*
- [x] 最大回撤守卫状态 *(v2.0)*
- [x] 前端 `RiskPanel.jsx` + 后端 `risk_engine.py` *(v2.0)*

### 赛前 vs 实时对比
- [x] PRE λ → LIVE λ 含 Δ 百分比变化 *(v2.3)*
- [x] TEMPO vs EXP 50 含 Δ 百分比 *(v2.3)*
- [x] 集成到 TotalGoalsPanel 顶部（紧凑 16px 行）*(v2.3)*

### 市场压力指数
- [x] 市场压力指示器集成到 LineMovement *(v2.0)*
- [x] 方向：OVER / UNDER / NEUTRAL *(v2.0)*
- [x] 从赔率移动方向推导 *(v2.0)*

---

## 阶段 4：v2.0 信号控制与战绩 — 已完成 *(v2.1)*

### 信号控制面板（半自动模式）
- [x] SIGNAL READY 展示含盘口/模型/市场/边际 *(v2.1)*
- [x] [CONFIRM] / [REJECT] 按钮（Enter/Escape 键盘快捷键）*(v2.1)*
- [x] 信号状态机：idle → ready → confirmed → cooldown *(v2.1)*
- [x] 确认后信号锁定（120秒冷却）*(v2.1)*
- [x] 确认时触发 AI 播报 *(v2.2)*
- [x] 前端 `SignalControlPanel.jsx` 组件 *(v2.1)*
- [x] 后端 `POST /api/signal/confirm` + `GET /api/signal/state` *(v2.1)*

### 战绩追踪面板
- [x] 今日信号数、命中数、失误数 *(v2.1)*
- [x] ROI 百分比展示 *(v2.1)*
- [x] 信号日志含结果标记（✓/✗/●）*(v2.1)*
- [x] 角落固定展示（始终可见）*(v2.1)*
- [x] 前端 `TrackRecord.jsx` 组件 *(v2.1)*
- [x] 后端 `performance_tracker.py` + `GET /api/performance` *(v2.1)*

### 赛后总结
- [x] 比赛结束自动生成总结（minute≥90）*(v2.1)*
- [x] 字段：Pre λ、最终进球、Peak λ、最佳 Edge、λ 准确度 *(v2.1)*
- [x] POST-MATCH 场景触发 *(v2.1)*
- [x] EXPORT JSON 导出按钮（match_summary_YYYY-MM-DD_HH-MM.json）*(v2.3)*
- [x] 前端 `PostMatchSummary.jsx` 组件 *(v2.1)*
- [x] 后端 `post_match_engine.py` *(v2.1)*

---

## 阶段 5：v2.0 AI 语音解说 — 已完成 *(v2.2)*

### TTS 引擎集成
- [x] Edge TTS（en-US-GuyNeural / zh-CN-YunxiNeural），-10% 语速 *(v2.2)*
- [x] 声音风格：男声、低沉、0.9x 语速 *(v2.2)*
- [x] 中英双语模板——10 阶段脚本各含 2 个变体 *(v2.2)*
- [x] `POST /announce` 接口——返回 MP3 音频字节 *(v2.2)*

### 半自动播报流程
- [x] 系统检测到 Edge≥4% → SIGNAL PENDING（AI："检测到潜在机会"）*(v2.2)*
- [x] 用户确认 → SIGNAL CONFIRMED（AI：Stage 5 正式播报）*(v2.2)*
- [x] 进球 → 自动播报（AI："进球，正在重算..."）——critical 优先级 *(v2.2)*
- [x] 赛后 → 自动总结播报（Stage 10，minute≥90）*(v2.2)*

### 触发规则与冷却
- [x] λ_total 变化 > 8%："模型波动显著" *(v2.2)*
- [x] Edge > 4%："边际建立中"（SIGNAL_PENDING）*(v2.2)*
- [x] Edge > 6%：正式信号（确认后 SIGNAL_CONFIRM）*(v2.2)*
- [x] Tempo > 70："高节奏区间" *(v2.2)*
- [x] 进球 / 红牌：critical 必触发 *(v2.2)*
- [x] 每 90 秒最多一次非重大播报 *(v2.2)*
- [x] 进球后冷却 60 秒，红牌后冷却 30 秒 *(v2.2)*

### UI-语音同步
- [x] AI 提及面板时该面板高亮（0.8秒发光）—— `useVoiceHighlight.js` *(v2.2)*
- [x] "AI SPEAKING..." 指示器（右上角）—— `AISpeakingIndicator.jsx` *(v2.2)*
- [x] Late Game 模式播报（60分钟后）+ Final Window（80分钟后）*(v2.2)*

### 10 阶段脚本模板
- [x] 第1阶段：赛前开场 *(v2.2)*
- [x] 第2阶段：开球监控 *(v2.2)*
- [x] 第3阶段：节奏累积（15-35分钟）*(v2.2)*
- [x] 第4阶段：信号准备（悬念）*(v2.2)*
- [x] 第5阶段：信号确认 *(v2.2)*
- [x] 第6阶段：信号锁定 + 冷却 *(v2.2)*
- [x] 第7阶段：进球触发 + 重算 *(v2.2)*
- [x] 第8阶段：下半场后段（60分钟后）*(v2.2)*
- [x] 第9阶段：终局阶段（80分钟后）*(v2.2)*
- [x] 第10阶段：赛后总结 *(v2.2)*

---

## 阶段 6：v2.0 OBS 场景集成 — 已完成 *(v2.3)*

### 4 场景结构
- [x] 场景1：PRE-MATCH（开球倒计时）*(v2.3)*
- [x] 场景2：LIVE TRADING（主场景，占 90% 时间）*(v2.3)*
- [x] 场景3：SIGNAL FOCUS（信号放大，确认后 5-10秒）*(v2.3)*
- [x] 场景4：POST-MATCH SUMMARY（赛后总结）*(v2.3)*

### OBS 图层结构
- [x] 6 层结构文档（背景→终端→信号→AI状态→战绩→免责）*(v2.3)*

### OBS 配置
- [x] 快捷键映射：F1=信号、F2=直播、F3=总结、F4=TTS *(v2.3)*
- [x] 输出：1080p 30fps、6000kbps、关键帧 2s *(v2.3)*
- [x] YouTube RTMPS 推流指南 *(v2.3)*
- [x] Browser Source 设置文档 *(v2.3)*
- [x] `doc/OBS_SETUP.md` 完整配置指南 *(v2.3)*

### 直播增强
- [x] 系统在线指示灯（绿色脉冲 + "SYSTEM ONLINE"，断连时红色）*(v2.3)*
- [x] 模型版本号显示（"MODEL v2.2"）*(v2.3)*
- [x] 音频设置文档（TTS -3dB、环境音 -28dB）*(v2.3)*

---

## 阶段 7：高级功能 — 已完成 *(v2.3)*

### 关键事件警报系统
- [x] 进球：全屏金色闪烁 2.5 秒 *(v2.1)*
- [x] 红牌：全屏红色闪烁 2 秒 *(v2.1)*
- [x] 概率剧变 > 15%：全屏青色闪烁 3 秒 *(v2.1)*
- [x] `EventAlert.jsx` + `useEventAlert.js` 含顺序队列 *(v2.1)*
- [x] Web Audio API 音效触发（进球/红牌/信号）`useSoundEffects.js` *(v2.3)*

### 蒙特卡洛比分矩阵
- [x] 基于泊松分布的精确比分概率矩阵（6×6，0-5 球）*(v2.3)*
- [x] 热力图可视化（金色透明度缩放，最大概率金色发光）*(v2.3)*
- [x] 最可能比分展示（Top 3）*(v2.3)*
- [x] 前端 `ScoreMatrix.jsx` + 后端 `score_matrix_engine.py` *(v2.3)*

### 多场比赛并行终端
- [x] 响应式网格布局（auto-fill，3-4 场）*(v2.3)*
- [x] 单场紧凑卡片（状态灯、比分、λ/edge/signal）*(v2.3)*
- [x] 前端 `MatchGrid.jsx` 组件（独立，数据驱动）*(v2.3)*
- [ ] 每场独立 WebSocket 连接（后端多场支持）

### 弹幕投票系统
- [x] 前端 `VotePanel.jsx`（1/X/2 投票条，模型 vs 观众，分歧高亮）*(v2.3)*
- [x] 模型 vs 观众对比，分歧 >10% 显示徽章 *(v2.3)*
- [ ] YouTube 直播弹幕 API 读取（后端）
- [ ] TikTok/抖音 直播连接器（后端）
- [ ] 投票解析（1/X/2）+ 实时聚合（后端）

### 音效设计
- [x] 进球：彭博 3 音符琶音（C5-E5-G5）*(v2.3)*
- [x] 红牌：警报双蜂鸣（400Hz 方波）*(v2.3)*
- [x] 概率剧变：上升频率扫描（800→1600Hz）*(v2.3)*
- [x] 半场：交易所收盘钟声（800Hz 正弦，600ms）*(v2.3)*
- [x] 模型重算："叮"（1200Hz，150ms）*(v2.3)*
- [x] 信号确认：双音（E5-G5）*(v2.3)*
- [x] `useSoundEffects.js` Web Audio API hook——无外部文件 *(v2.3)*

### 价值投注扫描器（EV）
- [x] 模型 vs 市场 Edge 检测含 EV 计算 *(v2.3)*
- [x] 每 $1 期望收益（OVER/UNDER）*(v2.3)*
- [x] 信心等级（LOW/MED/HIGH/STRONG）*(v2.3)*
- [x] 前端 `ValueBetScanner.jsx` + 后端 `compute_value_bet()` *(v2.3)*

---

## 阶段 8：变现与运营

### 会员分层
- [ ] Free：1X2 概率、基础统计、3 条事件、趋势图
- [ ] Pro（$9.99/月）：市场/Edge、Explain、完整事件流、量化指标
- [ ] Elite（$29.99/月）：不确定性、多场终端、报告导出、历史回放
- [ ] 支付集成（Stripe / Paddle）
- [ ] 认证系统（JWT/Session）
- [ ] 内容模糊/门控

### 云端部署
- [ ] 云服务器搭建（AWS/DO/阿里云）
- [ ] SSL 证书（Let's Encrypt）
- [ ] 域名配置
- [ ] CI/CD 流水线
- [ ] 监控与告警

---

## 模型训练改进

### 数据质量
- [x] 用 football-data.co.uk 真实 CSV 替换模拟数据 *(v1.2)*
- [x] 增加西甲、德甲、意甲、法甲数据 *(v1.2)*
- [x] 集成 Understat xG 数据用于训练 *(v1.2)*
- [x] 新增特征：近 5 场滚动统计 *(v1.2)*
- [ ] 新增特征：历史交锋记录（H2H）

### 模型架构
- [x] Brier Score + LogLoss 评估 *(v1.2)*
- [ ] 校准曲线分析
- [x] 特征重要性分析与筛选 *(v1.2)*
- [ ] 超参数调优（Optuna/GridSearch）
- [ ] 集成模型：XGBoost + LightGBM + 逻辑回归 加权融合
- [x] 基于时间的交叉验证（防止数据泄漏）*(v1.2)*

### 赛中修正
- [x] λ_live 引擎改进泊松修正 *(v1.2)*
- [ ] 赛中特征更新（射门、控球率、xG 差值）
- [x] 红牌影响模型（total_goals_engine R_c 因子）*(v1.2)*
- [ ] 换人影响追踪
- [ ] 天气/裁判偏差因素

### 持续学习
- [ ] 赛后结果自动采集流水线
- [ ] 每周模型自动重训练
- [ ] A/B 模型对比框架
- [ ] 模型版本追踪（MLflow 或简单 JSON 日志）

---

## 技术债务与打磨

- [x] 版权合规：添加 "DATA VISUALIZATION ONLY" 水印 *(v1.2)*
- [x] 数据延迟展示（合规要求最低 30 秒）*(v1.2)*
- [ ] 修复 sklearn 版本不匹配警告
- [ ] 增加完善的 API 失败错误处理
- [ ] 增加日志（结构化 JSON 日志）
- [ ] 引擎单元测试（market、explain、uncertainty、total_goals）
- [ ] WebSocket 载荷 Schema 集成测试
- [ ] 前端响应式布局（移动端适配）
- [ ] 无障碍访问（键盘导航、ARIA 标签）
- [ ] API 频率限制中间件
- [ ] Redis 持久化配置
