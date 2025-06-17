#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
类别名称获取测试脚本
测试从classes.txt、notes.json和标签文件中获取类别名称的功能
"""

import os
import json
import tempfile
import shutil

def create_test_files():
    """创建测试文件"""
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建目录结构
        train_dir = os.path.join(temp_dir, "train")
        labels_dir = os.path.join(train_dir, "labels")
        os.makedirs(labels_dir, exist_ok=True)
        
        # 1. 创建classes.txt文件
        classes_txt_path = os.path.join(temp_dir, "classes.txt")
        with open(classes_txt_path, 'w', encoding='utf-8') as f:
            f.write("product\n")
            f.write("product_red\n")
        
        # 2. 创建notes.json文件
        notes_json_path = os.path.join(temp_dir, "notes.json")
        notes_data = {
            "categories": [
                {"id": 0, "name": "product"},
                {"id": 1, "name": "product_red"}
            ],
            "info": {
                "year": 2025,
                "version": "1.0",
                "contributor": "Label Studio"
            }
        }
        with open(notes_json_path, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, indent=2, ensure_ascii=False)
        
        # 3. 创建示例标签文件
        label_file_path = os.path.join(labels_dir, "test.txt")
        with open(label_file_path, 'w') as f:
            f.write("0 0.5 0.5 0.2 0.3\n")  # class_id=0
            f.write("1 0.7 0.8 0.1 0.2\n")  # class_id=1
        
        return temp_dir, labels_dir

def test_class_names_extraction():
    """测试类别名称提取功能"""
    print("=== 测试类别名称提取功能 ===")
    
    # 创建测试文件
    temp_dir, labels_dir = create_test_files()
    
    # 模拟_get_class_names_from_labels方法
    def get_class_names_from_labels(labels_dir):
        """从classes.txt、notes.json或标签文件中获取类别名称"""
        train_path = os.path.dirname(os.path.dirname(labels_dir))  # 获取训练根目录
        
        # 1. 优先从classes.txt文件获取类别名称
        classes_txt_path = os.path.join(train_path, "classes.txt")
        if os.path.exists(classes_txt_path):
            try:
                with open(classes_txt_path, 'r', encoding='utf-8') as f:
                    class_names = [line.strip() for line in f.readlines() if line.strip()]
                print(f"✓ 从classes.txt获取到类别: {class_names}")
                return class_names
            except Exception as e:
                print(f"✗ 读取classes.txt失败: {e}")
        
        # 2. 从notes.json文件获取类别名称
        notes_json_path = os.path.join(train_path, "notes.json")
        if os.path.exists(notes_json_path):
            try:
                with open(notes_json_path, 'r', encoding='utf-8') as f:
                    notes_data = json.load(f)
                
                # 从categories中提取类别名称
                if 'categories' in notes_data:
                    categories = notes_data['categories']
                    class_names = [cat['name'] for cat in categories if 'name' in cat]
                    if class_names:
                        print(f"✓ 从notes.json获取到类别: {class_names}")
                        return class_names
            except Exception as e:
                print(f"✗ 读取notes.json失败: {e}")
        
        # 3. 从标签文件中推断类别名称（备用方案）
        class_names = set()
        
        if not os.path.exists(labels_dir):
            return ["class_0"]  # 默认类别名
            
        for label_file in os.listdir(labels_dir):
            if label_file.endswith('.txt'):
                file_path = os.path.join(labels_dir, label_file)
                try:
                    with open(file_path, 'r') as f:
                        for line in f:
                            parts = line.strip().split()
                            if len(parts) >= 1:
                                class_id = int(parts[0])
                                class_names.add(f"class_{class_id}")
                except:
                    continue
        
        if not class_names:
            class_names = ["class_0"]
        
        class_names = sorted(list(class_names))
        print(f"✓ 从标签文件推断出类别: {class_names}")
        return class_names
    
    # 测试1: 有classes.txt文件
    print("\n--- 测试1: 有classes.txt文件 ---")
    class_names = get_class_names_from_labels(labels_dir)
    expected = ["product", "product_red"]
    if class_names == expected:
        print(f"✓ 测试通过: {class_names}")
    else:
        print(f"✗ 测试失败: 期望 {expected}, 实际 {class_names}")
    
    # 测试2: 删除classes.txt，测试notes.json
    print("\n--- 测试2: 删除classes.txt，测试notes.json ---")
    classes_txt_path = os.path.join(temp_dir, "classes.txt")
    if os.path.exists(classes_txt_path):
        os.remove(classes_txt_path)
    
    class_names = get_class_names_from_labels(labels_dir)
    expected = ["product", "product_red"]
    if class_names == expected:
        print(f"✓ 测试通过: {class_names}")
    else:
        print(f"✗ 测试失败: 期望 {expected}, 实际 {class_names}")
    
    # 测试3: 删除notes.json，测试标签文件推断
    print("\n--- 测试3: 删除notes.json，测试标签文件推断 ---")
    notes_json_path = os.path.join(temp_dir, "notes.json")
    if os.path.exists(notes_json_path):
        os.remove(notes_json_path)
    
    class_names = get_class_names_from_labels(labels_dir)
    expected = ["class_0", "class_1"]
    if class_names == expected:
        print(f"✓ 测试通过: {class_names}")
    else:
        print(f"✗ 测试失败: 期望 {expected}, 实际 {class_names}")
    
    # 测试4: 所有文件都不存在
    print("\n--- 测试4: 所有文件都不存在 ---")
    shutil.rmtree(temp_dir)
    class_names = get_class_names_from_labels(labels_dir)
    expected = ["class_0"]
    if class_names == expected:
        print(f"✓ 测试通过: {class_names}")
    else:
        print(f"✗ 测试失败: 期望 {expected}, 实际 {class_names}")

def test_real_data_structure():
    """测试真实数据结构"""
    print("\n=== 测试真实数据结构 ===")
    
    # 模拟Label Studio导出的数据结构
    with tempfile.TemporaryDirectory() as temp_dir:
        # 创建目录结构
        train_dir = os.path.join(temp_dir, "project_6_20250617_075216")
        images_dir = os.path.join(train_dir, "images")
        labels_dir = os.path.join(train_dir, "labels")
        
        os.makedirs(images_dir, exist_ok=True)
        os.makedirs(labels_dir, exist_ok=True)
        
        # 创建classes.txt
        classes_txt_path = os.path.join(train_dir, "classes.txt")
        with open(classes_txt_path, 'w', encoding='utf-8') as f:
            f.write("product\n")
            f.write("product_red\n")
        
        # 创建notes.json
        notes_json_path = os.path.join(train_dir, "notes.json")
        notes_data = {
            "categories": [
                {"id": 0, "name": "product"},
                {"id": 1, "name": "product_red"}
            ],
            "info": {
                "year": 2025,
                "version": "1.0",
                "contributor": "Label Studio"
            }
        }
        with open(notes_json_path, 'w', encoding='utf-8') as f:
            json.dump(notes_data, f, indent=2, ensure_ascii=False)
        
        # 创建示例标签文件
        for i in range(3):
            label_file_path = os.path.join(labels_dir, f"image_{i}.txt")
            with open(label_file_path, 'w') as f:
                f.write(f"{i % 2} 0.5 0.5 0.2 0.3\n")  # 交替使用class 0和1
        
        print(f"创建测试目录: {temp_dir}")
        print(f"目录结构:")
        for root, dirs, files in os.walk(temp_dir):
            level = root.replace(temp_dir, '').count(os.sep)
            indent = ' ' * 2 * level
            print(f"{indent}{os.path.basename(root)}/")
            subindent = ' ' * 2 * (level + 1)
            for file in files:
                print(f"{subindent}{file}")
        
        # 测试类别名称获取
        def get_class_names_from_labels(labels_dir):
            train_path = os.path.dirname(labels_dir)  # 获取训练根目录
            
            # 1. 优先从classes.txt文件获取类别名称
            classes_txt_path = os.path.join(train_path, "classes.txt")
            if os.path.exists(classes_txt_path):
                try:
                    with open(classes_txt_path, 'r', encoding='utf-8') as f:
                        class_names = [line.strip() for line in f.readlines() if line.strip()]
                    print(f"✓ 从classes.txt获取到类别: {class_names}")
                    return class_names
                except Exception as e:
                    print(f"✗ 读取classes.txt失败: {e}")
            
            # 2. 从notes.json文件获取类别名称
            notes_json_path = os.path.join(train_path, "notes.json")
            if os.path.exists(notes_json_path):
                try:
                    with open(notes_json_path, 'r', encoding='utf-8') as f:
                        notes_data = json.load(f)
                    
                    # 从categories中提取类别名称
                    if 'categories' in notes_data:
                        categories = notes_data['categories']
                        class_names = [cat['name'] for cat in categories if 'name' in cat]
                        if class_names:
                            print(f"✓ 从notes.json获取到类别: {class_names}")
                            return class_names
                except Exception as e:
                    print(f"✗ 读取notes.json失败: {e}")
            
            # 3. 从标签文件中推断类别名称（备用方案）
            class_names = set()
            
            if not os.path.exists(labels_dir):
                return ["class_0"]  # 默认类别名
                
            for label_file in os.listdir(labels_dir):
                if label_file.endswith('.txt'):
                    file_path = os.path.join(labels_dir, label_file)
                    try:
                        with open(file_path, 'r') as f:
                            for line in f:
                                parts = line.strip().split()
                                if len(parts) >= 1:
                                    class_id = int(parts[0])
                                    class_names.add(f"class_{class_id}")
                    except:
                        continue
            
            if not class_names:
                class_names = ["class_0"]
            
            class_names = sorted(list(class_names))
            print(f"✓ 从标签文件推断出类别: {class_names}")
            return class_names
        
        class_names = get_class_names_from_labels(labels_dir)
        expected = ["product", "product_red"]
        if class_names == expected:
            print(f"✓ 真实数据结构测试通过: {class_names}")
        else:
            print(f"✗ 真实数据结构测试失败: 期望 {expected}, 实际 {class_names}")

def main():
    """主函数"""
    print("=== 类别名称获取测试 ===")
    
    try:
        # 测试基本功能
        test_class_names_extraction()
        
        # 测试真实数据结构
        test_real_data_structure()
        
        print("\n=== 所有测试完成 ===")
        
    except Exception as e:
        print(f"测试过程中发生错误: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main() 