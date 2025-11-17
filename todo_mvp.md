# CoverOCR MVP Todo List

> 目标：复用公开 OCR/字体模型，跑通“上传 → 文字识别 → 字体输出”链路，满足演示需求。

## 1. 基础环境
1. 初始化仓库结构：`frontend/`, `backend/`, `models/`, `scripts/`.
2. 准备 `start_local.sh`，支持一键启动 FastAPI + Vite。
3. 配置 `.env`（如 `VITE_API_BASE_URL`、允许 CORS 的源等）；可选地准备 `infra/.env` 以便未来扩展 MinIO/PG。

## 2. 数据与模型（MVP）
1. 不再采集封面分类数据，直接复用 PaddleOCR 官方中文检测+识别模型，下载至 `models/weights/paddleocr`.
2. 复用 PaddleClas 字体识别模型（或其他公开字体模型），覆盖宋体/黑体/仿宋/楷体/Arial/Times 等常见字体。
3. 编写 `scripts/download_models.sh` 或 README 说明，记录模型权重下载方式与存放路径。

## 3. 后端 FastAPI
1. `POST /api/v1/upload`：接收图片，返回 `request_id`；可先存内存，后续再接入 MinIO。
2. `GET /api/v1/result/{request_id}`：返回文字行、字体标签、置信度、耗时。
3. 推理流水线：调用 PaddleOCR 完成文字检测+识别，再将裁剪块输入字体模型；无需封面分类。
4. 视需要加入缓存或对象存储；若暂不集成 MinIO/PG，可将结果保存在内存字典中。

## 4. 前端 React (Vite + AntD)
1. 布局：左侧上传（AntD Upload/Dragger），右侧 Tabs 展示文字列表与字体概览。
2. 上传后轮询 `GET /result`，显示文字内容、字体标签、置信度及耗时；提供错误提示与重试。
3. 后续可扩展画布预览、高亮文字框等交互。

## 5. 验证与交付
1. 端到端脚本：随机选择封面图，调用 API，确认 10 秒内返回并输出文字+字体。
2. 浏览器手动测试：桌面/移动端上传实拍封面，截图演示结果。
3. 文档：更新 README、架构/实施文档，描述“复用 PaddleOCR/字体模型即可跑通演示”的方案。
