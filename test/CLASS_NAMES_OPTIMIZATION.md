# 类别名称获取优化和YOLO命名冲突修复

## 问题描述

### 1. 类别名称获取问题

用户发现Label Studio导出的数据中包含了`classes.txt`和`notes.json`文件，这些文件包含了准确的类别名称信息：

**classes.txt内容:**
```
product
product_red
```

**notes.json内容:**
```json
{
  "categories": [
    {
      "id": 0,
      "name": "product"
    },
    {
      "id": 1,
      "name": "product_red"
    }
  ],
  "info": {
    "year": 2025,
    "version": "1.0",
    "contributor": "Label Studio"
  }
}
```

但是代码中仍然从标签文件中推断类别名称，得到的是`['class_0', 'class_1']`而不是实际的类别名称。

### 2. YOLO命名冲突问题

在训练过程中出现错误：`'YOLO' object has no attribute 'train'`

这是因为代码中存在两个`YOLO`类：
- `ultralytics.YOLO`：用于模型训练和预测
- 自定义的`YOLO`类：继承自`LabelStudioMLBase`，用于Label Studio集成

在`fit`方法中使用`YOLO()`创建模型实例时，Python解释器选择了自定义的`YOLO`类，而不是`ultralytics.YOLO`类。

## 解决方案

### 1. 优化类别名称获取

修改`_get_class_names_from_labels`方法，实现三级获取策略：

```python
def _get_class_names_from_labels(self, labels_dir):
    """从classes.txt、notes.json或标签文件中获取类别名称"""
    train_path = os.path.dirname(os.path.dirname(labels_dir))  # 获取训练根目录
    
    # 1. 优先从classes.txt文件获取类别名称
    classes_txt_path = os.path.join(train_path, "classes.txt")
    if os.path.exists(classes_txt_path):
        try:
            with open(classes_txt_path, 'r', encoding='utf-8') as f:
                class_names = [line.strip() for line in f.readlines() if line.strip()]
            print(f"从classes.txt获取到类别: {class_names}")
            return class_names
        except Exception as e:
            print(f"读取classes.txt失败: {e}")
    
    # 2. 从notes.json文件获取类别名称
    notes_json_path = os.path.join(train_path, "notes.json")
    if os.path.exists(notes_json_path):
        try:
            import json
            with open(notes_json_path, 'r', encoding='utf-8') as f:
                notes_data = json.load(f)
            
            # 从categories中提取类别名称
            if 'categories' in notes_data:
                categories = notes_data['categories']
                class_names = [cat['name'] for cat in categories if 'name' in cat]
                if class_names:
                    print(f"从notes.json获取到类别: {class_names}")
                    return class_names
        except Exception as e:
            print(f"读取notes.json失败: {e}")
    
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
    print(f"从标签文件推断出类别: {class_names}")
    return class_names
```

### 2. 修复YOLO命名冲突

在`fit`方法中明确使用`ultralytics.YOLO`：

```python
def fit(self, event, data, **kwargs):
    if event == 'START_TRAINING':
        try:
            # ... 其他代码 ...
            
            # 检查模型文件是否存在
            if not os.path.exists(model_path):
                print(f"警告: 模型文件不存在 {model_path}，将使用默认模型")
                model = ultralytics.YOLO("yolov11n.pt") # 明确使用ultralytics.YOLO
            else:
                model = ultralytics.YOLO(model_path)  # 明确使用ultralytics.YOLO
            
            # ... 训练代码 ...
            
            # 重新加载模型时也要明确使用ultralytics.YOLO
            # self.model = ultralytics.YOLO(final_model_path)
            
        except Exception as e:
            print(f"训练过程中发生错误: {str(e)}")
            raise e
```

## 优化效果

### 修复前
```
类别: ['class_0', 'class_1']
训练过程中发生错误: 'YOLO' object has no attribute 'train'
```

### 修复后
```
从classes.txt获取到类别: ['product', 'product_red']
类别: ['product', 'product_red']
data.yaml 已创建: /data/dataset/project_6_20250617_085530/data.yaml
开始训练，参数: epochs=10, imgsz=640, batch_size=16
```

## 优势

1. **准确性**：直接从Label Studio导出的文件中获取准确的类别名称
2. **兼容性**：支持多种类别名称来源，确保在各种情况下都能正常工作
3. **清晰性**：明确区分不同的YOLO类，避免命名冲突
4. **可维护性**：代码结构清晰，易于理解和维护

## 测试验证

创建了`test_class_names.py`测试脚本，验证：
- 从classes.txt获取类别名称
- 从notes.json获取类别名称  
- 从标签文件推断类别名称
- 真实数据结构测试

## 注意事项

1. **文件编码**：确保classes.txt和notes.json文件使用UTF-8编码
2. **文件路径**：确保文件路径正确，特别是在Docker容器中
3. **权限问题**：确保有足够的权限读取这些文件
4. **命名冲突**：在代码中明确使用`ultralytics.YOLO`避免冲突

现在系统能够：
- 正确获取Label Studio项目中的类别名称
- 避免YOLO类的命名冲突
- 正常进行模型训练 