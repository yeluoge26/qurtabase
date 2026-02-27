# AI 足球量化终端 — 架构文档

> 版本: 1.1 | 2026-02-27

---

## 系统架构总览

```
                         ┌─────────────────────┐
                         │   YouTube / TikTok   │
                         │     直播推流          │
                         └─────────┬───────────┘
                                   │ RTMPS
                         ┌─────────┴───────────┐
                         │    OBS Studio        │
                         │  Browser Source       │
                         │  1920x1080 / 30fps   │
                         └─────────┬───────────┘
                                   │ http://localhost
                                   │
    ┌──────────────────────────────┼──────────────────────────────┐
    │                        Nginx :80                            │
    │                    （反向代理）                               │
    │                                                             │
    │  /           → 前端 :80  (React SPA)                       │
    │  /api/*      → 后端 :8000 (REST API)                       │
    │  /ws/*       → 后端 :8000 (WebSocket 升级)                  │
    │  /admin/*    → 后端 :8000 (静态文件)                        │
    └───────┬──────────────────────┬──────────────────────────────┘
            │                      │
   ┌────────┴────────┐    ┌───────┴─────────────────────────────┐
   │   前端            │    │           后端                       │
   │   React 18       │    │           FastAPI                    │
   │   + Vite         │    │                                     │
   │                  │    │  ┌─────────┐  ┌──────────────────┐ │
   │  组件：           │    │  │  管理    │  │  WebSocket       │ │
   │  QuantTerminal   │    │  │  API     │  │  管理器           │ │
   │  EventTape       │    │  │  (CRUD)  │  │  （广播）         │ │
   │  MarketEdge      │    │  └────┬────┘  └───────┬──────────┘ │
   │  ExplainPanel    │    │       │               │             │
   │  ReportBanner    │    │  ┌────┴───────────────┴──────────┐ │
   │                  │    │  │       引擎流水线                 │ │
   │  Hooks：          │    │  │                                │ │
   │  useWebSocket    │    │  │  LivePredictor (XGBoost)       │ │
   │                  │    │  │  → MarketEngine（市场引擎）      │ │
   │  工具：           │    │  │  → ExplainEngine（解释引擎）    │ │
   │  mapPayload      │    │  │  → UncertaintyEngine（不确定性）│ │
   │  i18n            │    │  │  → QuantEngine（量化引擎）      │ │
   │                  │    │  │  → MatchStateStore（状态存储）   │ │
   │  产出：           │    │  └──────────┬─────────────────────┘ │
   │  dist/ (nginx)   │    │             │                       │
   └──────────────────┘    │  ┌──────────┴─────────────────────┐ │
                           │  │       数据客户端                  │ │
                           │  │                                │ │
                           │  │  AllSportsClient（主数据源）     │ │
                           │  │  SportMonksClient (v3 API)     │ │
                           │  │  FootballAPIClient（备选）       │ │
                           │  │  OddsAPIClient (The Odds API)  │ │
                           │  │  CacheManager（内存缓存）        │ │
                           │  └──────────┬─────────────────────┘ │
                           └─────────────┼───────────────────────┘
                                         │
                ┌────────────────────────┼───────────────────────┐
                │                        │                       │
     ┌──────────┴──────────┐  ┌─────────┴────────┐  ┌──────────┴──────────┐
     │  AllSportsApi       │  │  The Odds API     │  │   Redis :6379       │
     │  （实时数据）         │  │  （投注赔率）      │  │   （缓存 + 未来      │
     │                     │  │                   │  │    PubSub）          │
     │   免费版：           │  │   已激活：          │  │                    │
     │   加纳 + 立陶宛      │  │   EPL 真实赔率     │  │   存储内容：         │
     │                     │  │   20 个事件        │  │   - API 响应缓存    │
     │   付费版：           │  │                   │  │   - 比赛状态        │
     │   EPL + 全部联赛     │  │                   │  │   - 会话数据        │
     └────────────────────┘  └───────────────────┘  └───────────────────┘
```

---

## 数据流图

