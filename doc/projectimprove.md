Ⅰ. λ_live 精确公式版本（Total Goals O/U 引擎）

目标：实时输出 λ_total_live，并据此计算 Over/Under 各盘口概率。
核心：赛前强度 + 赛中节奏与机会质量 + 比分状态 + 红牌 + 盘口市场校准。

1) 定义与输入
赛前（Pre-match）

λ_pre：赛前总进球强度（home+away）

λh_pre, λa_pre：主/客进球强度

赛中实时（Live, t 分钟）

t：当前分钟（0~90）

xG_t：截至 t 的累计 xG（home+away）

SOT_t：截至 t 的射正总数（home+away）

SHOT_t：截至 t 的射门总数

DA_t：危险进攻（dangerous attacks）

RC_h, RC_a：红牌（主/客）

score_diff = home_goals - away_goals

市场（Market）

p_mkt_over(L)：盘口 L 的市场去水后 Over 概率（实时赔率）

可选：λ_mkt：从市场盘口反推的“市场隐含 λ”（更专业）

2) 先计算“剩余时间系数”

我们只对“剩余时间”进行强度分配（越接近结束，剩余进球期望越少）。

定义剩余分钟：

r = max(90 - t, 1)

线性时间份额：

τ = r / 90

你也可以用更贴近真实的非线性（建议）：

τ_nl = (r / 90) ^ 0.85

3) 核心：实时节奏与机会质量（Tempo & Chance Quality）
3.1 xG 速度（最重要）

截至 t 的 xG 速度：

vxg = xG_t / max(t, 1)

赛前预期 xG 速度（用 λ_pre 近似，或用历史均值）：

vxg_pre = λ_pre / 90

相对比值：

Rxg = vxg / max(vxg_pre, 1e-6)

为了防极端，做截断：

Rxg_c = clip(Rxg, 0.4, 2.2)

3.2 射正速度补偿（防止 xG 缺失）

vsot = SOT_t / max(t,1)

vsot_pre：赛前均值（可按联赛/球队先给常数，比如 0.08~0.12）

Rsot_c = clip(vsot / max(vsot_pre,1e-6), 0.5, 1.8)

3.3 危险进攻补偿（数据源常有）

vda = DA_t / max(t,1)

vda_pre：赛前均值（联赛常数）

Rda_c = clip(vda / max(vda_pre,1e-6), 0.5, 1.8)

3.4 合成 Tempo 因子（加权几何平均更稳）

建议权重（可调）：

xG 最重要，其次 SOT，再次 DA

𝑇
𝑒
𝑚
𝑝
𝑜
=
exp
⁡
(
𝑤
1
ln
⁡
𝑅
𝑥
𝑔
𝑐
+
𝑤
2
ln
⁡
𝑅
𝑠
𝑜
𝑡
𝑐
+
𝑤
3
ln
⁡
𝑅
𝑑
𝑎
𝑐
)
Tempo=exp(w
1
	​

lnRxg
c
	​

+w
2
	​

lnRsot
c
	​

+w
3
	​

lnRda
c
	​

)

推荐：

w1=0.60, w2=0.25, w3=0.15

再做一次截断：

Tempo_c = clip(Tempo, 0.6, 1.7)

4) 比分状态因子（Game State）

比分对节奏影响巨大：领先方会降速，落后方会提速。

定义：

d = score_diff

一个实战好用的连续函数（避免硬规则跳变）：

𝐺
(
𝑑
,
𝑡
)
=
1
+
𝛼
⋅
tanh
⁡
(
𝛽
⋅
(
−
𝑑
)
)
⋅
𝑠
(
𝑡
)
G(d,t)=1+α⋅tanh(β⋅(−d))⋅s(t)

解释：

-d：主队落后（d<0）时为正，会提高总进球；主队领先则相反

s(t)：越到后面越明显（比如 60 分钟后追分更急）

取：

s(t) = sigmoid((t-55)/8) （55 分钟后开始明显）

α = 0.14（影响强度）

β = 0.9（变化陡峭）

直观效果：

0:0 → ~1.00

1:0 领先 → ~0.92~0.97

0:1 落后 → ~1.03~1.12（后期更明显）

5) 红牌因子（Red Card）

红牌对总进球影响不稳定：

领先方吃红牌：可能增加总进球（被压制）

落后方吃红牌：可能降低总进球（进攻没了）

实战建议：用“相对红牌差”+“比分状态”联合建模。

定义：

