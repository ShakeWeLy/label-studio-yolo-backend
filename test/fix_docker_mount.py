#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Docker挂载修复脚本
自动检测和修复常见的Docker挂载问题
"""

import os
import sys
import subprocess
import json

def run_command(command, description=""):
    """运行命令并返回结果"""
    if description:
        print(f"执行: {description}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        return result.returncode == 0, result.stdout, result.stderr
    except Exception as e:
        return False, "", str(e)

def check_docker_running():
    """检查Docker是否运行"""
    print("=== 检查Docker状态 ===")
    success, stdout, stderr = run_command("docker info")
    if success:
        print("✓ Docker正在运行")
        return True
    else:
        print("✗ Docker未运行或无法访问")
        print("请启动Docker Desktop")
        return False

def check_docker_desktop_settings():
    """检查Docker Desktop设置"""
    print("\n=== 检查Docker Desktop设置 ===")
    print("请手动检查以下设置:")
    print("1. 打开Docker Desktop")
    print("2. 进入 Settings > Resources > File Sharing")
    print("3. 确保F盘已启用共享")
    print("4. 点击 'Apply & Restart'")
    
    response = input("完成设置后按回车继续...")
    return True

def check_data_directory():
    """检查数据目录"""
    print("\n=== 检查数据目录 ===")
    data_path = r"F:/_Work/data_/haoyi/dataset"
    
    if not os.path.exists(data_path):
        print(f"✗ 数据目录不存在: {data_path}")
        print("请创建数据目录并放入训练数据")
        return False
    
    print(f"✓ 数据目录存在: {data_path}")
    
    # 检查目录结构
    train_path = os.path.join(data_path, "train")
    images_path = os.path.join(train_path, "images")
    labels_path = os.path.join(train_path, "labels")
    
    if not os.path.exists(train_path):
        print(f"✗ 训练目录不存在: {train_path}")
        os.makedirs(train_path, exist_ok=True)
        print(f"✓ 已创建训练目录: {train_path}")
    
    if not os.path.exists(images_path):
        print(f"✗ 图像目录不存在: {images_path}")
        os.makedirs(images_path, exist_ok=True)
        print(f"✓ 已创建图像目录: {images_path}")
    
    if not os.path.exists(labels_path):
        print(f"✗ 标签目录不存在: {labels_path}")
        os.makedirs(labels_path, exist_ok=True)
        print(f"✓ 已创建标签目录: {labels_path}")
    
    # 检查文件数量
    if os.path.exists(images_path):
        images = [f for f in os.listdir(images_path) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"))]
        print(f"图像文件数量: {len(images)}")
    
    if os.path.exists(labels_path):
        labels = [f for f in os.listdir(labels_path) if f.endswith('.txt')]
        print(f"标签文件数量: {len(labels)}")
    
    return True

def fix_docker_compose():
    """修复docker-compose.yml配置"""
    print("\n=== 修复docker-compose.yml配置 ===")
    
    compose_file = "docker-compose.yml"
    if not os.path.exists(compose_file):
        print(f"✗ {compose_file} 不存在")
        return False
    
    # 读取当前配置
    with open(compose_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # 检查是否包含正确的挂载配置
    if 'F:/_Work/data_/haoyi/dataset:/data/dataset' in content:
        print("✓ docker-compose.yml 挂载配置正确")
        return True
    
    # 修复配置
    print("修复docker-compose.yml配置...")
    
    # 替换DATASET_DIR环境变量
    content = content.replace(
        'DATASET_DIR=F:/_Work/data_/haoyi/dataset',
        'DATASET_DIR=/data/dataset'
    )
    
    # 添加挂载配置
    if 'volumes:' in content and 'F:/_Work/data_/haoyi/dataset:/data/dataset' not in content:
        # 在volumes部分添加挂载
        content = content.replace(
            'volumes:\n      - "./data/server:/data"',
            'volumes:\n      - "./data/server:/data"\n      # 添加数据目录挂载，将Windows主机的数据目录挂载到容器内\n      - "F:/_Work/data_/haoyi/dataset:/data/dataset"'
        )
    
    # 保存修复后的配置
    with open(compose_file, 'w', encoding='utf-8') as f:
        f.write(content)
    
    print("✓ docker-compose.yml 配置已修复")
    return True

def test_mount():
    """测试挂载"""
    print("\n=== 测试Docker挂载 ===")
    
    # 构建镜像
    print("构建Docker镜像...")
    success, stdout, stderr = run_command("docker build -t yolo-backend .")
    if not success:
        print("✗ 构建镜像失败")
        print(stderr)
        return False
    
    print("✓ 镜像构建成功")
    
    # 测试挂载
    print("测试数据目录挂载...")
    test_cmd = 'docker run --rm -v "F:/_Work/data_/haoyi/dataset:/data/dataset" yolo-backend python test_docker_mount.py'
    success, stdout, stderr = run_command(test_cmd)
    
    if success:
        print("✓ 挂载测试成功")
        print(stdout)
        return True
    else:
        print("✗ 挂载测试失败")
        print(stderr)
        return False

def main():
    """主函数"""
    print("=== Docker挂载修复工具 ===")
    print("此工具将帮助您诊断和修复Docker挂载问题")
    
    # 检查Docker状态
    if not check_docker_running():
        return 1
    
    # 检查Docker Desktop设置
    check_docker_desktop_settings()
    
    # 检查数据目录
    if not check_data_directory():
        return 1
    
    # 修复docker-compose.yml
    if not fix_docker_compose():
        return 1
    
    # 测试挂载
    if not test_mount():
        print("\n挂载测试失败，请检查:")
        print("1. Docker Desktop共享驱动器设置")
        print("2. 数据目录路径和权限")
        print("3. 数据目录结构")
        return 1
    
    print("\n=== 修复完成 ===")
    print("✓ 所有问题已修复")
    print("现在可以正常启动服务了:")
    print("docker compose up")
    
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