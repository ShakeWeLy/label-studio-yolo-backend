# Label Studio YOLO 训练指南

## 环境变量配置

在运行训练之前，请设置以下环境变量：

```bash
# Label Studio 配置
export LABEL_STUDIO_URL=http://localhost:8080
export LABEL_STUDIO_API_KEY=your_api_key_here

# 任务类型 (detection 或 segmentation)
export TASK_TYPE=detection

# 模型配置
export MODEL_DIR=/path/to/models
export MODEL_FILENAME=best.pt
export MODEL_PATH=yolov11n.pt

# 数据集配置
export DATASET_DIR=/data/VideoInference/datasets
export MODEL_SAVE_DIR=/data/VideoInference/models

# 训练参数
export TRAIN_EPOCHS=5
export TRAIN_IMGSZ=640
export TRAIN_BATCH_SIZE=16
```

## 使用方法

1. **启动 Label Studio ML 后端**：
   ```bash
   label-studio-ml start model.py
   ```

2. **在 Label Studio 中连接模型**：
   - 进入项目设置
   - 在 "Machine Learning" 标签页中添加模型
   - 输入后端 URL（通常是 `http://localhost:9090`）

3. **开始训练**：
   - 在 Label Studio 中标注数据
   - 点击 "Start Training" 按钮
   - 训练过程会自动开始

## 训练流程

1. **数据导出**：从 Label Studio 导出 YOLO 格式的标注数据
2. **数据分割**：自动分割为训练集(70%)、验证集(20%)、测试集(10%)
3. **模型训练**：使用 ultralytics YOLO 进行训练
4. **模型保存**：训练完成后保存最佳模型

## 输出文件

- 训练数据：`{DATASET_DIR}/project_{project_id}_{timestamp}/`
- 训练日志：`{DATASET_DIR}/runs/project_{project_id}_{project_title}/`
- 最终模型：`{MODEL_SAVE_DIR}/trained_model_{project_id}.pt`

## 注意事项

1. 确保 Label Studio 中有足够的标注数据
2. 检查所有环境变量是否正确设置
3. 确保有足够的磁盘空间存储训练数据
4. 训练时间取决于数据量和硬件配置 