rc_diff = RC_h - RC_a（主队红牌更多为正）

一个可落地的函数：

𝑅
(
𝑟
𝑐
_
𝑑
𝑖
𝑓
𝑓
,
𝑑
,
𝑡
)
=
1
+
𝛾
⋅
tanh
⁡
(
−
𝑟
𝑐
_
𝑑
𝑖
𝑓
𝑓
)
⋅
𝑢
(
𝑑
,
𝑡
)
R(rc_diff,d,t)=1+γ⋅tanh(−rc_diff)⋅u(d,t)

其中：

tanh(-rc_diff)：主队红牌更多 → negative → 使因子下降/上升按 u 决定

u(d,t)：取决于领先/落后与时间

一个实用近似：

如果 落后方吃红牌：总进球偏下降（追分难）

如果 领先方吃红牌：总进球偏上升（被围攻）

可用：

u(d,t) = 0.6 + 0.4*sigmoid((t-45)/10)（下半场更显著）

γ = 0.10~0.18

同时做截断：

R_c = clip(R, 0.75, 1.25)

6) 最终 λ_total_live 公式
6.1 计算“当前比赛总强度”

我们关心剩余时间的期望进球：

赛前剩余进球期望（基线）：

𝜆
𝑟
𝑒
𝑚
,
𝑝
𝑟
𝑒
=
𝜆
𝑝
𝑟
𝑒
⋅
𝜏
𝑛
𝑙
λ
rem,pre
	​

=λ
pre
	​

⋅τ
nl
	​


赛中修正：

𝜆
𝑟
𝑒
𝑚
,
𝑙
𝑖
𝑣
𝑒
=
𝜆
𝑟
𝑒
𝑚
,
𝑝
𝑟
𝑒
⋅
𝑇
𝑒
𝑚
𝑝
𝑜
𝑐
⋅
𝐺
(
𝑑
,
𝑡
)
⋅
𝑅
𝑐
λ
rem,live
	​

=λ
rem,pre
	​

⋅Tempo
c
	​

⋅G(d,t)⋅R
c
	​


最终全场总强度：

𝜆
𝑡
𝑜
𝑡
𝑎
𝑙
,
𝑙
𝑖
𝑣
𝑒
=
𝑔
𝑜
𝑎
𝑙
𝑠
_
𝑠
𝑜
_
𝑓
𝑎
𝑟
+
𝜆
𝑟
𝑒
𝑚
,
𝑙
𝑖
𝑣
𝑒
λ
total,live
	​

=goals_so_far+λ
rem,live
	​


其中：

goals_so_far = home_goals + away_goals

这个定义非常适合 O/U：因为 O/U 本质是“全场总进球”。

7) 市场校准（让盈利更稳）

你做实战盈利，必须把市场当作校准信息源。

定义 Over 盘口 L 的模型概率：

p_model_over(L)

市场去水概率：

p_mkt_over(L)

做一个“收缩到市场”的校准（避免模型过激）：

𝑝
𝑓
𝑖
𝑛
𝑎
𝑙
=
(
1
−
𝜂
)
 
𝑝
𝑚
𝑜
𝑑
𝑒
𝑙
+
𝜂
 
𝑝
𝑚
𝑘
𝑡
p
final
	​

=(1−η)p
model
	​

+ηp
mkt
	​


推荐：

η = 0.15~0.35（按联赛噪声调整）

高级联赛可低一点；低级联赛高一点

这样你的信号更稳、更容易 CLV 正。

8) 信号强度（吸粉直播关键）

吸粉不是“每分钟出信号”，而是：

少而准 + 有解释 + 有倒计时 + 有冷却

定义：

edge = p_final - p_mkt_over(L)

tempo_index = 100 * clip((Tempo_c - 0.6)/(1.7-0.6), 0, 1)

信号评级：

edge >= 0.04 且 tempo_index >= 60 → SIGNAL

edge >= 0.06 且 tempo_index >= 70 → STRONG

edge >= 0.08 且 tempo_index >= 78 → HIGH

加冷却：

进球后 cooldown = 180s

信号触发后 cooldown = 120s（避免刷屏）

Ⅱ. 终极 Bloomberg UI 视觉标准（Design System）

下面是可以直接写进你的项目 DESIGN_SYSTEM.md 的规范。

1) 设计语言与原则
1.1 关键词

Dense but readable（密集但可读）

Quiet confidence（克制权威）

Market-first（市场优先）

Explainable（可解释）

