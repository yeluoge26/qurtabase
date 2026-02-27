# AI 足球量化终端 — 功能清单

> 最后更新: 2026-02-27
> 当前版本: v1.2.0
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

## 阶段 2：v2.0 直播吸粉功能 — P0 必做

### O/U 多盘口扫描器
- [ ] 扫描多条盘口线：2.0 / 2.25 / 2.5 / 2.75
- [ ] 每条线显示 Edge 值 + Active 标记
- [ ] 前端 `OUScanner.jsx` 组件
- [ ] 后端：为每条线计算泊松 O/U 概率

### 高进球窗口系统
- [ ] 高进球窗口检测（节奏 + xG 速度阈值）
- [ ] 倒计时横幅："HIGH GOAL WINDOW — 预计 5-10 分钟"
- [ ] 窗口活跃计时器
- [ ] 信心百分比
- [ ] 前端 `GoalWindow.jsx` 组件

### 信号冷却显示
- [ ] 可见冷却倒计时器（180秒/120秒）
- [ ] "NEXT EVAL IN xx:xx" 显示
- [ ] 信号状态进程：BUILDING → READY → CONFIRMED → COOLDOWN
- [ ] Edge 构建动画（"EDGE BUILDING..."）

### Edge 热度条
- [ ] Edge 值的可视化进度条（不仅是数字）
- [ ] 渐变颜色：中性 → 金色 → 亮金
- [ ] 阈值标记

### 模型周期计时器
- [ ] "NEXT MODEL UPDATE 00:xx" 倒计时
- [ ] 当前状态：Monitoring / Evaluating / Recalculating
- [ ] 波动率等级指示器
- [ ] 进球后重算动画（"MODEL RESET — Recalculating λ..."）

---

## 阶段 3：v2.0 市场与风险透明 — P1

### 盘口移动监控
- [ ] 赔率变动监控（如 2.5 → 2.25）
- [ ] 大小球赔率变化追踪
- [ ] 市场压力指示器（OVER/UNDER 方向箭头）
- [ ] 前端 `LineMovement.jsx` 组件

### 风险面板
- [ ] 模型方差展示
- [ ] 信号稳定性百分比
- [ ] 市场波动率等级（低/中/高）
- [ ] 最大回撤守卫状态
- [ ] 前端 `RiskPanel.jsx` 组件

### 赛前 vs 实时对比
- [ ] PRE TOTAL λ vs LIVE TOTAL λ 含百分比变化
- [ ] TEMPO vs EXPECTED 对比
- [ ] 集成到 TotalGoalsPanel 顶部

### 市场压力指数
- [ ] PUBLIC BIAS / MARKET PRESSURE 指示器
- [ ] 方向：OVER / UNDER / NEUTRAL
- [ ] 从赔率移动方向推导

---

## 阶段 4：v2.0 信号控制与战绩 — P2

### 信号控制面板（半自动模式）
- [ ] SIGNAL READY 展示含盘口/模型/市场/边际
- [ ] [CONFIRM] / [REJECT] 按钮（支持键盘快捷键）
- [ ] 信号状态机：ready → pending → confirmed → cooldown
- [ ] 确认后信号锁定
- [ ] 确认时触发 AI 播报
- [ ] 前端 `SignalControlPanel.jsx` 组件
- [ ] 后端信号状态接口

### 战绩追踪面板
- [ ] 今日信号数、命中数、失误数
- [ ] ROI 百分比展示
- [ ] 历史预测数据库（match_id、预测值、实际结果）
- [ ] 角落固定展示（始终可见）
- [ ] 前端 `TrackRecord.jsx` 组件
- [ ] 后端 `/api/performance` 接口

### 赛后总结
- [ ] 比赛结束自动生成总结
- [ ] 字段：Pre λ、最终进球、Peak λ、最佳 Edge、信号准确度
- [ ] POST-MATCH 场景触发
- [ ] 导出功能（JSON / 图片快照）
- [ ] 前端 `PostMatchSummary.jsx` 组件

---

## 阶段 5：v2.0 AI 语音解说 — P3

### TTS 引擎集成
- [ ] Edge TTS / OpenAI TTS / ElevenLabs / CosyVoice 支持
- [ ] 声音风格：男声、低沉、0.9x 语速、轻微房间混响
- [ ] 中英双语模板
- [ ] `POST /announce` TTS 触发接口

