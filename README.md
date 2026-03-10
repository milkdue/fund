# 基金涨幅预测 MVP（安卓优先，预留 iOS 扩展）

本仓库实现了一个可演示的 MVP 骨架：
- 安卓客户端：Kotlin + Jetpack Compose + MVVM + Hilt + Retrofit + Room
- 后端服务：FastAPI + SQLAlchemy + PostgreSQL/Redis（compose）
- 协议稳定：`/v1` 版本化接口 + 统一错误结构，方便后续接 iOS

## 目录
- `android/` 安卓 App（当前主交付）
- `backend/` API 与预测服务骨架
- `infra/docker-compose.yml` 本地依赖一键启动
- `docs_api_contract.md` 跨端契约文档

## 已实现接口
- `GET /v1/funds/search?q=`
- `GET /v1/funds/hot`
- `GET /v1/funds/{code}/quote`
- `GET /v1/funds/{code}/predict?horizon=short|mid`
- `GET /v1/funds/{code}/prediction-change?horizon=short|mid`
- `GET /v1/funds/{code}/explain?horizon=short|mid`
- `GET /v1/funds/{code}/ai-judgement?horizon=short|mid`（Gemini 二级意见，失败自动回退到规则层）
- `GET /v1/funds/{code}/kline`（净值估算趋势图数据，非真实OHLC）
- `GET /v1/funds/{code}/news-signal`
- `POST /v1/funds/{code}/feedback`
- `GET /v1/funds/{code}/feedback/summary?horizon=short|mid`
- `GET /v1/user/watchlist`
- `POST /v1/user/watchlist`
- `GET /v1/user/watchlist/insights`
- `GET /v1/user/alerts`
- `POST /v1/user/alerts`
- `GET /v1/user/alerts/check`
- `GET /v1/user/alerts/events`
- `POST /v1/user/alerts/push-test`
- `POST /v1/user/events`
- `GET /v1/user/weekly-report`
- `GET /v1/model/health`
- `GET /v1/model/backtest/latest?horizon=short|mid`
- `GET /v1/model/backtest/walkforward?horizon=short|mid`
- `GET /v1/model/ab/latest?horizon=short|mid`
- `GET /v1/model/ab/summary?horizon=short|mid`
- `GET /v1/system/data-sources`
- `GET /v1/system/data-health`
- `GET /v1/system/market-context`
- `GET /healthz`

