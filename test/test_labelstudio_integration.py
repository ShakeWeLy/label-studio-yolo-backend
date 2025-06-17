#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio集成测试脚本
测试从Label Studio获取数据和模型保存功能
"""

import os
import sys
import requests
import zipfile
import tempfile
import shutil
from datetime import datetime

def test_labelstudio_connection():
    """测试Label Studio连接"""
    print("=== 测试Label Studio连接 ===")
    
    hostname = os.getenv("LABEL_STUDIO_URL")
    api_key = os.getenv("LABEL_STUDIO_API_KEY")
    
    print(f"LABEL_STUDIO_URL: {hostname}")
    print(f"API_KEY: {api_key[:10]}..." if api_key else "API_KEY: None")
    
    if not hostname or not api_key:
        print("错误: 缺少必要的环境变量")
        return False
    
    # 测试连接
    try:
        response = requests.get(f"{hostname}/api/projects/", headers={'Authorization': f'Token {api_key}'})
        print(f"连接测试状态码: {response.status_code}")
        
        if response.status_code == 200:
            projects = response.json()
            print(f"找到 {len(projects)} 个项目")
            for project in projects[:3]:  # 显示前3个项目
                print(f"  - {project.get('title', 'Unknown')} (ID: {project.get('id', 'Unknown')})")
            return True
        else:
            print(f"连接失败: {response.text}")
            return False
    except Exception as e:
        print(f"连接错误: {e}")
        return False

def test_data_export(project_id):
    """测试数据导出"""
    print(f"\n=== 测试数据导出 (项目ID: {project_id}) ===")
    
    hostname = os.getenv("LABEL_STUDIO_URL")
    api_key = os.getenv("LABEL_STUDIO_API_KEY")
    
    download_url = f'{hostname.rstrip("/")}/api/projects/{project_id}/export?export_type=YOLO&download_all_tasks=true'
    print(f"导出URL: {download_url}")
    
    try:
        response = requests.get(download_url, headers={'Authorization': f'Token {api_key}'})
        print(f"导出响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"导出成功，数据大小: {len(response.content)} 字节")
            
            # 创建临时目录测试解压
            with tempfile.TemporaryDirectory() as temp_dir:
                zip_path = os.path.join(temp_dir, "test_export.zip")
                
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_path) as zf:
                    print("ZIP文件内容:")
                    for item in zf.namelist():
                        print(f"  - {item}")
                
                print("数据导出测试成功")
                return True
        else:
            print(f"导出失败: {response.text}")
            return False
    except Exception as e:
        print(f"导出错误: {e}")
        return False

def test_model_directory():
    """测试模型目录"""
    print("\n=== 测试模型目录 ===")
    
    model_dir = os.getenv("MODEL_DIR", "./models")
    model_filename = os.getenv("MODEL_FILENAME", "best.pt")
    
    print(f"MODEL_DIR: {model_dir}")
    print(f"MODEL_FILENAME: {model_filename}")
    
    # 检查模型目录
    if not os.path.exists(model_dir):
        print(f"创建模型目录: {model_dir}")
        os.makedirs(model_dir, exist_ok=True)
    
    model_path = os.path.join(model_dir, model_filename)
    print(f"模型路径: {model_path}")
    print(f"模型文件存在: {os.path.exists(model_path)}")
    
    # 列出模型目录内容
    if os.path.exists(model_dir):
        files = os.listdir(model_dir)
        print(f"模型目录内容 ({len(files)} 个文件):")
        for file in files:
            file_path = os.path.join(model_dir, file)
            size = os.path.getsize(file_path) if os.path.isfile(file_path) else 0
            print(f"  - {file} ({size} 字节)")
    
    return True

def test_dataset_directory():
    """测试数据集目录"""
    print("\n=== 测试数据集目录 ===")
    
    dataset_dir = os.getenv("DATASET_DIR", "/data/dataset")
    print(f"DATASET_DIR: {dataset_dir}")
    
    # 检查数据集目录
    if not os.path.exists(dataset_dir):
        print(f"创建数据集目录: {dataset_dir}")
        os.makedirs(dataset_dir, exist_ok=True)
    
    print(f"数据集目录存在: {os.path.exists(dataset_dir)}")
    
    # 列出数据集目录内容
    if os.path.exists(dataset_dir):
        items = os.listdir(dataset_dir)
        print(f"数据集目录内容 ({len(items)} 个项目):")
        for item in items:
            item_path = os.path.join(dataset_dir, item)
            if os.path.isdir(item_path):
                print(f"  目录: {item}")
            else:
                print(f"  文件: {item}")
    
    return True

def main():
    """主函数"""
    print("=== Label Studio集成测试 ===")
    
    # 测试Label Studio连接
    if not test_labelstudio_connection():
        print("Label Studio连接测试失败")
        return 1
    
    # 测试模型目录
    if not test_model_directory():
        print("模型目录测试失败")
        return 1
    
    # 测试数据集目录
    if not test_dataset_directory():
        print("数据集目录测试失败")
        return 1
    
    # 测试数据导出（如果有项目ID）
    project_id = input("\n请输入要测试的项目ID (直接回车跳过): ").strip()
    if project_id:
        if not test_data_export(project_id):
            print("数据导出测试失败")
            return 1
    
    print("\n=== 所有测试完成 ===")
    print("✓ Label Studio集成测试成功")
    return 0

if __name__ == "__main__":
    try:
        exit_code = main()
        sys.exit(exit_code)
    except KeyboardInterrupt:
        print("\n用户取消操作")
        sys.exit(0)
    except Exception as e:
        print(f"发生错误: {e}")
        sys.exit(1) 