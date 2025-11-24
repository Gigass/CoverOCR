# CoverOCR 数据标注完整指南

## 📦 最终数据集结构

```
CoverOCR/data/
├── images/                    # 原始图片（必需！）
│   ├── book_001.jpg
│   ├── book_002.jpg
│   ├── book_003.jpg
│   └── ...
├── annotations/               # 标注文件（JSON）
│   └── dataset.json          # 汇总标注文件
└── README.md                 # 数据集说明
```

## 🔄 完整工作流程

### 步骤 1：准备图片

1. **收集图片**：
   ```bash
   # 创建临时文件夹
   mkdir ~/Desktop/book_images
   
   # 将所有要标注的教材封面照片放入这个文件夹
   # 建议命名：book_001.jpg, book_002.jpg, ...
   ```

2. **图片要求**：
   - 格式：JPG 或 PNG
   - 分辨率：宽度 > 1500px（推荐）
   - 清晰度：文字清晰可辨
   - 角度：尽量正面拍摄，减少透视

### 步骤 2：使用标注工具

1. **打开工具**：
   ```bash
   open /Users/gigass/DEVELOP/GitHub/CoverOCR/annotation_tool_standalone.html
   ```

2. **逐张标注**：
   - 点击"📤 上传图片"，选择 `book_001.jpg`
   - 点击"✏️ 手动添加区域"，在图片上框选文字
   - 填写标注信息（文字内容、字体、字号、磅值）
   - 点击"💾 保存"
   - 重复以上步骤，标注所有文字区域
   - 继续上传下一张图片

3. **定期备份**：
   - 每标注 10 张，点击"💾 导出所有标注"
   - 保存为 `backup_001.json`、`backup_002.json` 等

### 步骤 3：导出最终数据

1. **导出标注**：
   - 标注完成后，点击"💾 导出所有标注"
   - 保存为 `coverocr_annotations_final.json`

2. **文件说明**：
   - 这个 JSON 文件包含所有标注信息
   - **但不包含图片数据**（图片太大，浏览器无法处理）
   - 图片仍然在 `~/Desktop/book_images/` 文件夹中

### 步骤 4：导入项目

```bash
cd /Users/gigass/DEVELOP/GitHub/CoverOCR

# 1. 创建数据目录
mkdir -p data/images
mkdir -p data/annotations

# 2. 复制图片（重要！）
cp ~/Desktop/book_images/* data/images/

# 3. 复制标注文件
mv ~/Downloads/coverocr_annotations_final.json data/annotations/dataset.json

# 4. 验证数据
ls data/images/      # 应该看到所有图片
cat data/annotations/dataset.json | jq '.total_images'  # 应该显示图片数量
```

## 📋 数据集格式说明

### dataset.json 结构

```json
{
  "version": "2.0",
  "export_date": "2024-01-15T10:30:00.000Z",
  "total_images": 50,
  "images": [
    {
      "image_path": "images/book_001.jpg",
      "image_width": 1920,
      "image_height": 2560,
      "book_size": "16k",
      "book_width_cm": 18.5,
      "annotations": [
        {
          "id": 0,
          "text": "人工智能与机器学习",
          "bbox": [120, 450, 680, 550],
          "font_family": "黑体",
          "font_size_name": "初号",
          "point_size": 42,
          "confidence": "high",
          "notes": ""
        }
      ]
    }
  ]
}
```

### 字段说明

- `image_path`: 图片相对路径（如 `images/book_001.jpg`）
- `bbox`: 边界框坐标 `[x_min, y_min, x_max, y_max]`
- `font_family`: 字体类别（宋体、黑体、楷体等）
- `font_size_name`: 字号名称（初号、一号、小四等）
- `point_size`: 磅值（如 42、22、12）
- `confidence`: 标注置信度（high/medium/low）

## 🔧 训练模型时的数据加载

训练脚本会这样使用数据：

```python
import json
from PIL import Image

# 1. 加载标注文件
with open('data/annotations/dataset.json', 'r') as f:
    dataset = json.load(f)

# 2. 遍历每张图片
for img_data in dataset['images']:
    # 3. 加载图片
    img_path = f"data/{img_data['image_path']}"  # data/images/book_001.jpg
    image = Image.open(img_path)
    
    # 4. 遍历每个文字区域
    for annotation in img_data['annotations']:
        # 5. 裁剪文字区域
        bbox = annotation['bbox']  # [x_min, y_min, x_max, y_max]
        crop = image.crop(bbox)
        
        # 6. 获取标签
        font_family = annotation['font_family']  # "黑体"
        point_size = annotation['point_size']    # 42
        
        # 7. 训练模型
        # ...
```

## ⚠️ 重要提醒

### 为什么需要手动复制图片？

1. **浏览器安全限制**：
   - 浏览器无法直接访问本地文件系统
   - 无法将图片保存到指定文件夹
   - 只能下载单个文件（JSON）

2. **图片太大**：
   - 50 张图片可能有 100-200 MB
   - 无法嵌入 JSON 文件
   - 即使用 Base64 编码也会导致文件过大

3. **最佳实践**：
   - **图片和标注分开存储**
   - 标注文件只包含路径引用
   - 训练时动态加载图片

## ✅ 数据完整性检查

导入数据后，运行检查脚本：

```bash
python scripts/check_dataset.py
```

检查内容：
- ✅ 所有图片文件是否存在
- ✅ 标注数量是否匹配
- ✅ 边界框坐标是否合法
- ✅ 字号是否在合理范围内

## 📊 数据统计

标注完成后，您应该有：

- **图片数量**：50-200 张
- **文字区域数量**：250-1000 个
- **标注信息**：
  - 每个区域包含：文字内容、字体、字号、磅值
  - 总数据量：图片 100-400 MB + JSON 1-5 MB

## 🎯 总结

**核心要点**：
1. 标注工具只能导出 **JSON 文件**（标注信息）
2. **图片文件**需要您手动复制到 `data/images/`
3. JSON 中的 `image_path` 字段指向图片位置
4. 训练时，脚本会根据路径加载图片

**完整流程**：
```
标注工具 → 导出 JSON → 手动复制图片 → 导入项目 → 训练模型
```
