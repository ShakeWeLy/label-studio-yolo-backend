# Custom YOLO Backend for Label Studio

This backend provides ML-assisted labeling capabilities to accelerate your annotation workflow, supporting both **object detection** and **instance segmentation** tasks.

## 🏗️ Project Structure

- **Dockerfile**: The Dockerfile for building the backend container.

- **docker-compose.yml**: The docker-compose file for running the backend.

- **_wsgi.py**: WSGI app initializer.

- **start.sh**: bash script to start the whole process.

- **model.py**: The Python code for the ML backend model.

- **requirements.txt**: The list of Python dependencies for the backend.

## 🚀 Quick Start

### 方法一：使用智能启动脚本（推荐）

1. **Clone the repository**:

   ```bash
   git clone https://github.com/seblful/label-studio-yolo-backend.git
   cd label-studio-yolo-backend
   ```

2. **配置数据目录挂载:**

   在 `docker-compose.yml` 中确认数据目录挂载配置：
   
   ```yaml
   volumes:
     - "./data/server:/data"
     # 将Windows主机的数据目录挂载到容器内
     - "F:/_Work/data_/haoyi/dataset:/data/dataset"
     - "./models:/app/models"  # 挂载模型目录
   ```

3. **运行智能启动脚本:**

   ```bash
   python start_with_test.py
   ```
   
   此脚本会：
   - 自动测试Docker挂载是否正常
   - 检查数据目录结构
   - 启动Docker服务
   - 显示服务状态

### 方法二：手动启动

1. **Clone the repository**:

   ```bash
   git clone https://github.com/seblful/label-studio-yolo-backend.git
   cd label-studio-yolo-backend
   ```

2. **Create and prepare your model directory:**
   
    ```bash
    mkdir models
    cp /path/to/your/model.pt models/
    ```

3. **配置数据目录挂载 (重要！):**

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

4. **Edit `.env` with your settings:**
   
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

5. **测试Label Studio集成:**
   
   在启动服务前，可以先测试Label Studio连接：
   
   ```bash
   # 测试Label Studio集成
   python test_labelstudio_integration.py
   
   # 测试图像下载功能
   python test_image_download.py
   ```

6. **Deploy using the following command:**
   
    ```bash
    docker compose up
    ```

7. **Add the model in project settings:**

    From the project settings, select the **Model** page and click [**Connect Model**](https://labelstud.io/guide/ml#Connect-the-model-to-Label-Studio).
    
    Add the URL `http://locallhost:9090` and save the model as an ML backend.

   ![Connect Model](https://github.com/seblful/label-studio-yolo-backend/raw/main/assets/images/connect_model.png)
   ![Connected model](https://github.com/seblful/label-studio-yolo-backend/raw/main/assets/images/connected_model.png)

8. **Label in interactive mode**

    To use this functionality, activate **Auto-Annotation**.

  ![Example annotation](https://github.com/seblful/label-studio-yolo-backend/raw/main/assets/images/annotation.png)


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

### For users with internet restrictions:
  
Configure Docker daemon with proxy:
```json
{
  "registry-mirrors": ["https://registry.docker-cn.com"]
}
```

## 📋 TODO

- Add support for obb and keypoints.

## 💁 Contributing

Contributions to this project are welcome. To contribute, please submit an issue or pull request.