```
                    外部数据源
                    =========

    ┌──────────────┐   ┌──────────────┐   ┌──────────────┐
    │  AllSportsApi │   │  The Odds    │   │  football-   │
    │  实时 API      │   │  API         │   │  data.co.uk  │
    │  （30秒轮询）  │   │  （60秒轮询） │   │  （训练数据） │
    └──────┬───────┘   └──────┬───────┘   └──────┬───────┘
           │                  │                   │
           ▼                  ▼                   ▼
    ┌──────────────────────────────┐      ┌──────────────┐
    │      后端处理流水线            │      │   训练流水线   │
    │                              │      │              │
    │  1. 获取原始数据              │      │  features.py │
    │  2. 解析统计/事件             │      │  train.py    │
    │  3. 构建特征向量              │      │  → .pkl      │
    │  4. XGBoost predict_proba   │      └──────────────┘
    │  5. 泊松分布赛中修正          │
    │  6. 市场隐含概率 + Edge      │
    │  7. 解释 Top 因素            │
    │  8. 不确定性 CI95/Brier     │
    │  9. 比赛状态 Delta 计算      │
    │  10. 组装 v1.1 JSON 载荷    │
    └──────────────┬───────────────┘
                   │
                   ▼ WebSocket 推送（每 2 秒）
    ┌──────────────────────────────┐
    │      v1.1 JSON 载荷           │
    │                              │
    │  {                           │
    │    meta: { 健康状态, 序列号 }  │
    │    match: { 比分, 分钟 }      │
    │    probability: { 主/平/客 }  │
    │    market: { 赔率, Edge }    │
    │    stats: { 射门, xG... }    │
    │    events: [ ... ]           │
    │    quant: { 压力指数... }     │
    │    uncertainty: { CI95 }     │
    │    explain: { 因素 }          │
    │    report: { 半场/全场 }      │
    │  }                           │
    └──────────────┬───────────────┘
                   │
                   ▼ mapPayload.js
    ┌──────────────────────────────┐
    │      前端渲染                  │
    │                              │
    │  ┌───────────────────────┐  │
    │  │ 状态栏（meta）          │  │
    │  ├───────────────────────┤  │
    │  │ 概率 + Delta           │  │
    │  │ 市场 Edge（Pro）       │  │
    │  │ 解释面板（Pro）         │  │
    │  ├───────────────────────┤  │
    │  │ 趋势 Sparkline        │  │
    │  ├───────────────────────┤  │
    │  │ 统计 + 事件流          │  │
    │  ├───────────────────────┤  │
    │  │ 量化指标               │  │
    │  │ 不确定性（Elite）      │  │
    │  └───────────────────────┘  │
    │                              │
    │  1920 x 1080 彭博风格 UI     │
    └──────────────────────────────┘
```

---

## 文件结构

