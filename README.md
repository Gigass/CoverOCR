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

## 技术实现演进与核心方案

本项目从最初的规则系统演进到高精度的机器学习方案，经历了一个完整的探索过程。以下是我们的实现思路、走过的弯路以及最终确定的方案。

### 1. 核心难点：实拍场景下的字号识别

在实拍场景下识别字号（Point Size）面临一个巨大的物理挑战：**拍摄距离的不确定性**。
- 同一本书，近距离拍摄时文字像素高度大，远距离拍摄时像素高度小。
- 传统的 OCR 只返回像素坐标，无法直接换算成物理尺寸（磅数）。

### 2. 演进之路（我们走过的弯路）

#### 阶段一：固定比例法（Naive Approach）
我们最初尝试使用一个固定的转换系数 `k`：
$$ \text{Point Size} = \text{Pixel Height} \times k $$
- **结果**：失败。
- **原因**：无法处理拍摄距离变化。一张图里的 16pt 文字可能高 50px，另一张图里可能只有 30px。

#### 阶段二：动态规则法（Heuristic Approach）
为了解决距离问题，我们引入了"动态 DPI"概念，利用图像宽度与书本物理宽度的比例来推算 DPI。同时，根据文本特征（如全大写、中文/英文）调整系数。
- **结果**：有所改善，但不够精准（MAE ~7.5pt）。
- **原因**：OCR 的检测框（Bounding Box）并不总是紧贴文字。对于"人工智能"（中文）和 "Artificial"（英文），OCR 框的松紧度不同，导致高度计算存在固有噪声。

### 3. 最终方案：基于锚点的机器学习回归

为了彻底解决上述问题，我们确定了 **"锚点归一化 + 机器学习回归"** 的最终方案。

#### 3.1 核心思想：锚点归一化 (Anchor-based Normalization)
我们发现，无论拍摄距离多远，**同一张图内**不同文字的**相对大小**是恒定的。
我们选取书名 **"人工智能与机器学习"** 作为**锚点（Anchor）**。
- 即使拍摄距离改变，其他文字高度与书名高度的**比值**是不变的。
- 我们构建了核心特征：`height_ratio_to_anchor = bbox_height / anchor_height`。

**这是解决"远景导致字体错误"的关键一招。**

#### 3.2 机器学习模型的应用

我们使用了两个独立的 ML 模型来分别解决不同问题：

**A. 字体分类 (ResNet18)**
- **任务**：识别宋体、黑体、Times New Roman 等。
- **实现**：微调 ResNet18 视觉模型。
- **数据**：从 52 张实拍图中裁剪出 364 个文字图像片段。
- **预处理**：图像缩放、归一化、数据增强（旋转、模糊）。

**B. 字号回归 (RandomForest)**
- **任务**：精准预测字号（Point Size）。
- **实现**：RandomForestRegressor（随机森林回归）。
- **输入特征**：
  - `height_ratio_to_anchor` (锚点比率，权重 57%)
  - `bbox_width`, `bbox_height` (几何特征)
  - `text_length` (文本长度)
  - `is_chinese`, `is_all_caps` (文本属性)
- **数据预处理技术**：
  1.  **缺失值处理**：训练时自动过滤未检测到锚点的图片。
  2.  **异常值处理**：通过与模板的精确文本匹配（Exact Match）过滤掉 OCR 识别错误的样本，确保训练数据纯净。
  3.  **归一化 (Normalization)**：通过锚点比率消除尺度差异。
  4.  **独热编码 (One-Hot Encoding)**：将 `is_chinese`、`is_all_caps` 等类别特征编码为数值特征供模型使用。

### 4. 最终效果

通过这套方案，我们将字号识别的平均误差（MAE）从 **7.55pt** 降低到了 **0.03pt**，实现了质的飞跃。

---

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
