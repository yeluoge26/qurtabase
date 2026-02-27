# AI Football Quant Terminal — 完整实施指南
## Implementation Guide: From JSX Prototype to Production

---

## 一、总览 Overview

你现在有的：`quant-terminal.jsx` — 一个 React 原型，使用模拟数据。

你需要做的：

```
原型 (JSX)
  → 独立 React 项目
    → 接入真实比赛数据 API
      → 接入训练好的预测模型
        → 部署 FastAPI 后端
          → OBS 推流 YouTube
            → 会员系统变现
```

---

## 二、技术栈清单 Tech Stack

### 前端 Frontend

| 组件 | 技术 | 用途 |
|------|------|------|
| 框架 | React 18 + Vite | 构建 dashboard |
| 样式 | CSS-in-JS (inline styles) | 已内置在 JSX 中 |
| 字体 | IBM Plex Mono + Noto Sans SC | 等宽 + 中文 |
| 图表 | 内置 SVG sparkline | 无需额外库 |
| 通信 | WebSocket (native) | 实时数据推送 |

### 后端 Backend

| 组件 | 技术 | 用途 |
|------|------|------|
| API 框架 | FastAPI (Python) | REST + WebSocket 服务 |
| 数据缓存 | Redis | 实时数据缓存 |
| 任务调度 | Celery 或 APScheduler | 定时拉取比赛数据 |
| 模型推理 | scikit-learn / XGBoost | 预测概率计算 |
| 模型存储 | joblib / pickle | 模型序列化 |

### 数据源 Data Source

| 数据 | 推荐 API | 说明 |
|------|----------|------|
| 实时比分 | API-Football / SportRadar | 比分/事件/统计 |
| 实时赔率 | The Odds API / BetsAPI | 多公司欧赔/亚盘 |
| 历史数据 | Football-Data.co.uk (免费CSV) | 训练模型 |
| xG 数据 | Understat / FBref | 期望进球 |

### 部署 Deployment

| 组件 | 技术 |
|------|------|
| 容器化 | Docker + docker-compose |
| 云服务 | AWS EC2 / DigitalOcean / 阿里云 |
| 反向代理 | Nginx |
| 直播推流 | OBS Studio |

---

## 三、项目结构 Project Structure

```
football-quant-terminal/
├── frontend/                    # React 前端
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── main.jsx             # 入口
│       ├── App.jsx              # 主 App
│       ├── QuantTerminal.jsx    # ← 你的 quant-terminal.jsx
│       ├── hooks/
│       │   └── useWebSocket.js  # WebSocket hook
│       └── utils/
│           └── i18n.js          # 语言配置
│
├── backend/                     # Python 后端
│   ├── requirements.txt
│   ├── main.py                  # FastAPI 入口
│   ├── config.py                # 配置
│   ├── models/
│   │   ├── predictor.py         # 概率预测模型
│   │   ├── quant.py             # 量化指标计算
│   │   └── trained/
│   │       └── model_xgb.pkl    # 训练好的模型文件
│   ├── data/
│   │   ├── api_client.py        # 比赛数据 API 客户端
│   │   ├── odds_client.py       # 赔率数据客户端
│   │   └── cache.py             # Redis 缓存层
│   ├── ws/
│   │   └── manager.py           # WebSocket 连接管理
│   └── training/
│       ├── train.py             # 模型训练脚本
│       ├── features.py          # 特征工程
│       └── data/
│           └── matches.csv      # 历史数据
│
├── docker-compose.yml
├── Dockerfile.frontend
├── Dockerfile.backend
└── nginx.conf
```

---

## 四、分步实施 Step-by-Step

### Step 1：搭建前端项目 (30 分钟)

```bash
# 创建项目
npm create vite@latest frontend -- --template react
cd frontend
npm install
```

把 `quant-terminal.jsx` 复制为 `src/QuantTerminal.jsx`。

修改 `src/main.jsx`：

```jsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import QuantTerminal from './QuantTerminal'

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <QuantTerminal />
  </React.StrictMode>
)
```

修改 `index.html`，设置黑色背景：

```html
<body style="margin:0; background:#0E1117;">
  <div id="root"></div>
  <script type="module" src="/src/main.jsx"></script>
</body>
```

测试：

```bash
npm run dev
# 打开 http://localhost:5173
```

此时你会看到使用模拟数据的完整终端。

---

### Step 2：创建 WebSocket Hook (替换模拟数据)

创建 `src/hooks/useWebSocket.js`：

