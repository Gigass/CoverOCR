# CoverOCR MVP Implementation Plan (V1.1)

> 对应 `todo_mvp.md` 的可执行方案：以“直接复用公开 OCR/字体模型，快速跑通演示”为目标。

## 1. 基础环境
1. **初始化仓库结构**
   - `frontend/`, `backend/`, `models/`, `scripts/`, `infra/`。
   - FastAPI+Vite Hello World 可跑通；`start_local.sh` 支持一键启动。
2. **可选 Docker Compose**
   - `infra/docker-compose.yml` 中仅保留 `frontend`, `backend`, `minio`, `postgres`（为未来扩展预留）；MVP 可直接本机运行。
3. **环境变量管理**
   - `frontend/.env.example` 定义 `VITE_API_BASE_URL`；`infra/.env.example` 定义存储/数据库变量；`backend/app/core/config.py` 通过 Pydantic Settings 读取。

## 2. 数据与模型
1. **OCR 模型接入**
   - 直接下载 PaddleOCR PP-OCRv4 中文检测/识别模型（官方权重）；封装 `scripts/download_models.sh`。
   - 验证：`python backend/services/ocr.py --image sample.jpg` 输出文字框与文本。
2. **字体识别模型**
   - 复用 PaddleClas 字体识别模型或其他公开权重（无需自训），放置于 `models/weights/fonts/`。
   - 验证：`python backend/services/font_classifier.py --image crop.png` 输出字体标签。
3. **数据管理（可选）**
   - 若需记录上传图像，可将样本与推理结果写入本地目录或 MinIO；暂不采集封面数据。

## 3. 后端 FastAPI
1. **路由实现**
   - `POST /api/v1/upload`：保存图像（内存或 `/tmp`），生成 `request_id`。
   - `GET /api/v1/result/{request_id}`：返回文字、字体、耗时；若无结果返回 404。
   - 验证：`pytest backend/tests/test_api.py`。
2. **推理流水线**
   - 在 `backend/app/services/pipeline.py` 调用 PaddleOCR 完成检测+识别，再将裁剪块传入字体模型；使用 asyncio 提升吞吐。
   - 保证单张图 10 秒内完成，必要时对高分辨率图片做缩放。
3. **对象存储/数据库（后续可加）**
   - MVP 阶段使用内存字典缓存结果；如需持久化，再接入 MinIO + PostgreSQL。

## 4. 前端 React
1. **项目初始化**
   - 使用 Vite+React+TS，安装 `antd`, `axios`, `@tanstack/react-query`（可选）。
2. **界面**
   - 左侧上传卡片、流程状态 Tag、请求 ID；右侧 Tabs 展示文字列表与字体分布、耗时。
   - 提供错误提示、超时提示、重试按钮；后续可加画布预览。
3. **API 集成**
   - 通过 `axios` 调用 `POST /upload`、轮询 `GET /result/{id}`；封装 hooks 或自定义状态管理。
   - 可添加 Skeleton/Loading 状态以优化体验。

## 5. 验证与交付
1. **端到端脚本**
   - `scripts/e2e_test.py --image samples/demo.jpg`：调用上传+查询接口，验证在 10 秒内得到文字/字体结果。
2. **手动场景回归**
   - 在桌面/移动浏览器上传 2-3 张实拍封面，确认界面展示正常并截图。
3. **文档交付**
   - 更新 README（本地运行/一键启动）、`architecture_design.md`（V1.1 方案）、`implementation_plan_v1.md`、`todo_mvp.md`。

## 6. 里程碑建议
| 周期 | 目标 | 验收 |
|------|------|------|
| Week 1 | 完成环境、模型下载、后端占位 API | `start_local.sh` 可运行；`pytest backend/tests` 通过 |
| Week 2 | 接入 PaddleOCR + 字体模型，打通推理流水线 | 本地调用能返回文字+字体结果，耗时 ≤10s |
| Week 3 | 前端 UI & API 集成 | 浏览器上传可看到识别结果，错误状态提示完整 |
| Week 4 | 端到端验证、文档更新 | `scripts/e2e_test.py` 通过，README/架构文档更新为 V1.1 |