Zero entertainment aesthetics（零娱乐化视觉）

1.2 禁止项

❌ 霓虹光效 / HUD 发光线

❌ 仪表盘 / 圆环 / 赛博炫光

❌ 球场背景 / 球员图片 / 俱乐部 Logo

❌ 大动画 / 闪烁字幕条

❌ 电视台转播布局

2) Typography（字体系统）
2.1 字体选择

主字体：IBM Plex Mono（数字/标签/终端）

辅助：Noto Sans SC（中文说明）

2.2 字号等级（建议）

H0（核心报价）：28–34px（仅概率/λ/Edge）

H1（关键数值）：16–18px

Body（表格/指标）：11–13px

Meta（状态/注释）：8–10px

2.3 数字排版

所有数值右对齐

概率统一 xx.xx%

λ 统一 x.xx

Edge 统一带符号：+x.xx%

3) Color System（颜色系统）

你现有配色已经很好，这里补充“语义规则”。

3.1 基础色（建议沿用）

bg: #0E1117

bgCard: #131720

border: #1E2530

text: #E5E5E5

textDim: #6B7280

3.2 语义色（严格语义）

Up (positive / favorable): #00C853

Down (negative / unfavorable): #FF3D00

Accent (signal): #F4C430 仅用于 Signal/Alert

AccentBlue (market/away): #00C8FF 仅用于 Market line / Away line

3.3 使用规则（很重要）

“主队”不要用专属色，避免体育感

只有 变化方向 才上色（▲绿 / ▼红）

金色只用于：

SIGNAL ACTIVE

EDGE 达到阈值

SYSTEM ALERT

4) Layout Grid（布局网格）
4.1 主布局（直播版推荐）

3 列：

左：Quote（1X2 + O/U）

中：Trend（λ_total + market + tempo）

右：Tape（events + stats）

4.2 固定高度区域（避免跳动）

顶部 State bar：固定 36–44px

Disclaimer bar：固定 16–20px

Footer：固定 18–22px

中间主区：height: calc(100vh - Xpx) 固定

5) Components（组件规范）
5.1 StateBar（必须）

显示：

LEAGUE | ROUND | SCORE | MIN | HALF

DELAY xx s | HEALTH OK/DEGRADED/STALE | SRC LIVE | ODDS

健康状态用点：

OK：绿点

DEGRADED：橙点

STALE：红点（并显示 STALE）

5.2 QuoteCard（报价卡）

用于：

1X2 概率

O/U 概率 + Market + Edge + Signal

结构：

Label（8–10px）

Value（H0）

Delta（11px，▲/▼）

5.3 TradingPanel（吸粉核心）

固定展示：

Pre λ_total

Live λ_total

Market Prob

Model Prob

Edge

Signal

Why Δ（Top 3）

注意：Signal 不弹窗，用“卡片顶部细线 + 背景轻微提亮”即可。

5.4 TrendChart（趋势）

推荐 1 张主图就够：

主线：λ_total_live

辅线：λ_mkt（虚线）

叠加：tempo index（细线/淡色）

5.5 EventTape（留存模块）

显示最近 5–8 条：

GOAL / VAR / RED / YELLOW / SUB / PENALTY
每条固定格式：

67' GOAL — HOME

5.6 MicroBars（节奏条）

替代仪表盘：

Tempo Index

Pressure Index

Volatility

6) Motion（动效规范）

仅做 数值平滑过渡（200–300ms）

禁止闪烁

关键事件（Goal）允许：

顶栏背景亮 0.5s（极弱）

EventTape 插入新行高亮 0.8s

7) Streaming Readability（直播可读性）
7.1 OBS 安全区

关键数字（λ / Edge / Signal）距离边缘至少 24px

字号不要低于 10px（否则手机端看不清）

7.2 “吸粉三秒原则”

屏幕任何时刻都必须能一眼看到这三项：

当前线：LINE 2.5

Edge：+7%

Signal：BUY OVER / NO SIGNAL

Ⅲ. 你下一步最该加的“吸粉 UI 功能”（不涉及会员）

按收益排序（直接提升留存）：

O/U Trading Panel（常驻）：LINE/Model/Market/Edge/Signal

EventTape（常驻）：每 1–2 分钟至少动一次

Why Δ（常驻）：每次概率变化给理由

Signal Cooldown Countdown：NEXT EVAL IN 01:20（系统运行感）

Goal Window Banner：HIGH GOAL WINDOW 5–10 MIN（刺激留存但不夸张）