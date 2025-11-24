# CoverOCR MVP

CoverOCR 是一个面向教材/参考书封面的端到端识别系统，支持实拍图像的书名、文字与字体识别。本仓库包含：

- `backend/`：FastAPI 服务，提供上传与结果查询接口，并内置占位推理流水线。
- `frontend/`：Vite + React + Ant Design 前端，支持拖拽上传与识别结果展示。
- `infra/`：Docker Compose 配置，以及 `.env` 示例。
- `docs/`：需求、架构设计、实施计划等文档。

## 快速开始

### 方式一：一键启动（推荐）

```bash
# 1. 克隆仓库
git clone <repository-url>
cd CoverOCR

# 2. 一键启动
./start_local.sh
```

脚本会自动：
- 创建 Python 虚拟环境 (`.venv`)
- 安装后端依赖 (`backend/requirements.txt`)
- 安装前端依赖 (`npm install`)
- 启动 FastAPI 服务 (`http://localhost:8000`)
- 启动 Vite 前端 (`http://localhost:5173`)

**首次运行注意**：
- 会自动下载 PaddleOCR/PaddleClas 模型（~200MB）
- 会下载示例字体文件到 `models/fonts/`（~40MB）
- 整个过程可能需要 5-10 分钟

**访问应用**：
- 前端界面：http://localhost:5173
- 后端 API 文档：http://localhost:8000/docs

**停止服务**：
- 按 `Ctrl+C` 或运行 `./stop_local.sh`

### 方式二：手动启动

#### 后端
```bash
# 1. 创建虚拟环境
python3 -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 2. 安装依赖
pip install -r backend/requirements.txt

# 3. 启动服务
cd backend
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### 前端
```bash
# 在新终端窗口

# 1. 安装依赖
cd frontend
npm install

# 2. 启动开发服务器
npm run dev
```

### 方式三：Docker Compose

```bash
cd infra
cp .env.example .env
docker compose up --build
```

访问地址：
- 前端：http://localhost:5173
- 后端 API：http://localhost:8000/api/v1
- MinIO 控制台：http://localhost:9001

## 使用指南

### 1. 上传图片
- 拖拽图片到上传区域
- 或点击上传按钮选择文件
- 支持格式：JPG, PNG
- 建议尺寸：短边 ≥ 640px

### 2. 查看结果
- 等待 2-5 秒处理
- 查看识别的文字内容
- 查看字体、字号、磅数信息
- 格式：`【小四，宋体，固定值 12 磅】`

### 3. 训练自定义模型（可选）

如果你有自己的书籍封面数据：

```bash
# 1. 准备数据
# - 将图片放到 data/aiphoto/
# - 创建标注文件 data/annotations/template_cover.json

# 2. 训练字体分类模型
python scripts/prepare_font_data.py
python scripts/train_font_classifier.py

# 3. 训练字号回归模型
python scripts/train_point_size_model.py

# 4. 评估模型
python scripts/evaluate_typography.py
```

## 环境要求

- **Python**: 3.9+
- **Node.js**: 16+
- **内存**: 建议 ≥ 4GB
- **磁盘**: 建议 ≥ 2GB（包含模型文件）
- **操作系统**: macOS, Linux, Windows

> 首次运行时会自动下载 PaddleOCR/PaddleClas 依赖以及示例字体（Noto Sans/Serif SC、霞鹜文楷等，存放于 `models/fonts/`，共 ~40MB），耗时较长属正常现象。

## 开发

### 后端开发
```bash
source .venv/bin/activate
cd backend
uvicorn app.main:app --reload
```

### 前端开发
```bash
cd frontend
npm run dev
```

### 运行测试

### 运行测试

```bash
# 后端测试
pytest backend/tests

# 前端构建测试
cd frontend && npm run build
```

## 项目结构

```
CoverOCR/
├── backend/              # FastAPI 后端
│   ├── app/
│   │   ├── api/         # API 路由
│   │   ├── services/    # 核心服务（OCR, 字体识别, 字号预测）
│   │   └── schemas/     # Pydantic 模型
│   └── tests/           # 后端测试
├── frontend/            # React + Vite 前端
│   └── src/
├── models/              # 训练好的模型
│   ├── custom_font_classifier/    # ResNet18 字体分类模型
│   └── point_size_model/          # RandomForest 字号回归模型
├── scripts/             # 训练和评估脚本
├── data/                # 训练数据
│   ├── aiphoto/        # 原始图片
│   └── annotations/    # 标注文件
└── docs/                # 文档
```

## 文档
- `markdown_export.md`：需求。
- `architecture_design.md`：技术栈与架构设计。
- `implementation_plan_v1.md`、`todo_mvp.md`：实现计划与待办。

## 核心功能

### 字体识别
- 使用微调的 **ResNet18** 模型
- 针对特定书籍封面训练
- **准确率**: 86.26%

### 字号识别
- 使用 **RandomForest** 回归模型
- 基于锚点归一化的特征工程
- **准确率**: 
  - Point Size MAE: **0.03 pt**
  - Size Name Accuracy: **98.08%**

### 模型训练
```bash
# 训练字体分类模型
python scripts/train_font_classifier.py

# 训练字号回归模型
python scripts/train_point_size_model.py

# 评估模型性能
python scripts/evaluate_typography.py
```
