# Label Studio集成和模型保存修改总结

## 修改目标

将系统从使用本地数据改为从Label Studio获取数据，并且模型保存到本地的MODEL_DIR目录，使用MODEL_FILENAME进行finetune。

## 主要修改内容

### 1. 修改 `model.py` 中的 `gen_train_data` 方法

**修改前**: 使用本地数据目录
**修改后**: 从Label Studio获取数据

```python
# 从Label Studio下载数据
download_url = f'{HOSTNAME.rstrip("/")}/api/projects/{project_id}/export?export_type=YOLO&download_all_tasks=true'
response = requests.get(download_url, headers={'Authorization': f'Token {API_KEY}'})

# 解压并处理数据
with zipfile.ZipFile(zip_path) as f:
    f.extractall(train_path)

# 数据集分割
random.shuffle(images)
train_count = int(total_images * 0.7)
val_count = int(total_images * 0.2)
test_count = total_images - train_count - val_count

# 创建标准YOLO目录结构
for split in ["train", "val", "test"]:
    for sub in ["images", "labels"]:
        p = os.path.join(train_path, split, sub)
        os.makedirs(p, exist_ok=True)
```

### 2. 修改 `model.py` 中的 `fit` 方法

**修改前**: 使用默认模型
**修改后**: 使用本地MODEL_DIR和MODEL_FILENAME进行finetune

```python
# 加载本地模型进行finetune
model_dir = os.getenv("MODEL_DIR", "./models")
model_filename = os.getenv("MODEL_FILENAME", "best.pt")
model_path = os.path.join(model_dir, model_filename)

# 检查模型文件是否存在
if not os.path.exists(model_path):
    print(f"警告: 模型文件不存在 {model_path}，将使用默认模型")
    model = YOLO("yolov8n.pt")
else:
    model = YOLO(model_path)

# 保存训练好的模型到MODEL_DIR
final_model_path = os.path.join(model_dir, model_filename)
shutil.copy(str(best_model_path), final_model_path)

# 重新加载模型
self.model = YOLO(final_model_path)
```

### 3. 修改 `docker-compose.yml`

**添加的环境变量**:
```yaml
environment:
  - DATASET_DIR=/data/dataset  # 训练数据目录
  - MODEL_DIR=./models         # 模型目录
  - MODEL_FILENAME=best.pt     # 模型文件名
```

**添加的挂载**:
```yaml
volumes:
  - "./models:/app/models"  # 挂载模型目录
```

### 4. 添加数据集分割功能

自动将Label Studio导出的数据按以下比例分割：
- 训练集: 70%
- 验证集: 20%
- 测试集: 10%

创建标准的YOLO目录结构：
```
project_123_20241201_143022/
├── train/
│   ├── images/
│   └── labels/
├── val/
│   ├── images/
│   └── labels/
├── test/
│   ├── images/
│   └── labels/
└── data.yaml
```

### 5. 自动生成 `data.yaml` 配置文件

```yaml
# YOLO 数据集配置文件
path: /data/dataset/project_123_20241201_143022
train: train/images
val: val/images
test: test/images

# 类别数量
nc: 2

# 类别名称
names: ['class_0', 'class_1']
```

## 工作流程

1. **触发训练**: Label Studio发送 `START_TRAINING` 事件
2. **获取数据**: 从Label Studio API下载YOLO格式数据
3. **数据分割**: 自动分割为训练/验证/测试集
4. **加载模型**: 从 `MODEL_DIR/MODEL_FILENAME` 加载模型
5. **开始训练**: 使用YOLO进行finetune训练
6. **保存模型**: 训练完成后保存到 `MODEL_DIR/MODEL_FILENAME`
7. **重新加载**: 重新加载训练好的模型用于预测

## 环境变量配置

```bash
# Label Studio配置
LABEL_STUDIO_URL=http://host.docker.internal:8080
LABEL_STUDIO_API_KEY=your_api_key

# 模型配置
MODEL_DIR=./models
MODEL_FILENAME=best.pt

# 训练配置
TRAIN_EPOCHS=10
TRAIN_IMGSZ=640
TRAIN_BATCH_SIZE=16

# 数据目录
DATASET_DIR=/data/dataset
```

## 测试脚本

创建了 `test_labelstudio_integration.py` 测试脚本，用于验证：
- Label Studio连接
- 数据导出功能
- 模型目录配置
- 数据集目录配置

## 优势

1. **自动化**: 完全自动化从Label Studio获取数据
2. **标准化**: 使用标准的YOLO数据集结构
3. **增量训练**: 支持模型finetune
4. **持久化**: 训练好的模型保存到本地
5. **可配置**: 通过环境变量灵活配置

## 注意事项

1. 确保Label Studio项目中有已标注的数据
2. 确保MODEL_DIR目录存在且有写入权限
3. 首次训练时如果没有模型文件，会使用默认的yolov8n.pt
4. 训练完成后会自动重新加载模型用于后续预测 