```
e:\code\qurtabase\
│
├── doc/
│   ├── implementation-guide.md      # 原始 v1.0 开发指南
│   ├── v1.1 implement.txt          # v1.1 升级规格说明
│   ├── feature-roadmap.md          # 功能路线图（P0-P3）
│   ├── PRD.md / PRD_CN.md         # 产品需求文档（英/中）
│   ├── ARCHITECTURE.md / _CN.md   # 架构文档（英/中）
│   ├── TODO.md / TODO_CN.md       # 功能清单（英/中）
│   └── MODEL-TRAINING.md / _CN.md # 模型训练指南（英/中）
│
├── frontend/                        # React 18 + Vite
│   ├── package.json
│   ├── vite.config.js               # 开发代理：/api, /ws → localhost:8000
│   ├── index.html
│   └── src/
│       ├── main.jsx                 # React 入口
│       ├── App.jsx                  # 比赛选择 → QuantTerminal
│       ├── QuantTerminal.jsx        # 主终端（5 层 UI）
│       ├── hooks/
│       │   └── useWebSocket.js      # 含斐波那契退避的 WebSocket Hook
│       ├── utils/
│       │   ├── mapPayload.js        # snake_case → camelCase 映射器
│       │   └── i18n.js              # 中英双语翻译
│       └── components/
│           ├── EventTape.jsx        # 比赛事件日志
│           ├── MarketEdge.jsx       # 赔率 + 隐含概率 + Edge
│           ├── ExplainPanel.jsx     # Why Δ（Top 3 因素）
│           └── ReportBanner.jsx     # 半场/全场报告通知
│
├── backend/                         # FastAPI Python 后端
│   ├── main.py                      # 应用入口：WS、管理 API、Demo、Live
│   ├── config.py                    # 配置（环境变量、API 密钥）
│   ├── requirements.txt
│   ├── data/
│   │   ├── allsports_client.py     # AllSportsApi（主数据源）
│   │   ├── sportmonks_client.py    # SportMonks v3 API（备选）
│   │   ├── api_client.py           # API-Football（备选）
│   │   ├── odds_client.py          # The Odds API（赔率数据）
│   │   └── cache.py                # 内存缓存 + 可选 Redis 缓存
│   ├── models/
│   │   ├── predictor.py            # LivePredictor（XGBoost + 泊松修正）
│   │   ├── quant.py                # QuantEngine（降级方案）
│   │   └── trained/
│   │       ├── model_calibrated.pkl # 生产模型
│   │       ├── model_xgb.pkl       # XGBoost 原始模型
│   │       ├── model_logistic.pkl  # 逻辑回归基线
│   │       └── model_meta.json     # 特征名称、类别映射
│   ├── services/
│   │   ├── market_engine.py        # 隐含概率 + Edge 计算
│   │   ├── explain_engine.py       # 概率 Delta 的关键因素
│   │   └── uncertainty_engine.py   # CI95、滚动 Brier、锐度
│   ├── store/
│   │   └── match_state.py          # 单场状态（Delta、事件、Brier）
│   ├── ws/
│   │   └── manager.py              # WebSocket 连接管理器
│   ├── static/
│   │   ├── index.html              # 管理面板（/admin/ 访问）
│   │   └── admin.html              # 管理面板（原始文件）
│   └── training/
│       ├── train.py                # 3 模型对比训练流水线
│       ├── features.py             # 特征工程（13 个特征）
│       ├── generate_data.py        # 模拟数据生成器
│       └── data/
│           └── matches.csv         # 训练数据（3000 场模拟）
│
├── model/                           # 原始模型原型
│   ├── features.py
│   ├── predictor.py
│   ├── train.py
│   ├── generate_data.py
│   └── model_meta.json
│
├── jsx/
│   └── quant-terminal.jsx          # 原始 React 原型
│
├── docker-compose.yml              # 4 个服务：redis、backend、frontend、nginx
├── Dockerfile.backend              # Python 3.11-slim
├── Dockerfile.frontend             # Node 20-alpine 构建 + nginx 服务
├── nginx.conf                      # 反向代理配置
├── .env                            # API 密钥（不提交到仓库）
├── .env.example                    # API 密钥模板
└── .gitignore
```

---

## 引擎流水线详细图

