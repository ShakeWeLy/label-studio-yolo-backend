#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker挂载测试脚本
用于验证Docker容器中的数据目录挂载是否正常工作
"""

import os
import sys

def test_docker_mount():
    """测试Docker挂载功能"""
    print("=== Docker挂载测试 ===")
    
    # 检查环境变量
    dataset_dir = os.getenv("DATASET_DIR", "/data/dataset")
    print(f"DATASET_DIR: {dataset_dir}")
    
    # 检查是否在Docker容器中
    is_docker = os.path.exists('/.dockerenv')
    print(f"运行环境: {'Docker容器' if is_docker else '本地环境'}")
    
    # 检查数据集目录
    print(f"\n=== 数据集目录检查 ===")
    print(f"数据集目录路径: {dataset_dir}")
    print(f"数据集目录存在: {os.path.exists(dataset_dir)}")
    
    if os.path.exists(dataset_dir):
        print(f"数据集目录内容:")
        try:
            items = os.listdir(dataset_dir)
            print(f"  包含 {len(items)} 个项目")
            for item in items:
                item_path = os.path.join(dataset_dir, item)
                if os.path.isdir(item_path):
                    print(f"  目录: {item}")
                    try:
                        subitems = os.listdir(item_path)
                        print(f"    包含 {len(subitems)} 个子项目")
                        if len(subitems) > 0:
                            print(f"    前5个子项目: {subitems[:5]}")
                    except PermissionError:
                        print(f"    - 无法访问目录内容")
                else:
                    print(f"  文件: {item}")
        except Exception as e:
            print(f"  读取目录失败: {e}")
    else:
        print("数据集目录不存在！")
        return False
    
    # 检查训练数据目录
    train_path = os.path.join(dataset_dir, "train")
    print(f"\n=== 训练数据目录检查 ===")
    print(f"训练路径: {train_path}")
    print(f"训练路径存在: {os.path.exists(train_path)}")
    
    if os.path.exists(train_path):
        image_dir = os.path.join(train_path, "images")
        label_dir = os.path.join(train_path, "labels")
        
        print(f"图像目录: {image_dir}")
        print(f"图像目录存在: {os.path.exists(image_dir)}")
        print(f"标签目录: {label_dir}")
        print(f"标签目录存在: {os.path.exists(label_dir)}")
        
        # 检查图像文件
        if os.path.exists(image_dir):
            images = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"))]
            print(f"图像文件数量: {len(images)}")
            if len(images) > 0:
                print(f"前5个图像文件: {images[:5]}")
            else:
                print("警告: 没有找到图像文件！")
        else:
            print("图像目录不存在！")
        
        # 检查标签文件
        if os.path.exists(label_dir):
            labels = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
            print(f"标签文件数量: {len(labels)}")
            if len(labels) > 0:
                print(f"前5个标签文件: {labels[:5]}")
            else:
                print("警告: 没有找到标签文件！")
        else:
            print("标签目录不存在！")
    
    # 搜索整个数据集目录中的图像文件
    print(f"\n=== 全局图像文件搜索 ===")
    image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']
    found_images = []
    
    if os.path.exists(dataset_dir):
        for root, dirs, files in os.walk(dataset_dir):
            for file in files:
                if any(file.lower().endswith(ext) for ext in image_extensions):
                    found_images.append(os.path.join(root, file))
    
    print(f"在整个数据集目录中找到 {len(found_images)} 个图像文件")
    if found_images:
        print("前10个图像文件:")
        for img in found_images[:10]:
            print(f"  - {img}")
    else:
        print("未找到任何图像文件！")
        print("\n可能的问题:")
        print("1. Docker挂载配置不正确")
        print("2. Windows路径格式问题")
        print("3. Docker Desktop共享驱动器设置问题")
        print("4. 数据目录权限问题")
        return False
    
    print(f"\n=== 测试完成 ===")
    print("Docker挂载测试成功！")
    return True

if __name__ == "__main__":
    success = test_docker_mount()
    sys.exit(0 if success else 1) 