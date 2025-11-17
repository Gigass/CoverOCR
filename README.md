# CoverOCR MVP

CoverOCR 是一个面向教材/参考书封面的端到端识别系统，支持实拍图像的书名、文字与字体识别。本仓库包含：

- `backend/`：FastAPI 服务，提供上传与结果查询接口，并内置占位推理流水线。
- `frontend/`：Vite + React + Ant Design 前端，支持拖拽上传与识别结果展示。
- `infra/`：Docker Compose 配置，以及 `.env` 示例。
- `docs/`：需求、架构设计、实施计划等文档。

## 开发环境

### 一键启动
```bash
./start_local.sh
```
脚本会自动创建 `.venv`、安装后端依赖、确保前端 `node_modules` 存在，并分别在 `http://localhost:8000` 与 `http://localhost:5173` 启动 FastAPI 与 Vite。按 `Ctrl+C` 结束。

> 首次运行时会自动下载 PaddleOCR/PaddleClas 依赖以及示例字体（Noto Sans/Serif SC、霞鹜文楷等，存放于 `models/fonts/`，共 ~40MB），耗时较长属正常现象。

### 后端
```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r backend/requirements.txt
uvicorn app.main:app --reload --app-dir backend
```

### 前端
```bash
cd frontend
npm install
npm run dev
```

默认环境变量可通过 `frontend/.env.example`、`infra/.env.example` 复制生成。

## Docker Compose
```bash
cd infra
cp .env.example .env
docker compose up --build
```

- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/v1
- MinIO 控制台：http://localhost:9001

## 测试

### 后端
```bash
source .venv/bin/activate
pytest backend/tests
```

### 前端
```bash
cd frontend
npm run build
```

## 文档
- `markdown_export.md`：需求。
- `architecture_design.md`：技术栈与架构设计。
- `implementation_plan_v1.md`、`todo_mvp.md`：实现计划与待办。