```javascript
import { useState, useEffect, useRef, useCallback } from 'react';

export function useMatchData(matchId) {
  const [data, setData] = useState(null);
  const [connected, setConnected] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    const url = `ws://localhost:8000/ws/${matchId}`;
    const ws = new WebSocket(url);

    ws.onopen = () => setConnected(true);
    ws.onclose = () => {
      setConnected(false);
      // 自动重连
      setTimeout(() => {
        wsRef.current = new WebSocket(url);
      }, 3000);
    };
    ws.onmessage = (event) => {
      const payload = JSON.parse(event.data);
      setData(payload);
    };

    wsRef.current = ws;
    return () => ws.close();
  }, [matchId]);

  return { data, connected };
}
```

在 `QuantTerminal.jsx` 中替换模拟数据：

```jsx
// 删除 simData 函数和 setInterval
// 改为：
import { useMatchData } from './hooks/useWebSocket';

// 在组件内：
const { data, connected } = useMatchData("12345");
```

---

### Step 3：搭建 FastAPI 后端

```bash
mkdir backend && cd backend
pip install fastapi uvicorn redis requests numpy scikit-learn \
    xgboost joblib aiohttp --break-system-packages
```

创建 `backend/main.py`：

```python
import asyncio
import json
import time
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from models.predictor import MatchPredictor
from data.api_client import FootballAPIClient

app = FastAPI(title="Football Quant API")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

predictor = MatchPredictor()
api_client = FootballAPIClient()

@app.websocket("/ws/{match_id}")
async def websocket_endpoint(ws: WebSocket, match_id: str):
    await ws.accept()
    try:
        while True:
            # 1. 从 API 获取实时数据
            live = await api_client.fetch_live(match_id)

            # 2. 模型预测
            prob = predictor.predict(live)

            # 3. 计算量化指标
            quant = predictor.compute_quant(live, prob)

            # 4. 组装 JSON (按 PRD §8 结构)
            payload = {
                "match": {
                    "league": live["league"],
                    "minute": live["minute"],
                    "score": f"{live['home_goals']}-{live['away_goals']}",
                    "half": "H1" if live["minute"] <= 45 else "H2",
                },
                "probability": {
                    "home": round(prob[0], 2),
                    "draw": round(prob[1], 2),
                    "away": round(prob[2], 2),
                    "delta_home": round(prob[0] - prob[3], 2),
                    "confidence": quant["confidence"],
                },
                "stats": live["stats"],
                "quant": quant,
            }

            await ws.send_json(payload)
            await asyncio.sleep(2)  # PRD §6: 概率刷新 2 秒

    except WebSocketDisconnect:
        pass
```

---

### Step 4：接入比赛数据 API

以 **API-Football** (api-football.com) 为例：

创建 `backend/data/api_client.py`：

```python
import aiohttp

class FootballAPIClient:
    BASE_URL = "https://v3.football.api-sports.io"

    def __init__(self):
        self.api_key = "YOUR_API_KEY"  # 从 .env 读取
        self.headers = {"x-apisports-key": self.api_key}

    async def fetch_live(self, match_id: str) -> dict:
        async with aiohttp.ClientSession() as session:
            # 获取实时比赛数据
            url = f"{self.BASE_URL}/fixtures"
            params = {"id": match_id}
            async with session.get(
                url, headers=self.headers, params=params
            ) as resp:
                data = await resp.json()

            fixture = data["response"][0]
            stats_raw = fixture.get("statistics", [])

            return {
                "league": fixture["league"]["name"],
                "minute": fixture["fixture"]["status"]["elapsed"] or 0,
                "home_goals": fixture["goals"]["home"] or 0,
                "away_goals": fixture["goals"]["away"] or 0,
                "stats": self._parse_stats(stats_raw),
            }

    def _parse_stats(self, stats_raw):
        # 将 API 返回的统计数据映射为 PRD 格式
        home_stats = {s["type"]: s["value"] for s in stats_raw[0]["statistics"]} if stats_raw else {}
        away_stats = {s["type"]: s["value"] for s in stats_raw[1]["statistics"]} if len(stats_raw) > 1 else {}

        return {
            "shots": [
                home_stats.get("Total Shots", 0),
                away_stats.get("Total Shots", 0),
            ],
            "shots_on_target": [
                home_stats.get("Shots on Goal", 0),
                away_stats.get("Shots on Goal", 0),
            ],
            "possession": [
                int(str(home_stats.get("Ball Possession", "50%")).replace("%", "")),
                int(str(away_stats.get("Ball Possession", "50%")).replace("%", "")),
            ],
            "corners": [
                home_stats.get("Corner Kicks", 0),
                away_stats.get("Corner Kicks", 0),
            ],
            "fouls": [
                home_stats.get("Fouls", 0),
                away_stats.get("Fouls", 0),
            ],
        }
