# CoverOCR MVP Todo List

> 目标：在保证需求闭环的前提下实现最小可用版本，后续再做性能与精度优化。

## 1. 基础环境
1. 初始化仓库结构：`frontend/`, `backend/`, `models/`, `data/`.
2. 编写 `docker-compose.yml`，包含 FastAPI、推理服务、MinIO、PostgreSQL（可使用官方镜像）。
3. 配置 `.env`（API 密钥、存储路径、数据库连接）。

## 2. 数据与模型（MVP）
1. 收集/下载公开教材封面（至少 5-10 本，每本 5 张）并整理为 `data/covers`.
2. 采用 PaddleOCR 官方中文检测+识别模型，验证推理脚本；封面分类使用预训练 EfficientNet-B3，仅替换分类头后微调。
3. 字体识别 MVP：暂用合成字体样本生成的小模型（ResNet18），支持宋体/黑体/仿宋/楷体/Arial/Times 六类。
4. 将模型权重放置在 `models/weights/`，并记录下载脚本。

## 3. 后端 FastAPI
1. 实现 `POST /api/v1/upload` 接口：接收图片，保存到 `/tmp/uploads`，返回 `request_id`.
2. 实现 `GET /api/v1/result/{request_id}`：返回封面、文字、字体识别结果（JSON）。
3. 集成推理流水线：顺序调用封面分类 -> OCR -> 字体识别，并聚合结果；保证 10 秒内返回超时控制。
4. 将 MinIO 作为对象存储，将上传图像与结果 JSON 写入存档。

## 4. 前端 React (Vite + AntD)
1. 页面布局：左侧上传（AntD Upload），右侧结果展示（Tabs）。
2. 上传成功后轮询 `GET /result` 接口；显示书名候选、文字表格、字体标签。
3. 结果页显示总耗时与高亮提示；失败时提供重试按钮。

## 5. 验证与交付
1. 编写端到端脚本：随机选取一张本地封面，调用 API，确认 10 秒内返回。
2. 前端手动测试：在桌面/移动浏览器上传实拍图像，截图记录效果。
3. 撰写 MVP 使用说明：如何启动 Docker、上传图片、查看结果。
