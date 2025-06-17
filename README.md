## 🚀 Quick Start

1. **配置数据目录挂载:**

   在 `docker-compose.yml` 中确认数据目录挂载配置：

   ```yaml
   volumes:
     - "./data/server:/data"
     # 将Windows主机的数据目录挂载到容器内
     - "F:/_Work/data_/haoyi/dataset:/data/dataset"
     - "./models:/app/models"  # 挂载模型目录
   ```

2. **配置数据目录挂载 (重要！):**

   在 `docker-compose.yml` 中配置数据目录挂载：

   ```yaml
   volumes:
     - "./data/server:/data"
     # 将Windows主机的数据目录挂载到容器内
     - "F:/_Work/data_/haoyi/dataset:/data/dataset"
     - "./models:/app/models"  # 挂载模型目录
   ```

   **注意事项:**

   - 确保Windows主机上的数据目录路径正确
   - 在Docker Desktop中启用共享驱动器 (Settings > Resources > File Sharing)
   - 数据目录结构应该是: `dataset/train/images/` 和 `dataset/train/labels/`

3. **Edit `.env` with your settings:**

   ```yaml
   BASIC_AUTH_USER=  # Optional
   BASIC_AUTH_PASS=  # Optional
   LOG_LEVEL=DEBUG
   
   MODEL_FILENAME=model.pt
   MODEL_DIR=/app/models
   
   PORT=8080
   
   LABEL_STUDIO_URL=http://host.docker.internal:8080
   LABEL_STUDIO_API_KEY= # API key from LS
   TASK_TYPE=segmentation # segmentation or detection
   
   # 训练参数
   TRAIN_EPOCHS=10
   TRAIN_IMGSZ=640
   TRAIN_BATCH_SIZE=16
   ```


### 类别名称获取
系统支持多种方式获取类别名称，按优先级排序：
1. **classes.txt文件**（最高优先级）
   ```
   product
   product_red
   ```
2. **notes.json文件**
   
   ```json
   {
     "categories": [
       {"id": 0, "name": "product"},
       {"id": 1, "name": "product_red"}
     ]
   }
   ```
   
### **目录结构:**
   ```
   F:/_Work/data_/haoyi/dataset/
   ├── train/
   │   ├── images/
   │   │   ├── image1.jpg
   │   │   ├── image2.jpg
   │   │   └── ...
   │   └── labels/
   │       ├── image1.txt
   │       ├── image2.txt
   │       └── ...
   └── data.yaml (可选，会自动生成)
   ```