```
                输入：原始实时数据 + 赔率
                           │
                ┌──────────┴──────────┐
                │   LivePredictor     │
                │                     │
                │  1. build_features  │  13 个特征 → numpy 数组
                │  2. model.predict   │  XGBoost → [P(客), P(平), P(主)]
                │  3. poisson_update  │  比分 + 时间 → 修正后概率
                │  4. compute_quant   │  压力、动量、波动率
                │                     │
                │  输出：              │
                │  probability{}      │  主胜/平局/客胜 概率
                │  quant{}            │  7 个量化指标
                └──────────┬──────────┘
                           │
         ┌─────────────────┼─────────────────┐
         │                 │                 │
  ┌──────┴──────┐  ┌──────┴──────┐  ┌──────┴──────┐
  │ 市场引擎     │  │ 解释引擎     │  │ 不确定性    │
  │ Market      │  │ Explain     │  │ 引擎        │
  │             │  │             │  │ Uncertainty │
  │ 赔率 →      │  │ 当前 vs 上次 │  │ 概率 →      │
  │ 隐含概率    │  │ 状态差异     │  │ CI95 区间   │
  │ Edge =      │  │ → Top 3     │  │ Brier 分数  │
  │ AI - 市场   │  │   因素       │  │ 锐度        │
  │             │  │   + 摘要     │  │ MC 模拟次数 │
  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘
         │                │                 │
         └─────────────────┼─────────────────┘
                           │
                ┌──────────┴──────────┐
                │  MatchStateStore    │
                │  比赛状态存储        │
                │                     │
                │  - last_probability │  → Delta 计算
                │  - event_ids set    │  → 事件去重
                │  - brier_buffer[]   │  → 滚动窗口
                │  - last_update_ts   │  → 健康状态检测
                │  - seq counter      │  → 消息排序
                └──────────┬──────────┘
                           │
                           ▼
                   v1.1 JSON 载荷
                   （10 个区块，约 2KB）
                           │
                           ▼
                   WebSocket 广播
                   （每 2 秒推送一次）
```

---

## Docker Compose 拓扑图

```
  ┌────────────────────────────────────────────────────────────┐
  │                    Docker 网络                               │
  │                                                            │
  │  ┌──────────┐    ┌──────────────┐    ┌──────────────────┐ │
  │  │  Redis    │    │   后端        │    │    前端           │ │
  │  │  :6379    │◄───│   :8000     │    │    :80 (nginx)   │ │
  │  │          │    │              │    │                  │ │
  │  │  alpine  │    │  python:3.11 │    │  node:20 构建    │ │
  │  │  7-alpine│    │  FastAPI     │    │  + nginx:alpine │ │
  │  └──────────┘    │  uvicorn     │    └────────┬────────┘ │
  │                  │              │              │          │
  │                  │  挂载卷：     │              │          │
  │                  │  ./models/   │              │          │
  │                  │   trained/   │              │          │
  │                  └──────┬───────┘              │          │
  │                         │                      │          │
  │                  ┌──────┴──────────────────────┴────────┐ │
  │                  │         Nginx  :80 / :443            │ │
  │                  │         （反向代理）                   │ │
  │                  │                                     │ │
  │                  │  /        → frontend:80（前端）      │ │
  │                  │  /api/*   → backend:8000（REST）     │ │
  │                  │  /ws/*    → backend:8000（WS 升级）  │ │
  │                  │  /admin/* → backend:8000（静态文件）  │ │
  │                  └─────────────────────────────────────┘ │
  │                                                            │
  └────────────────────────────────────────────────────────────┘
                              │
                     暴露端口：
                     80   → Nginx（主入口）
                     443  → Nginx（HTTPS，未来）
                     8000 → 后端（直连）
                     5173 → 前端（直连）
                     6379 → Redis（直连）
```

---

## 模式选择逻辑

```
启动：
  │
  ├── ALLSPORTS_API_KEY 已配置？
  │     ├── 是 → 模式: LIVE，数据源: AllSportsApi
  │     └── 否 ──┐
  │              │
  │              ├── SPORTMONKS_API_KEY 已配置？
  │              │     ├── 是 → 模式: LIVE，数据源: SportMonks
  │              │     └── 否 ──┐
  │              │              │
  │              │              ├── FOOTBALL_API_KEY 已配置？
  │              │              │     ├── 是 → 模式: LIVE，数据源: API-Football
  │              │              │     └── 否 → 模式: DEMO（模拟比赛数据）
  │
  ├── ODDS_API_KEY 已配置？
  │     ├── 是 → 注入真实赔率（DEMO 模式下同样生效）
  │     └── 否 → 使用模拟赔率
  │
  └── 比赛请求 (ws/{match_id})：
        │
        ├── match_id == "demo" → 始终使用 Demo 模拟器
        │     └── + 如果配置了 ODDS_API_KEY 则注入真实赔率
        │
        └── match_id == 其他 → 如有 API 密钥则使用 Live 模式
              └── API 失败时回退到 Demo 模式
```
