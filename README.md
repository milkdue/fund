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
- `GET /v1/funds/{code}/explain?horizon=short|mid`
- `GET /v1/user/watchlist`
- `POST /v1/user/watchlist`
- `GET /v1/model/health`
- `GET /v1/system/data-sources`
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
- `FUND_MODEL_SHORT_VERSION=short-v0.1`
- `FUND_MODEL_MID_VERSION=mid-v0.1`
- `FUND_SOURCE_NAV_LIMIT_PER_MIN=90`
- `FUND_SOURCE_SEARCH_LIMIT_PER_MIN=30`

可选：
- `FUND_REDIS_URL=<Upstash Redis URL>`（当前版本可不填）

说明：
- 数据库连接请使用 Neon 的 pooled 字符串。
- 若连接串未带 `sslmode=require`，代码会自动补上。
- 不要把 `.env`、`.env.local`、`.env.production` 推送到远程仓库（已在 `.gitignore`）。

### 每日自动刷新（Vercel Cron）
- 已在 `vercel.json` 配置：`0 2 * * *`（每天 UTC 02:00）
- 触发路径：`/v1/internal/cron/daily-refresh`
- 该接口要求 `Authorization: Bearer <CRON_SECRET>`，Vercel Cron 会自动携带。

## 当前模型实现
- 规则基线预测：基于最新日涨跌与20日波动生成 short/mid 概率与预期涨幅
- 真实净值来源：东方财富 `pingzhongdata/{fund_code}.js`
- 基金搜索来源：本地库优先 + 东方财富 `fundcode_search.js` 远程补全并回写缓存
- 已加每源每分钟限流（默认：净值 90/min，搜索 30/min；超限返回 429）
- 每日任务入口：`backend/app/workers/daily_job.py`

## 后续接入真实能力
1. 接入公开行情/因子数据并落库
2. 用 LightGBM/XGBoost 替换当前 mock 预测
3. 引入 Celery beat/cron 做每日更新
4. 添加埋点、告警、回测报告

## 合规边界（已在产品流中体现）
- 首次风险提示强确认
- 文案固定为“仅供学习研究，不构成投资建议”
- 不做收益承诺、不做自动交易