```

**数据 API 对比与推荐：**

| API | 价格 | 实时性 | xG数据 | 推荐度 |
|-----|------|--------|--------|--------|
| API-Football | $0 (100次/天免费) | 好 | 无 | ⭐⭐⭐ 入门 |
| SportRadar | $$$ | 极好 | 有 | ⭐⭐⭐⭐ 专业 |
| Football-Data.org | 免费 | 延迟 | 无 | ⭐⭐ 训练 |
| Understat | 免费(爬) | 赛后 | 有 | ⭐⭐ xG训练 |
| The Odds API | $0 (500次/月) | 好 | — | ⭐⭐⭐ 赔率 |

---

### Step 5：训练预测模型

创建 `backend/training/train.py`：

```python
import pandas as pd
import numpy as np
from sklearn.model_selection import cross_val_score
from xgboost import XGBClassifier
import joblib

# 1. 加载历史数据
# 下载: https://www.football-data.co.uk/englandm.php
df = pd.read_csv("data/matches.csv")

# 2. 特征工程
def build_features(df):
    features = pd.DataFrame()
    features["home_odds"] = 1 / df["B365H"]   # Bet365 主胜隐含概率
    features["draw_odds"] = 1 / df["B365D"]
    features["away_odds"] = 1 / df["B365A"]
    features["home_shots"] = df.get("HS", 0)
    features["away_shots"] = df.get("AS", 0)
    features["home_corners"] = df.get("HC", 0)
    features["away_corners"] = df.get("AC", 0)
    return features

X = build_features(df)

# 3. 标签: 0=客胜, 1=平, 2=主胜
y = df["FTR"].map({"H": 2, "D": 1, "A": 0}).values

# 4. 训练
model = XGBClassifier(
    n_estimators=500,
    max_depth=4,
    learning_rate=0.05,
    subsample=0.8,
    colsample_bytree=0.8,
    eval_metric="mlogloss",
)
model.fit(X.values, y)

# 5. 评估
scores = cross_val_score(model, X.values, y, cv=5, scoring="accuracy")
print(f"CV Accuracy: {scores.mean():.4f} ± {scores.std():.4f}")

# 6. 保存
joblib.dump(model, "models/trained/model_xgb.pkl")
print("Model saved.")
```

创建 `backend/models/predictor.py`：

```python
import numpy as np
import joblib
import math

class MatchPredictor:
    def __init__(self, model_path="models/trained/model_xgb.pkl"):
        self.model = joblib.load(model_path)

    def predict(self, live_data: dict) -> tuple:
        """返回 (home_prob, draw_prob, away_prob, prev_home_prob)"""
        features = self._extract_features(live_data)
        proba = self.model.predict_proba([features])[0]
        # 类别顺序: [客胜, 平, 主胜]
        away_p, draw_p, home_p = proba[0], proba[1], proba[2]

        # 赛中 Poisson 修正
        minute = live_data.get("minute", 0)
        h_goals = live_data.get("home_goals", 0)
        a_goals = live_data.get("away_goals", 0)
        home_p, draw_p, away_p = self._live_adjust(
            home_p, draw_p, away_p, minute, h_goals, a_goals
        )

        return (
            round(home_p * 100, 2),
            round(draw_p * 100, 2),
            round(away_p * 100, 2),
            0,  # prev_home (需要在外层追踪)
        )

    def _extract_features(self, live):
        stats = live.get("stats", {})
        return [
            stats.get("shots", [0, 0])[0],
            stats.get("shots", [0, 0])[1],
            stats.get("corners", [0, 0])[0],
            stats.get("corners", [0, 0])[1],
            stats.get("possession", [50, 50])[0] / 100,
            stats.get("possession", [50, 50])[1] / 100,
        ]

    def _live_adjust(self, hp, dp, ap, minute, hg, ag):
        """Poisson 修正：用剩余时间和当前比分调整"""
        remain = max((90 - minute) / 90, 0.02)
        diff = hg - ag

        if diff > 0:
            hp *= (1 + 0.15 * diff * (1 - remain))
        elif diff < 0:
            ap *= (1 + 0.15 * abs(diff) * (1 - remain))

        total = hp + dp + ap
        return hp / total, dp / total, ap / total

    def compute_quant(self, live, prob):
        """计算 PRD §4.5 量化指标"""
        minute = live.get("minute", 0)
        stats = live.get("stats", {})
        h_shots = stats.get("shots", [0, 0])[0]
        a_shots = stats.get("shots", [0, 0])[1]

        pressure = min(98, max(10,
            50 + (h_shots - a_shots) * 3
            + (stats.get("possession", [50, 50])[0] - 50) * 0.8
        ))

        return {
            "pressure_index": round(pressure),
            "momentum": round((h_shots - a_shots) * 2.5),
            "volatility": round(0.5 + (minute / 90) * 0.5, 2),
            "risk_concede": round(30 + (90 - minute) / 90 * 20),
            "goal_window": f"{max(1, 5 - minute // 20)}-{max(3, 12 - minute // 15)}",
            "confidence": round(prob[0] + 60 + np.random.uniform(-3, 3)),
            "model_variance": round(np.random.uniform(0.05, 0.15), 3),
        }
