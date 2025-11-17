# CoverOCR 技术栈与架构设计（V1.0）

## 1. 文档目的
- 将业务需求转化为可落地的技术方案，确保封面/文字/字体识别链路与上传体验能在 10 秒内完成。
- 指导研发团队快速搭建 MVP，并为后续扩展（新增书籍、字体、语言）留出接口。

## 2. 技术栈设计

### 2.1 语言与框架
| 层级 | 技术 | 选择理由 |
|------|------|----------|
| 前端 GUI | **React + Vite + TypeScript**, Ant Design 组件库 | 生态成熟，上手快；AntD 提供上传、结果卡片、Skeleton 等控件；Vite 支持快速迭代。 |
| 后端 API | **FastAPI (Python 3.11)** | 异步 IO 适合并发上传；Pydantic 便于构建请求/响应模型；与 Python ML 生态无缝衔接。 |
| 模型训练 | **PyTorch + PyTorch Lightning** | Lightning 规范化训练流程，便于复现；PyTorch 具备丰富的预训练模型。 |
| 推理服务 | **TorchServe / FastAPI 内嵌推理 + ONNX Runtime（可选）** | TorchServe 支持 GPU Batch 推理；ONNX Runtime 可在 CPU 环境加速。 |
| 数据标注 | **Label Studio / Roboflow** | 快速构建文字区域、字体标签，支持协作。 |
| 任务编排 | **Prefect / Airflow（可按需）** | 统一训练、评估、部署流水线。 |

### 2.2 模型与库
| 模块 | 建议模型/库 | 补充说明 |
|------|-------------|----------|
| 封面分类 | **EfficientNet-B3 / ConvNeXt-Tiny** 预训练 -> Fine-tune | 输入归一化为 384×384，分类头输出书目 ID；Top-1≥85%。 |
| 文字检测 | **PP-OCRv4 Detection (PaddleOCR) / DBNet++** | 预训练模型适配实拍场景，支持仿射/光照增强。 |
| 文字识别 | **PARSeq / SVTR-LCNet** | 支持中英文混排，部署时可蒸馏为轻量版以满足时延。 |
| 字体识别 | **Vision Transformer (ViT-S) / ResNet50** | 输入为裁剪文字块+背景；输出常见字体类别。 |
| OCR Pipeline | **PaddleOCR / MMOCR 组件** | 结合检测与识别模块，并提供训练脚本。 |
| 数据增强 | Albumentations, TorchVision Augmentations | 包含透视、亮度、噪声、模糊、CutMix。 |

### 2.3 数据与存储
| 功能 | 技术 | 说明 |
|------|------|------|
| 训练数据存储 | **MinIO / S3 兼容对象存储** | 统一管理原始与标注图像，支持版本化。 |
| 元数据/标签 | **PostgreSQL** | 存储书目、字体、标注任务状态；JSONB 字段记录检测框。 |
| 嵌入检索（可选） | **Milvus / FAISS** | 用于封面相似度搜索、近似匹配。 |
| 配置与实验 | **DVC + Git** | 跟踪数据版本和模型权重；实验参数写入 YAML。 |

### 2.4 部署与基础设施
- **容器化**：使用 Docker 打包前端、后端、推理服务；通过 Docker Compose 或 Kubernetes 管理。
- **硬件**：推理节点建议配备 1×NVIDIA T4/A10；CPU 场景可使用 ONNX INT8 模型。
- **CI/CD**：GitHub Actions 进行单元测试、模型精度校验、Docker 构建；推送至私有容器仓库。
- **监控**：Prometheus + Grafana 监测 QPS、时延、GPU 利用率；Sentry 捕获前端/后端异常。

## 3. 系统架构设计

### 3.1 总体架构
```
用户浏览器
    │
    ▼
React GUI (Vite) ──> FastAPI 网关 ──> 推理编排器
                                    │
               ┌────────────────────┼────────────────────┐
               ▼                    ▼                    ▼
        封面分类服务         OCR 检测+识别服务       字体分类服务
               │                    │                    │
               └─────────► 结果融合器 ◄──────────────────┘
                                    │
                            PostgreSQL / MinIO
```
- **推理编排器**：一个 Python Service（可内置于 FastAPI 或独立微服务），负责调用各个模型、缓存结果，并执行超时控制（<10s）。
- **结果融合器**：统一封面 ID、文字行列表、字体标签，并返回给前端。
- **数据持久层**：存储上传历史、推理日志与模型版本信息，方便回溯与再训练。

