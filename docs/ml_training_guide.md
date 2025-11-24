# 机器学习模型训练与评估指南

## 概述

本项目实现了两个机器学习模型用于书籍封面的排版属性识别：
1. **字体分类模型**（ResNet18）
2. **字号回归模型**（RandomForest）

## 数据准备

### 训练数据
- **位置**: `data/aiphoto/` (52 张书籍封面图片)
- **标注**: `data/annotations/auto_bbox_with_fonts.json` (OCR 结果 + bbox)
- **模板**: `data/annotations/template_cover.json` (真实字体和字号标签)

### 数据特点
- 所有图片拍摄自同一本书《人工智能与机器学习》
- 每张图包含 7 个固定文本区域
- 总样本数：364 (52 × 7)

## 模型 1: 字体分类（ResNet18）

### 训练步骤

```bash
# 1. 准备训练数据（裁剪文字区域并按字体分类）
python scripts/prepare_font_data.py

# 2. 训练模型
python scripts/train_font_classifier.py

# 输出：
# - models/custom_font_classifier/font_resnet18.pdparams
# - models/custom_font_classifier/class_mapping.json
```

### 模型架构
- **基础模型**: ResNet18 (预训练)
- **输出层**: 5 个类别（黑体、宋体、华文细黑、Helvetica、Times New Roman）
- **数据增强**: 旋转、颜色抖动、亮度变化

### 性能指标
- **训练准确率**: ~84%
- **测试准确率**: 86.26%
- **模型大小**: 45MB

## 模型 2: 字号回归（RandomForest）

### 训练步骤

```bash
# 训练模型
python scripts/train_point_size_model.py

# 输出：
# - models/point_size_model/xgboost_model.pkl (实际是 RandomForest)
```

### 核心特征

#### 1. 锚点归一化特征（最重要）
```python
'height_ratio_to_anchor': bbox_height / anchor_height
```
- **anchor**: 书名"人工智能与机器学习"的高度
- **作用**: 消除拍摄距离的影响

#### 2. 文本特征
- `text_length`: 文本字符数
- `is_chinese`: 是否包含中文
- `is_all_caps`: 是否全大写
- `is_title_case`: 是否首字母大写

#### 3. 几何特征
- `bbox_height`, `bbox_width`: 检测框尺寸
- `aspect_ratio`: 宽高比
- `relative_height`: 相对于图片宽度的高度

### 性能指标
- **测试 MAE**: 0.08 pt
- **测试 R²**: 0.992
- **Size Name Accuracy**: 98.08%
- **模型大小**: ~1MB

### 特征重要性
1. `text_length`: 57.4%
2. `bbox_width`: 34.5%
3. `is_chinese`: 5.4%
4. `height_ratio_to_anchor`: 1.7%

## 评估

```bash
# 运行完整评估
python scripts/evaluate_typography.py

# 输出示例：
# Total Samples: 364
# Font Family Accuracy: 86.26%
# Size Name Accuracy:   98.08%
# Point Size MAE:       0.03 pt
```

## 模型集成

### 自动加载
模型在服务启动时自动加载：

```python
# backend/app/services/typography.py
class TypographyEstimator:
    def __init__(self):
        # 加载字体分类模型
        self.font_classifier = FontClassifier()  # 自动加载 ResNet18
        
        # 加载字号回归模型
        self.ml_model = load_model("models/point_size_model/xgboost_model.pkl")
```

### 推理流程

```python
# backend/app/services/pipeline.py
def _run_pipeline(self, ...):
    # 1. 找到锚点（书名）
    anchor_height = find_anchor(regions)
    
    # 2. 对每个文字区域
    for region in regions:
        typo_result = self._typography_estimator.estimate(
            text=region.text,
            crop=region.crop,
            box=region.box,
            image_width=image_width,
            anchor_height=anchor_height  # 传递锚点
        )
```

## 局限性与改进方向

### 当前局限
1. **单书籍特化**: 模型只在一本书上训练，泛化能力有限
2. **依赖锚点**: 需要识别出"人工智能与机器学习"作为参照
3. **小样本**: 仅 364 个样本

### 改进方向
1. **多书籍训练**:
   - 收集 100+ 本不同书籍的封面
   - 扩充字体类别和字号范围
   
2. **端到端深度学习**:
   - 直接从图像预测字号（CNN + Regression）
   - 无需依赖 OCR 框的准确性

3. **自适应锚点**:
   - 自动检测最大/最显眼的文字作为锚点
   - 或使用多个锚点的加权平均

## 故障排查

### 模型未加载
```bash
# 检查模型文件是否存在
ls -lh models/custom_font_classifier/
ls -lh models/point_size_model/

# 查看日志
# 应该看到: "[TypographyEstimator] ML model loaded successfully."
```

### 准确率下降
- 检查是否传递了 `anchor_height`
- 验证图片是否来自同一本书
- 查看 OCR 是否正确识别了书名

## 参考文献

- PaddleOCR: https://github.com/PaddlePaddle/PaddleOCR
- PaddleClas: https://github.com/PaddlePaddle/PaddleClas
- RandomForest: https://scikit-learn.org/stable/modules/ensemble.html#forest