```

---

### Step 6：OBS 直播配置

```
┌─────────────────────────────────────────┐
│  OBS Studio 配置                         │
│                                         │
│  1. 场景: "Quant Terminal"              │
│                                         │
│  2. 来源:                               │
│     [Browser Source]                     │
│       URL: http://localhost:5173        │
│       宽度: 1920                        │
│       高度: 1080                        │
│       ☑ 刷新页面 when scene active      │
│       ☑ 关闭 source when not visible    │
│                                         │
│  3. 推流设置:                            │
│     服务: YouTube - RTMPS               │
│     密钥: (从 YouTube Studio 获取)       │
│                                         │
│  4. 输出:                               │
│     编码器: x264                        │
│     比特率: 4500 Kbps                   │
│     分辨率: 1920x1080                   │
│     帧率: 30 FPS                        │
│                                         │
│  5. 可选: 加摄像头 (右下角小窗)          │
└─────────────────────────────────────────┘
```

---

### Step 7：Docker 部署

`docker-compose.yml`：

```yaml
version: "3.9"
services:
  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports: ["8000:8000"]
    depends_on: [redis]
    environment:
      - REDIS_URL=redis://redis:6379
      - FOOTBALL_API_KEY=${FOOTBALL_API_KEY}
    volumes:
      - ./backend/models/trained:/app/models/trained

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports: ["5173:80"]
    depends_on: [backend]

  nginx:
    image: nginx:alpine
    ports: ["80:80", "443:443"]
    volumes:
      - ./nginx.conf:/etc/nginx/conf.d/default.conf
    depends_on: [frontend, backend]
```

---

## 五、启动流程 Launch SOP

```bash
# 1. 启动服务
docker-compose up -d

# 2. 确认后端
curl http://localhost:8000/health

# 3. 确认前端
# 打开 http://localhost:5173

# 4. 打开 OBS
# Browser Source → http://localhost:5173

# 5. 开始推流
# OBS → 开始推流
```

---

## 六、分阶段实施计划

| 阶段 | 时间 | 内容 | 产出 |
|------|------|------|------|
| **Week 1** | 3天 | 前端项目搭建 + 本地跑通 | 可运行的 React 项目 |
| **Week 1** | 2天 | FastAPI 后端 + WebSocket | 前后端联通 |
| **Week 2** | 3天 | 接入 API-Football | 真实比赛数据 |
| **Week 2** | 2天 | 训练基础 XGBoost 模型 | model_xgb.pkl |
| **Week 3** | 3天 | 量化指标 + Poisson 修正 | 完整 Quant Layer |
| **Week 3** | 2天 | OBS 配置 + 测试直播 | 首次直播测试 |
| **Week 4** | 5天 | Docker 部署 + 上线 | 正式上线 YouTube |

---

## 七、费用预估 Cost Estimate

| 项目 | 月费 (USD) | 说明 |
|------|-----------|------|
| 云服务器 | $10-20 | DigitalOcean 2C4G |
| API-Football | $0-10 | 免费层够用 |
| The Odds API | $0 | 免费层 500次/月 |
| 域名 | $1 | 可选 |
| OBS | $0 | 免费 |
| **合计** | **$11-31/月** | |

---

## 八、关键注意事项

### 版权安全
- 页面始终显示 `DATA VISUALIZATION ONLY`
- 不使用联赛官方 Logo
- 不播放比赛画面/声音
- 数据延迟 30 秒以上

### 模型准确度
- 初期用赔率隐含概率作为 baseline (已经很强)
- 逐步加入 xG、Elo、状态等特征
- 用 Brier Score 评估校准度，不仅看准确率

### 扩展路线
```
单场终端 → 多场并行 → API SaaS → 会员订阅
```