### 半自动播报流程
- [ ] 系统检测到 Edge → SIGNAL PENDING（AI："检测到潜在机会"）
- [ ] 用户确认 → SIGNAL CONFIRMED（AI：正式播报）
- [ ] 进球 → 自动播报（AI："进球出现，正在重算..."）
- [ ] 赛后 → 自动总结播报

### 触发规则与冷却
- [ ] λ_total 变化 > 8%："模型波动显著"
- [ ] Edge > 4%："边际建立中"
- [ ] Edge > 6%：正式信号
- [ ] Tempo > 70："比赛进入高节奏区间"
- [ ] 进球 / 红牌：必触发
- [ ] 每 90 秒最多一次非重大播报
- [ ] 进球后冷却 60 秒

### UI-语音同步
- [ ] AI 提及面板时该面板高亮（0.8秒发光）
- [ ] "AI SPEAKING..." 指示器（右上角）
- [ ] Late Game 模式播报（70分钟后）

### 10 阶段脚本模板
- [ ] 第1阶段：赛前开场
- [ ] 第2阶段：开球监控
- [ ] 第3阶段：节奏累积（15-35分钟）
- [ ] 第4阶段：信号准备（悬念）
- [ ] 第5阶段：信号确认
- [ ] 第6阶段：信号锁定 + 冷却
- [ ] 第7阶段：进球触发 + 重算
- [ ] 第8阶段：下半场后段（60分钟后）
- [ ] 第9阶段：终局阶段（80分钟后）
- [ ] 第10阶段：赛后总结

---

## 阶段 6：v2.0 OBS 场景集成 — P4

### 4 场景结构
- [ ] 场景1：PRE-MATCH（赛前预热，开球倒计时）
- [ ] 场景2：LIVE TRADING（主场景，占 90% 时间）
- [ ] 场景3：SIGNAL FOCUS（信号放大，确认后持续 5-10秒）
- [ ] 场景4：POST-MATCH SUMMARY（赛后总结）

### OBS 图层结构
- [ ] 图层1：背景层（#0E1117 颜色源）
- [ ] 图层2：主终端（Browser Source 1920x1080）
- [ ] 图层3：信号覆盖层（独立浏览器源，6秒淡出）
- [ ] 图层4：AI 语音状态条（"AI SPEAKING..."）
- [ ] 图层5：今日战绩面板（固定右下角）
- [ ] 图层6：免责声明条（固定底部 20px）

### OBS 配置
- [ ] 快捷键映射：F1=信号、F2=直播、F3=总结、F4=TTS
- [ ] 输出：1080p 30fps、6000kbps、关键帧 2s
- [ ] YouTube RTMPS 推流测试
- [ ] Browser Source：不可见时关闭、场景激活时刷新

### 直播增强
- [ ] 系统在线指示灯（绿色圆点，左上角）
- [ ] 模型版本号显示（如 "MODEL v2.3"）
- [ ] 音频：TTS -3dB、环境音 -28dB

---

## 阶段 7：高级功能 — P5（第3月以后）

### 关键事件警报系统
- [ ] 进球：状态栏闪黄 2 秒
- [ ] 红牌：状态栏闪红
- [ ] 概率剧变 > 15%：全屏 ALERT 横幅
- [ ] OBS WebSocket 通知触发音效

### 蒙特卡洛比分矩阵
- [ ] 基于泊松分布的精确比分概率矩阵
- [ ] 热力图可视化（颜色深浅编码）
- [ ] 最可能比分展示（Top 3）
- [ ] 前端 `ScoreMatrix.jsx` 组件

### 多场比赛并行终端
- [ ] 网格布局（3-4 场并列）
- [ ] 单场紧凑卡片
- [ ] 每场独立 WebSocket 连接
- [ ] 前端 `MatchGrid.jsx` 组件

### 弹幕投票系统
- [ ] YouTube 直播弹幕 API 读取
- [ ] TikTok/抖音 直播连接器
- [ ] 投票解析（1/X/2）+ 实时聚合
- [ ] 模型 vs 观众对比
- [ ] 前端 `VotePanel.jsx` 组件

### 音效设计
- [ ] 进球：彭博交易执行音
- [ ] 红牌：警报蜂鸣
- [ ] 概率剧变 > 15%：涨停提示音
- [ ] 半场：交易所收盘钟声
- [ ] 模型重算完成：清脆的"叮"

### 价值投注扫描器（EV）
- [ ] 模型 vs 市场 Edge 检测（阈值 +5%）
- [ ] 每 $1 期望收益计算
- [ ] 信心等级（低/中/高/强）

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