### 3.2 模块划分
| 模块 | 功能 | 输入/输出 |
|------|------|-----------|
| Upload Handler | 接收上传图像，进行尺寸/类型校验，写入对象存储 | 输入：JPG/PNG；输出：预处理后图像路径 |
| Preprocessor | 图像重采样、去噪、颜色校正、矩形校正 | 输入：原图；输出：标准化 Tensor |
| Cover Classifier | 预测书目 ID，返回 Top-K 候选及置信度 | 输入：标准化图像 | 输出：`[(book_id, score)]` |
| Text Detector | 产出文本区域多边形 | 输入：标准化图像 | 输出：`List[Polygon]` |
| Text Recognizer | 逐区域识别文字 | 输入：裁剪文字块 | 输出：`List[str]` |
| Font Classifier | 预测字体类别 | 输入：裁剪文字块 | 输出：`List[font_label]` |
| Result Aggregator | 将书名候选、文字行、字体标签映射为 API 响应 | 输入：各模块输出 | 输出：JSON 结构 |
| Admin Console（非必需 MVP） | 标注审核、模型状态监控 | 输入：用户操作 | 输出：管理报告 |

### 3.3 关键流程（推理路径）
1. **上传阶段**：前端使用 AntD `Upload` 组件；文件通过 FastAPI `POST /api/v1/upload` 上传。限制 20MB，自动生成请求 ID。
2. **预处理**：后端进行 EXIF 旋转校正、尺寸缩放 (短边 640)、直方图均衡；缓存至 `/tmp` 或 Redis。
3. **封面分类**：推理编排器先运行封面分类模型以确定 Top-K 候选书籍，供最终结果匹配。
4. **文字检测与识别**：对原图运行检测模型，遍历区域调用识别模型；可使用批量推理以缩短时延。
5. **字体识别**：用与文字识别相同的裁剪结果输入字体分类器，输出字体标签和置信度。
6. **结果融合与返回**：生成结构化 JSON，包括书名、ISBN（如有）、每段文字、字体、置信度、耗时。前端展示卡片、表格及 OCR 区域高亮。

## 4. 图形界面设计要点
- **布局**：左右两栏。左侧为上传、拍照指南、历史记录；右侧显示图像预览与识别结果。
- **关键组件**：
  - `UploadCard`：支持拖拽、拍照（移动端调起相机），展示上传进度条。
  - `PreviewCanvas`：用 fabric.js 或 Konva 渲染文字框，点击高亮对应结果行。
  - `ResultTabs`：Tab1 显示书籍识别（Top-K 列表）；Tab2 显示文字内容（表格，可复制）；Tab3 显示字体分布（标签云 / 柱状图）。
  - `LatencyIndicator`：顶部显示总耗时，>8s 时提示“建议重新拍摄”。
- **交互细节**：上传后展示 Skeleton，结果到齐前逐步填充；失败时提供重试按钮并上传日志 ID。

## 5. 快速实现路线（MVP）
1. **模型复用**：首版直接使用 PaddleOCR 提供的中文通用检测+识别模型；封面分类使用预训练 EfficientNet，少量图片即可微调。
2. **部署**：单机 Docker Compose：`frontend`（Vite 编译后 Nginx 静态），`api`（FastAPI+Uvicorn），`inference`（TorchServe）。GPU 不可用时，将模型导出 ONNX 并启用 INT8 推理。
3. **数据闭环**：所有上传样本及识别结果写入 MinIO + PostgreSQL，供后续人工审核与再训练。
4. **性能优化**：并行化 OCR 识别（多线程或异步任务），缓存常见书籍的封面嵌入；必要时用消息队列（Redis Streams）隔离上传与推理。

## 6. 验收指标对应
| 需求项 | 技术实现映射 |
|--------|--------------|
| 封面识别准确率 ≥85% | EfficientNet + 数据增强 + Top-K 召回；必要时结合嵌入检索。 |
| 文字识别准确率 ≥80% | 选择 PaddleOCR / PARSeq，并对数据集进行仿射、噪声增强；引入语言模型纠错。 |
| 字体识别准确率 ≥70% | ViT/ResNet 字体分类器 + 字体数据集扩增；结果附置信度提示。 |
| 10 秒内返回 | FastAPI 异步 + 并行推理 + 模型量化；超时控制与性能监控。 |
| 实拍鲁棒性 | 预处理模块 + 数据增强；在数据集内涵盖角度、光照、多背景样本。 |

## 7. 后续扩展
- 新增书籍：通过 Admin Console 上传新书封面及信息，触发再训练流水线。
- 新语言：在 OCR 识别模块加载多语言模型，并扩充字体分类器标签。
- 移动端：封装 React Native 或 Flutter 壳，将 FastAPI 暴露的 REST API 直接复用。
- SaaS 化：多租户隔离、鉴权（JWT + OAuth2），并加入计费与限流。

> 以上方案兼顾快速落地与长远扩展，团队可按此文档拆解任务、搭建开发环境并启动实现。
