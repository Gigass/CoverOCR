#!/usr/bin/env python3
"""
将标注工具导出的 JSON 拆分为单个文件
用法: python split_annotations.py annotations.json
"""

import json
import sys
from pathlib import Path

def split_annotations(input_file):
    # 读取导出的 JSON
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 创建输出目录
    output_dir = Path('data/annotations')
    output_dir.mkdir(parents=True, exist_ok=True)
    
    # 拆分每张图片的标注
    for img_data in data['images']:
        # 提取文件名（不含路径）
        image_name = Path(img_data['image_path']).stem
        output_file = output_dir / f'{image_name}.json'
        
        # 写入单个文件
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(img_data, f, ensure_ascii=False, indent=2)
        
        print(f'✅ {output_file}')
    
    print(f'\n✅ 完成！共拆分 {len(data["images"])} 个文件到 {output_dir}')

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print('用法: python split_annotations.py <annotations.json>')
        sys.exit(1)
    
    split_annotations(sys.argv[1])
