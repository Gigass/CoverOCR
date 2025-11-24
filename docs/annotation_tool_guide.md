# CoverOCR 增强版标注工具使用指南

## 🎯 工具特点

✅ **完全离线运行** - 无需后端服务
✅ **自动保存** - 数据存储在浏览器本地
✅ **一键打包** - 导出 ZIP 文件（图片 + 标注）
✅ **即开即用** - 双击 HTML 文件即可使用

## 📦 导出的数据集结构

```
coverocr_dataset_20241124.zip
├── images/                    # 原始图片
│   ├── book_001.jpg
│   ├── book_002.jpg
│   └── ...
├── annotations/               # 标注文件
│   └── dataset.json
└── README.md                 # 使用说明
```

## 🚀 快速开始

### 1. 打开工具

```bash
open annotation_tool_standalone.html
```

或直接双击文件在浏览器中打开。

### 2. 标注流程

#### 步骤 1：上传图片
- 点击 "📤 上传图片"
- 选择教材封面照片

#### 步骤 2：添加文字区域
- 点击 "✏️ 手动添加区域"
- 在图片上拖动鼠标框选文字

#### 步骤 3：填写标注
- **文字内容**：输入识别的文字
- **字体类别**：选择字体（宋体、黑体、楷体等）
- **字号名称**：选择字号（初号、一号、小四等）
- **磅值**：输入实际磅值（如 22、12）
- **置信度**：选择标注的确定程度

#### 步骤 4：保存
- 点击 "💾 保存"

#### 步骤 5：继续标注
- 重复步骤 1-4，标注所有图片

### 3. 导出数据

#### 方式 A：导出完整数据集（推荐）

点击 **"📦 导出完整数据集"**

- ✅ 包含图片和标注
- ✅ 一个 ZIP 文件搞定
- ✅ 解压后直接可用

#### 方式 B：仅导出标注

点击 **"💾 仅导出标注"**

- ⚠️ 只有 JSON 文件
- ⚠️ 需要手动复制图片

## 📥 导入项目

### 使用完整数据集（推荐）

```bash
cd /Users/gigass/DEVELOP/GitHub/CoverOCR

# 1. 解压下载的 ZIP 文件
unzip ~/Downloads/coverocr_dataset_*.zip -d /tmp/

# 2. 复制到项目
cp -r /tmp/coverocr_dataset/images data/
cp -r /tmp/coverocr_dataset/annotations data/

# 3. 验证数据
python scripts/check_dataset.py

# 4. 清理临时文件
rm -rf /tmp/coverocr_dataset
```

### 使用仅标注文件

```bash
# 1. 手动复制图片（假设在 ~/Desktop/book_images/）
mkdir -p data/images
cp ~/Desktop/book_images/* data/images/

# 2. 复制标注文件
mkdir -p data/annotations
mv ~/Downloads/coverocr_annotations_*.json data/annotations/dataset.json

# 3. 验证数据
python scripts/check_dataset.py
```

## 💡 使用技巧

### 1. 定期备份

每标注 10 张图片，点击"导出完整数据集"备份一次。

### 2. 批量标注

- 先标注所有图片的文字区域（框选）
- 再逐个填写标注信息
- 这样效率更高

### 3. 使用快捷键

- 标注时可以用 Tab 键在表单字段间切换
- Enter 键保存当前标注

### 4. 标注一致性

- 同一本书的相同文字应该标注相同的字体和字号
- 使用"备注"字段记录特殊情况

### 5. 字号测量

参考 `docs/annotation_guide.md` 中的测量方法：

**方法 1：计算法**
```
1. 测量书本实际宽度（如 18.5cm）
2. 测量照片中书本的像素宽度（如 800px）
3. 计算 DPI：800 / (18.5/2.54) = 109.9
4. 测量文字高度（像素）：如 50px
5. 计算磅值：50 * (72/109.9) = 32.7pt
```

**方法 2：对照表**

| 字号 | 磅值 | 常见用途 |
|------|------|---------|
| 初号 | 42pt | 封面标题 |
| 一号 | 26pt | 主标题 |
| 二号 | 22pt | 大标题 |
| 小二 | 18pt | 标题 |
| 三号 | 16pt | 标题 |
| 小四 | 12pt | 正文 |
| 五号 | 10.5pt | 正文 |

## ⚠️ 注意事项

### 1. 浏览器兼容性

- ✅ Chrome / Edge（推荐）
- ✅ Firefox
- ✅ Safari
- ❌ IE（不支持）

### 2. 数据安全

- 数据存储在浏览器 LocalStorage
- **清除浏览器缓存会丢失数据**
- **定期导出备份**

### 3. 文件大小限制

- 单张图片建议 < 5MB
- 总数据量建议 < 500MB
- 如果图片太多，分批标注

### 4. 导出时间

- 10 张图片：约 5 秒
- 50 张图片：约 20 秒
- 100 张图片：约 40 秒

## 🐛 常见问题

### Q1：导出时卡住了？

**A**：可能是图片太多或太大。建议：
- 分批标注（每次 20-30 张）
- 压缩图片后再上传

### Q2：标注数据丢失了？

**A**：检查是否清除了浏览器缓存。建议：
- 定期导出备份
- 使用同一个浏览器

### Q3：无法打开 ZIP 文件？

**A**：确保：
- 导出完成后再下载
- 使用解压软件（如 The Unarchiver）

### Q4：图片尺寸不匹配？

**A**：可能是图片被压缩了。建议：
- 使用原始照片
- 不要在上传前编辑图片

## 📊 数据质量检查

导入数据后，运行检查脚本：

```bash
python scripts/check_dataset.py
```

检查内容：
- ✅ 所有图片文件是否存在
- ✅ 标注数量是否匹配
- ✅ 边界框坐标是否合法
- ✅ 字号是否在合理范围内

## 🎯 下一步

标注完成后：

1. **验证数据**：
   ```bash
   python scripts/check_dataset.py
   ```

2. **训练模型**（后续）：
   ```bash
   python scripts/train_font_classifier.py
   python scripts/train_size_regressor.py
   ```

3. **评估效果**：
   ```bash
   python scripts/evaluate_model.py
   ```

## 📞 技术支持

如有问题，请查看：
- `docs/annotation_guide.md` - 详细标注指南
- `docs/data_workflow.md` - 数据工作流程

---

**祝标注顺利！** 🎉
