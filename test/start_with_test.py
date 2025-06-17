#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
启动脚本 - 在启动Docker服务前测试挂载
"""

import os
import sys
import subprocess
import time

def run_command(command, description):
    """运行命令并显示结果"""
    print(f"\n=== {description} ===")
    print(f"执行命令: {command}")
    
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        print(f"返回码: {result.returncode}")
        if result.stdout:
            print("输出:")
            print(result.stdout)
        if result.stderr:
            print("错误:")
            print(result.stderr)
        return result.returncode == 0
    except Exception as e:
        print(f"执行命令时出错: {e}")
        return False

def test_docker_mount():
    """测试Docker挂载"""
    print("开始测试Docker挂载...")
    
    # 检查Docker是否运行
    if not run_command("docker info", "检查Docker状态"):
        print("Docker未运行或无法访问！")
        return False
    
    # 构建镜像
    if not run_command("docker build -t yolo-backend .", "构建Docker镜像"):
        print("构建镜像失败！")
        return False
    
    # 测试挂载
    mount_test_cmd = 'docker run --rm -v "F:/_Work/data_/haoyi/dataset:/data/dataset" yolo-backend python test_docker_mount.py'
    if not run_command(mount_test_cmd, "测试数据目录挂载"):
        print("挂载测试失败！")
        print("\n请检查:")
        print("1. Docker Desktop是否启用了F盘共享")
        print("2. 数据目录路径是否正确")
        print("3. 数据目录是否存在")
        return False
    
    print("挂载测试成功！")
    return True

def start_services():
    """启动Docker服务"""
    print("\n开始启动Docker服务...")
    
    if not run_command("docker compose up -d", "启动Docker Compose服务"):
        print("启动服务失败！")
        return False
    
    print("服务启动成功！")
    print("等待服务完全启动...")
    time.sleep(5)
    
    # 检查服务状态
    if not run_command("docker compose ps", "检查服务状态"):
        print("无法检查服务状态！")
        return False
    
    return True

def main():
    """主函数"""
    print("=== YOLO Backend 启动脚本 ===")
    print("此脚本将测试Docker挂载并启动服务")
    
    # 检查必要文件
    required_files = ["docker-compose.yml", "Dockerfile", "test_docker_mount.py"]
    for file in required_files:
        if not os.path.exists(file):
            print(f"错误: 缺少必要文件 {file}")
            return 1
    
    # 测试挂载
    if not test_docker_mount():
        print("\n挂载测试失败，请检查配置后重试")
        return 1
    
    # 询问是否启动服务
    response = input("\n挂载测试成功！是否启动Docker服务？(y/n): ").lower().strip()
    if response not in ['y', 'yes', '是']:
        print("取消启动服务")
        return 0
    
    # 启动服务
    if not start_services():
        print("\n启动服务失败！")
        return 1
    
    print("\n=== 启动完成 ===")
    print("服务已成功启动！")
    print("访问地址: http://localhost:9090")
    print("使用 Ctrl+C 停止服务")
    
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