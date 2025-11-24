# CoverOCR V2.0 改造方案与执行清单

基于最新的 V2.0 需求文档，我们需要对现有项目进行以下改造。核心目标是引入机器学习数据预处理流程，并增强排版属性（字体、字号、磅值）的识别能力。

## 一、 核心改造点概览

1.  **数据预处理 (强制要求)**: 必须在代码中显式实现缺失值处理、异常值处理、归一化和独热编码。
2.  **排版属性识别 (增强)**: 从单纯的字体分类升级为“字体+字号+磅值”的多任务预测。
3.  **结果格式化**: 输出格式需严格遵循 `【字号名，字体名，固定值 X 磅】`。

---

## 二、 详细执行清单 (Action Items)

### 1. 数据与预处理模块 (Backend - Data Processing)
> **目标**: 构建符合机器学习标准的预处理流水线。

- [ ] **创建目录结构**: `backend/app/data_processing/`
- [ ] **实现缺失值/异常值处理器 (`cleaner.py`)**:
    - [ ] 编写函数 `handle_missing_values(data, strategy='mean')`: 处理标注数据中的 NaN。
    - [ ] 编写函数 `remove_outliers(data, column, method='iqr')`: 基于 IQR 或 Z-Score 剔除异常样本。
- [ ] **实现归一化/标准化器 (`normalizer.py`)**:
    - [ ] 编写函数 `normalize_image(image_array)`: 将像素值缩放到 [0, 1] 或 [-1, 1]。
    - [ ] 编写函数 `standardize_labels(numerical_labels)`: 对磅值等连续标签进行 StandardScaler 处理。
- [ ] **实现编码器 (`encoder.py`)**:
    - [ ] 编写函数 `encode_one_hot(categorical_labels)`: 对字体类别、字号名称进行 One-Hot 编码。
- [ ] **单元测试**: 为上述模块编写 `tests/test_data_processing.py`，确保逻辑正确。

### 2. 模型与推理服务 (Backend - Services)
> **目标**: 升级推理管道以支持详细排版属性。

- [ ] **排版属性估算器 (`typography_model.py`)**:
    - [ ] *方案 A (理想)*: 定义一个多头神经网络结构 (Multi-head CNN)，分别输出 Font(Class), Size(Class), Point(Reg)。
    - [ ] *方案 B (MVP快速实现)*: 
        - 字体：复用 PaddleClas。
        - 字号/磅值：基于检测框高度 (Box Height) + 图像 DPI 估算，结合启发式规则映射到标准字号（如“小四”）。
    - [ ] 封装 `predict_typography(image_crop)` 接口。
- [ ] **更新推理流水线 (`pipeline.py`)**:
    - [ ] 在 OCR 识别出文字后，调用 `predict_typography`。
    - [ ] 将结果组装成 `TypographyResult` 对象。

### 3. API 与数据模型 (Backend - API)
> **目标**: 更新接口定义以返回新的结果格式。

- [ ] **更新 Pydantic 模型 (`schemas.py`)**:
    - [ ] 新增字段 `font_family` (str), `font_size_name` (str), `point_size` (float)。
    - [ ] 更新响应模型 `OCRResultResponse`。
- [ ] **结果格式化**:
    - [ ] 在 API 返回前，将属性格式化为字符串：`"【{size_name}，{font}，固定值 {point} 磅】"`。

### 4. 前端展示 (Frontend)
> **目标**: 适配新的结果展示格式。

- [ ] **更新结果卡片组件**:
    - [ ] 修改结果列表项，清晰展示“文字内容”与“排版属性”。
    - [ ] (可选) 增加视觉区分，例如用不同颜色标签显示字体和字号。

---

## 三、 推荐实施步骤

1.  **Step 1 (基础)**: 先完成 `backend/app/data_processing/` 下的三个预处理脚本（Cleaner, Normalizer, Encoder）并通过测试。这是 V2.0 的核心考核点。
2.  **Step 2 (模型)**: 实现一个基于规则+模型的 `TypographyEstimator`，先跑通流程，确保能输出磅值和字号名。
3.  **Step 3 (集成)**: 修改后端 Pipeline 和 API，串联所有模块。
4.  **Step 4 (UI)**: 更新前端界面。

请确认是否按照此清单开始执行 **Step 1**？
