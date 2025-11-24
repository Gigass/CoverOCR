#!/usr/bin/env python3
"""
CoverOCR 数据集完整性检查脚本
检查图片和标注文件是否匹配，数据是否合法
"""

import json
import sys
from pathlib import Path
from PIL import Image

def check_dataset(dataset_path='data/annotations/dataset.json', images_dir='data/images'):
    print("🔍 开始检查数据集...")
    print("=" * 60)
    
    # 检查文件是否存在
    dataset_file = Path(dataset_path)
    if not dataset_file.exists():
        print(f"❌ 错误：找不到标注文件 {dataset_path}")
        return False
    
    images_path = Path(images_dir)
    if not images_path.exists():
        print(f"❌ 错误：找不到图片目录 {images_dir}")
        return False
    
    # 加载标注文件
    with open(dataset_file, 'r', encoding='utf-8') as f:
        dataset = json.load(f)
    
    print(f"✅ 标注文件版本: {dataset.get('version', 'unknown')}")
    print(f"✅ 导出日期: {dataset.get('export_date', 'unknown')}")
    print(f"✅ 声明图片数量: {dataset.get('total_images', 0)}")
    print()
    
    # 统计信息
    total_images = len(dataset['images'])
    total_regions = 0
    annotated_regions = 0
    missing_images = []
    invalid_bboxes = []
    invalid_point_sizes = []
    
    # 检查每张图片
    for idx, img_data in enumerate(dataset['images'], 1):
        image_path = Path(images_dir) / Path(img_data['image_path']).name
        
        # 检查图片是否存在
        if not image_path.exists():
            missing_images.append(img_data['image_path'])
            print(f"❌ [{idx}/{total_images}] 图片不存在: {image_path}")
            continue
        
        # 加载图片验证尺寸
        try:
            img = Image.open(image_path)
            actual_width, actual_height = img.size
            
            if actual_width != img_data['image_width'] or actual_height != img_data['image_height']:
                print(f"⚠️  [{idx}/{total_images}] 图片尺寸不匹配: {image_path}")
                print(f"    标注: {img_data['image_width']}x{img_data['image_height']}")
                print(f"    实际: {actual_width}x{actual_height}")
        except Exception as e:
            print(f"❌ [{idx}/{total_images}] 无法打开图片: {image_path} ({e})")
            continue
        
        # 检查标注
        for ann in img_data['annotations']:
            total_regions += 1
            
            # 检查是否已标注
            if ann['font_family'] and ann['point_size']:
                annotated_regions += 1
            
            # 检查边界框
            bbox = ann['bbox']
            if len(bbox) != 4:
                invalid_bboxes.append((image_path.name, ann['id']))
            elif not (0 <= bbox[0] < bbox[2] <= actual_width and 
                     0 <= bbox[1] < bbox[3] <= actual_height):
                invalid_bboxes.append((image_path.name, ann['id']))
            
            # 检查磅值
            if ann['point_size'] and not (5 <= ann['point_size'] <= 100):
                invalid_point_sizes.append((image_path.name, ann['id'], ann['point_size']))
        
        print(f"✅ [{idx}/{total_images}] {image_path.name}: {len(img_data['annotations'])} 个区域")
    
    # 输出统计
    print()
    print("=" * 60)
    print("📊 数据集统计")
    print("=" * 60)
    print(f"总图片数: {total_images}")
    print(f"总文字区域数: {total_regions}")
    print(f"已标注区域数: {annotated_regions} ({annotated_regions/total_regions*100:.1f}%)")
    print(f"未标注区域数: {total_regions - annotated_regions}")
    print()
    
    # 输出问题
    has_errors = False
    
    if missing_images:
        has_errors = True
        print("❌ 缺失的图片:")
        for img in missing_images:
            print(f"   - {img}")
        print()
    
    if invalid_bboxes:
        has_errors = True
        print("❌ 无效的边界框:")
        for img_name, region_id in invalid_bboxes[:10]:  # 只显示前10个
            print(f"   - {img_name}, 区域 #{region_id}")
        if len(invalid_bboxes) > 10:
            print(f"   ... 还有 {len(invalid_bboxes) - 10} 个")
        print()
    
    if invalid_point_sizes:
        has_errors = True
        print("❌ 异常的磅值:")
        for img_name, region_id, pt in invalid_point_sizes[:10]:
            print(f"   - {img_name}, 区域 #{region_id}: {pt}pt")
        if len(invalid_point_sizes) > 10:
            print(f"   ... 还有 {len(invalid_point_sizes) - 10} 个")
        print()
    
    # 总结
    print("=" * 60)
    if has_errors:
        print("⚠️  发现问题，请修正后再训练模型")
        return False
    else:
        print("✅ 数据集检查通过！可以开始训练模型")
        return True

if __name__ == '__main__':
    dataset_path = sys.argv[1] if len(sys.argv) > 1 else 'data/annotations/dataset.json'
    images_dir = sys.argv[2] if len(sys.argv) > 2 else 'data/images'
    
    success = check_dataset(dataset_path, images_dir)
    sys.exit(0 if success else 1)
