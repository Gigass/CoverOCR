#!/bin/bash
# 清理项目中的垃圾文件

echo "开始清理垃圾文件..."

# 1. 删除调试日志
if [ -f "debug_font.log" ]; then
    rm debug_font.log
    echo "✓ 删除 debug_font.log"
fi

# 2. 删除调试脚本
if [ -f "scripts/debug_data.py" ]; then
    rm scripts/debug_data.py
    echo "✓ 删除 scripts/debug_data.py"
fi

# 3. 删除调试输出目录
if [ -d "data/debug_edge_detection" ]; then
    rm -rf data/debug_edge_detection
    echo "✓ 删除 data/debug_edge_detection/"
fi

# 4. 删除所有 .DS_Store 文件
find . -name ".DS_Store" -type f -delete
echo "✓ 删除所有 .DS_Store 文件"

# 5. 删除 Python 缓存
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null
find . -type f -name "*.pyc" -delete 2>/dev/null
find . -type f -name "*.pyo" -delete 2>/dev/null
echo "✓ 删除 Python 缓存文件"

# 6. 可选：删除训练中间数据（已生成模型，可以删除）
read -p "是否删除训练中间数据 data/font_train/ (364个裁剪图片)? [y/N] " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    if [ -d "data/font_train" ]; then
        rm -rf data/font_train
        echo "✓ 删除 data/font_train/"
    fi
fi

echo ""
echo "清理完成！"
echo ""
echo "保留的重要文件："
echo "  - models/custom_font_classifier/     (字体分类模型)"
echo "  - models/point_size_model/           (字号回归模型)"
echo "  - data/aiphoto/                      (原始训练图片)"
echo "  - data/annotations/                  (标注文件)"
