# CoverOCR MVP Implementation Plan (V1.0)

> 对应 `todo_mvp.md` 的可执行方案，明确每个任务的负责人、产出物与验证方式。

## 1. 基础环境
1. **初始化仓库结构**
   - 动作：创建 `frontend/`, `backend/`, `models/`, `data/`, `infra/`.
   - 产出物：`backend/app/main.py` (占位), `frontend/package.json` (Vite React).
   - 验证：`tree -L 2` 显示结构，`pnpm dev` 与 `uvicorn` 均可运行 Hello World。
2. **Docker Compose**
   - 动作：在 `infra/docker-compose.yml` 定义 `frontend`, `backend`, `inference`, `minio`, `postgres`.
   - 配置：共享 `.env`，FastAPI 通过 `MINIO_ENDPOINT`, `DATABASE_URL` 读取。
   - 验证：`docker compose up` 后前端可访问（占位页面），MinIO/PG 容器健康。
3. **环境变量管理**
   - 动作：在 `infra/.env.example` 定义密钥、存储路径；使用 `python-dotenv` 加载。
   - 验证：`backend/app/config.py` 能读取变量，`pytest` 中注入测试值。

## 2. 数据与模型
1. **封面数据采集**
   - 动作：编写 `scripts/download_covers.py`，从公开数据集抓取至少 10 本教材封面。
   - 存放：`data/covers/{book_id}/{uuid}.jpg`。
   - 验证：`python scripts/validate_dataset.py --type cover` 输出通过。
2. **OCR 模型接入**
   - 动作：下载 PaddleOCR 中文检测/识别模型至 `models/weights/paddleocr/`；提供 `scripts/download_models.sh`.
   - 验证：`python backend/services/ocr.py --image sample.jpg` 输出文字列表。
3. **封面分类模型微调**
   - 动作：在 `models/training/cover_classifier.ipynb`（或 `.py`）加载 EfficientNet-B3，替换分类头，使用小批量数据微调。
   - 产出物：`models/weights/cover_classifier.pt`.
   - 验证：`python backend/services/cover_classifier.py --image sample.jpg` 输出 top-k。
4. **字体识别 MVP**
   - 动作：使用字体文件渲染语料，合成 6 类字体数据；训练 ResNet18。
   - 存储：`data/fonts/{font}/{uuid}.png`, 模型 `models/weights/font_classifier.pt`.
   - 验证：`python backend/services/font_classifier.py --image crop.png` 输出字体。

## 3. 后端 FastAPI
1. **路由实现**
   - `POST /api/v1/upload`: 保存文件 + 生成 `request_id`（UUID），写入 PostgreSQL `jobs` 表。
   - `GET /api/v1/result/{request_id}`: 查询 `jobs` 状态，返回 JSON。
   - 验证：`pytest backend/tests/test_routes.py`.
2. **推理流水线**
   - 动作：实现 `backend/pipeline/inference.py`，串联封面分类、OCR、字体识别；使用 asyncio 并发处理。
   - 超时：10 秒超时，超时写入 `jobs.status=FAILED_TIMEOUT`.
   - 验证：`pytest backend/tests/test_pipeline.py` + 手动调用。
3. **对象存储与数据库**
   - MinIO：使用 `aioboto3` 上传原图与结果 JSON。
   - PostgreSQL：`jobs`, `results`, `books` 三张表；使用 SQLAlchemy ORM。
   - 验证：`alembic upgrade head` + `pytest backend/tests/test_repositories.py`.

## 4. 前端 React
1. **项目初始化**
   - 命令：`pnpm create vite frontend --template react-ts`; 安装 `antd`, `axios`, `react-query`.
   - 验证：`pnpm run dev` 页面可访问。
2. **页面开发**
   - 组件：`UploadCard`, `ResultTabs`, `PreviewCanvas`, `LatencyIndicator`.
   - 流程：上传 -> 显示进度 -> 轮询结果 -> 渲染 Tab/Canvas。
   - 验证：`pnpm run lint`，Storybook（可选）展示主要组件。
3. **API 集成**
   - `useUploadMutation` & `useResultQuery` hooks；错误状态展示重试按钮。
   - 验证：Mock API + Cypress E2E（可选）覆盖上传流程。

## 5. 验证与交付
1. **端到端脚本**
   - 脚本：`scripts/e2e_test.py --image data/covers/demo.jpg`; 自动调用 API 并打印耗时。
   - 验证：确认总耗时 ≤ 10s，返回字段齐全。
2. **手动场景回归**
   - 桌面与移动浏览器各上传 2 张实拍图；记录截图与日志 ID。
3. **文档交付**
   - 产出：`README.md`（启动/使用说明）、`docs/mvp_user_guide.md`（操作流程）、`docs/model_notes.md`.

## 6. 里程碑建议
| 周期 | 目标 | 验收 |
|------|------|------|
| Week 1 | 完成环境、数据采集、模型下载 | `docker compose up` 成功；OCR 脚本跑通 |
| Week 2 | 后端路由 + 推理流水线联调 | `POST /upload` + `GET /result` 通畅 |
| Week 3 | 前端 UI & API 集成 | 浏览器端可上传、查看结果 |
| Week 4 | 端到端验证、文档交付 | `scripts/e2e_test.py` 通过；完成 README |