## 快速启动
### 1) 后端
```bash
make backend-install
make backend-run
```
访问 [Swagger](http://127.0.0.1:8000/docs)

### 2) 安卓
1. Android Studio 打开 `android/`
2. 启动模拟器（后端地址已配为 `10.0.2.2:8000`）
3. 运行 `app`

## 打包发布
### Debug APK
```bash
cd android
./build_apk.sh
```

### Release AAB（上架或内测分发）
```bash
cd android
./build_aab.sh
```

说明：
- 若提示 `gradlew not found`，先在 Android Studio 里打开项目并生成 Gradle Wrapper（或执行 `gradle wrapper`）。
- Release 包需要你在 Android Studio/Gradle 中配置签名证书（keystore）。

## Vercel 部署后端
本项目已提供 Vercel 入口与配置：
- `api/index.py`
- `api/requirements.txt`
- `vercel.json`

### 推荐环境变量（Vercel Project Settings -> Environment Variables）
- `FUND_ENV=prod`
- `FUND_DB_URL=<Neon pooled connection string>`
- `FUND_AUTO_CREATE_TABLES=true`
- `FUND_BOOTSTRAP_DEMO_DATA=false`
- `CRON_SECRET=<long-random-string>`（推荐，Vercel Cron 鉴权）
- `FUND_AUTH_ENABLED=false`（开启后，用户态接口需 Bearer Token）
- `FUND_AUTH_BEARER_TOKEN=<single-token>`
- `FUND_AUTH_TOKEN_MAP=<token1:user1,token2:user2>`（可选，多用户映射；配置后优先）
- `FUND_AUTH_DEFAULT_USER_ID=authorized-user`
- `FUND_AUTH_USER_API_LIMIT_PER_MIN=120`
- `FUND_AUTH_AUDIT_ENABLED=true`
- `FUND_MODEL_SHORT_VERSION=short-v0.1`
- `FUND_MODEL_MID_VERSION=mid-v0.1`
- `FUND_MODEL_CANDIDATE_SHORT_VERSION=short-v0.2`
- `FUND_MODEL_CANDIDATE_MID_VERSION=mid-v0.2`
- `FUND_MODEL_AB_ENABLED=true`
- `FUND_GEMINI_ENABLED=false`
- `FUND_GEMINI_API_KEY=<your-gemini-key>`
- `FUND_GEMINI_MODEL=gemini-2.0-flash`
- `FUND_GEMINI_TEMPERATURE=0.2`
- `FUND_GEMINI_TIMEOUT_MS=12000`
- `FUND_GEMINI_MAX_OUTPUT_TOKENS=512`
- `FUND_GEMINI_PROMPT_VERSION=v1`
- `FUND_GEMINI_DAILY_BUDGET_CALLS=400`
- `FUND_GEMINI_COMPLIANCE_FILTER_ENABLED=true`
- `FUND_BARK_ENABLED=false`
- `FUND_BARK_BASE_URL=https://api.day.app`
- `FUND_BARK_USER_KEY=<your-bark-user-key>`
- `FUND_BARK_ICON_URL=<optional-icon-url>`
- `FUND_BARK_GROUP=fund_predictor`
- `FUND_BARK_LIMIT_PER_MIN=30`
- `FUND_BARK_TIMEOUT_MS=5000`
- `FUND_SOURCE_NAV_LIMIT_PER_MIN=90`
- `FUND_SOURCE_SEARCH_LIMIT_PER_MIN=30`
- `FUND_SOURCE_NEWS_LIMIT_PER_MIN=20`
- `FUND_SOURCE_MARKET_LIMIT_PER_MIN=30`

可选：
- `FUND_REDIS_URL=<Upstash Redis URL>`（当前版本可不填）

说明：
- 数据库连接请使用 Neon 的 pooled 字符串。
- 若连接串未带 `sslmode=require`，代码会自动补上。
- 不要把 `.env`、`.env.local`、`.env.production` 推送到远程仓库（已在 `.gitignore`）。
- 当 `FUND_AUTH_ENABLED=true` 时，以下接口需 `Authorization: Bearer <token>`：
  `POST /v1/funds/{code}/feedback`、`/v1/user/watchlist*`、`/v1/user/alerts*`、`/v1/user/events`、`/v1/user/weekly-report`。

### 每日自动刷新（Vercel Cron）
- 已在 `vercel.json` 配置：`0 2 * * *`（每天 UTC 02:00）
- 触发路径：`/v1/internal/cron/daily-refresh`
- 该接口要求 `Authorization: Bearer <CRON_SECRET>`，Vercel Cron 会自动携带。

### 每周回测报表（Vercel Cron）
- 已在 `vercel.json` 配置：`0 3 * * 1`（每周一 UTC 03:00）
- 触发路径：`/v1/internal/cron/weekly-backtest`
- 可通过 `/v1/model/backtest/latest?horizon=short|mid` 查询最新报表

## 当前模型实现
- 规则基线预测：基于最新日涨跌与20日波动生成 short/mid 概率与预期涨幅
- AI 二级意见：`/v1/funds/{code}/ai-judgement`，输入量化+市场+舆情+回测上下文，Gemini 不可用时自动降级规则输出
- AI 治理：支持每日调用预算上限与合规措辞过滤（检测确定性承诺词并自动降级）
- 阈值推送：支持 Bark 推送（环境变量配置 `FUND_BARK_USER_KEY`，代码中不写入明文 key）
- 舆情增强：每日抓取基金公告标题，进行关键词情绪与事件打分，参与预测修正
- 风险提示增强：`explain` 返回风险标签（高波动、置信度偏低、舆情负面等）
- 数据新鲜度：`quote/predict/explain` 返回 `data_freshness`（fresh/lagging/stale）
- 周报机制：自动生成固定回测指标（准确率、AUC、F1、年化、回撤、夏普）
- 可追溯快照：`predict` 返回 `snapshot_id/model_version/data_source`，支持历史变化比对
- 漂移分析：`prediction-change` 返回与上次预测差异及因子变化
- 可观测性：`system/data-health` 汇总覆盖率、新鲜度、数据源状态
- 用户运营：行为事件采集与 `weekly-report` 周报
- 市场因子：引入沪深300/中证500/创业板的市场与风格打分
- 概率校准：对 `up_probability` 进行校准变换，减少过度自信
- 反馈闭环：支持“本次预测是否有帮助”采集
- 阈值提醒：支持用户配置概率/置信度/预期涨幅阈值
- A/B 对比：同一时点记录 baseline/candidate 预测差异与胜率
- 真实净值来源：东方财富 `pingzhongdata/{fund_code}.js`
- 基金搜索来源：本地库优先 + 东方财富 `fundcode_search.js` 远程补全并回写缓存
- 公告来源：东方财富 `FundArchivesDatas.aspx?type=jjgg&code={fund_code}`
- 已加每源每分钟限流（默认：净值 90/min，搜索 30/min，公告 20/min；超限返回 429）
- 每日任务入口：`backend/app/workers/daily_job.py`

## 后续接入真实能力
1. 接入公开行情/因子数据并落库
2. 用 LightGBM/XGBoost 替换当前 mock 预测
3. 引入 Celery beat/cron 做每日更新
4. 添加埋点、告警、回测报告

## P1/P2 预留扩展位
- 统一新鲜度字段：`quote/predict/explain` 的 `data_freshness`
- 统一风险输出：`explain.risk_flags`
- 统一周报查询：`/v1/model/backtest/latest`
- 趋势图语义标记：`kline.is_synthetic` + `kline.note`

## 合规边界（已在产品流中体现）
- 首次风险提示强确认
- 文案固定为“仅供学习研究，不构成投资建议”
- 不做收益承诺、不做自动交易
