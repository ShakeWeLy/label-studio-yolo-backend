#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Label Studio图像下载测试脚本
测试从Label Studio获取任务列表和下载图像文件
"""

import os
import sys
import requests
import urllib.parse
import tempfile

def test_get_tasks(project_id):
    """测试获取任务列表"""
    print(f"=== 测试获取任务列表 (项目ID: {project_id}) ===")
    
    hostname = os.getenv("LABEL_STUDIO_URL")
    api_key = os.getenv("LABEL_STUDIO_API_KEY")
    
    if not hostname or not api_key:
        print("错误: 缺少必要的环境变量")
        return False, []
    
    tasks_url = f'{hostname.rstrip("/")}/api/projects/{project_id}/tasks/'
    print(f"任务列表URL: {tasks_url}")
    
    try:
        response = requests.get(tasks_url, headers={'Authorization': f'Token {api_key}'})
        print(f"响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            tasks = response.json()
            print(f"找到 {len(tasks)} 个任务")
            
            # 显示前3个任务的详细信息
            for i, task in enumerate(tasks[:3]):
                task_id = task.get('id')
                task_data = task.get('data', {})
                image_url = task_data.get('image')
                print(f"  任务 {i+1}: ID={task_id}, 图像URL={image_url}")
            
            return True, tasks
        else:
            print(f"获取任务列表失败: {response.text}")
            return False, []
    except Exception as e:
        print(f"获取任务列表错误: {e}")
        return False, []

def test_download_image(image_url, filename):
    """测试下载单个图像"""
    print(f"测试下载图像: {filename}")
    
    hostname = os.getenv("LABEL_STUDIO_URL")
    api_key = os.getenv("LABEL_STUDIO_API_KEY")
    
    # 构建完整的图像URL
    if image_url.startswith('http'):
        full_image_url = image_url
    else:
        full_image_url = f"{hostname.rstrip('/')}{image_url}"
    
    print(f"完整图像URL: {full_image_url}")
    
    try:
        response = requests.get(full_image_url, headers={'Authorization': f'Token {api_key}'})
        print(f"下载响应状态码: {response.status_code}")
        
        if response.status_code == 200:
            print(f"✓ 成功下载: {filename} ({len(response.content)} 字节)")
            return True
        else:
            print(f"✗ 下载失败: {filename} - {response.text}")
            return False
    except Exception as e:
        print(f"✗ 下载错误: {filename} - {e}")
        return False

def test_project_export(project_id):
    """测试项目导出"""
    print(f"\n=== 测试项目导出 (项目ID: {project_id}) ===")
    
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
                import zipfile
                zip_path = os.path.join(temp_dir, "test_export.zip")
                
                with open(zip_path, 'wb') as f:
                    f.write(response.content)
                
                with zipfile.ZipFile(zip_path) as zf:
                    print("ZIP文件内容:")
                    for item in zf.namelist():
                        print(f"  - {item}")
                
                print("项目导出测试成功")
                return True
        else:
            print(f"导出失败: {response.text}")
            return False
    except Exception as e:
        print(f"导出错误: {e}")
        return False

def main():
    """主函数"""
    print("=== Label Studio图像下载测试 ===")
    
    # 检查环境变量
    hostname = os.getenv("LABEL_STUDIO_URL")
    api_key = os.getenv("LABEL_STUDIO_API_KEY")
    
    print(f"LABEL_STUDIO_URL: {hostname}")
    print(f"API_KEY: {api_key[:10]}..." if api_key else "API_KEY: None")
    
    if not hostname or not api_key:
        print("错误: 缺少必要的环境变量")
        return 1
    
    # 获取项目ID
    project_id = input("请输入要测试的项目ID: ").strip()
    if not project_id:
        print("未提供项目ID")
        return 1
    
    # 测试项目导出
    if not test_project_export(project_id):
        print("项目导出测试失败")
        return 1
    
    # 测试获取任务列表
    success, tasks = test_get_tasks(project_id)
    if not success:
        print("获取任务列表失败")
        return 1
    
    if len(tasks) == 0:
        print("项目中没有任务")
        return 1
    
    # 测试下载前3个图像
    print(f"\n=== 测试下载图像文件 ===")
    download_success = 0
    
    for i, task in enumerate(tasks[:3]):
        task_id = task.get('id')
        task_data = task.get('data', {})
        image_url = task_data.get('image')
        
        if not image_url:
            print(f"任务 {task_id} 没有图像URL")
            continue
        
        # 从URL中提取文件名
        parsed_url = urllib.parse.urlparse(image_url)
        image_filename = os.path.basename(parsed_url.path)
        
        if test_download_image(image_url, image_filename):
            download_success += 1
    
    print(f"\n=== 测试结果 ===")
    print(f"总任务数: {len(tasks)}")
    print(f"测试下载数: {min(3, len(tasks))}")
    print(f"成功下载数: {download_success}")
    
    if download_success > 0:
        print("✓ 图像下载测试成功")
        return 0
    else:
        print("✗ 图像下载测试失败")
        return 1

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