# Custom YOLO Backend for Label Studio

This backend provides ML-assisted labeling capabilities to accelerate your annotation workflow, supporting both **object detection** and **instance segmentation** tasks.

## 🏗️ Project Structure

- **Dockerfile**: The Dockerfile for building the backend container.

- **docker-compose.yml**: The docker-compose file for running the backend.

- **_wsgi.py**: WSGI app initializer.

- **start.sh**: bash script to start the whole process.

- **model.py**: The Python code for the ML backend model.

- **requirements.txt**: The list of Python dependencies for the backend.

- **test_docker_mount.py**: Docker挂载测试脚本，用于验证数据目录挂载是否正常。

- **start_with_test.py**: 智能启动脚本，自动测试挂载并启动服务。

- **fix_docker_mount.py**: Docker挂载修复脚本，自动检测和修复常见的挂载问题。

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

    PORT=8080

    LABEL_STUDIO_API_KEY= # API key from LS
    TASK_TYPE=segmentation # segmentation or detection
    ```

5. **测试Docker挂载:**
   
   在启动服务前，可以先测试挂载是否正常：
   
   ```bash
   # 构建镜像
   docker build -t yolo-backend .
   
   # 测试挂载
   docker run --rm -v "F:/_Work/data_/haoyi/dataset:/data/dataset" yolo-backend python test_docker_mount.py
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

## 🔧 故障排除

### Docker挂载问题

如果遇到"图像目录为空"的错误，请检查：

1. **Docker Desktop设置:**
   - 打开Docker Desktop
   - 进入 Settings > Resources > File Sharing
   - 确保包含数据目录的驱动器已启用共享

2. **路径格式:**
   - Windows路径使用正斜杠: `F:/_Work/data_/haoyi/dataset`
   - 避免使用反斜杠: `F:\_Work\data_\haoyi\dataset`

3. **目录结构:**
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

4. **权限问题:**
   - 确保Docker有权限访问数据目录
   - 检查目录和文件的读取权限

### 测试挂载

使用提供的测试脚本验证挂载：

```bash
# 在容器中运行测试
docker run --rm -v "F:/_Work/data_/haoyi/dataset:/data/dataset" yolo-backend python test_docker_mount.py
```

### 自动修复挂载问题

如果遇到挂载问题，可以使用自动修复脚本：

```bash
# 运行修复脚本
python fix_docker_mount.py
```

此脚本会：
- 检查Docker状态
- 验证数据目录结构
- 修复docker-compose.yml配置
- 测试挂载功能
- 提供详细的错误诊断

### 常见错误及解决方案

1. **"图像目录为空"错误:**
   - 检查Docker挂载配置
   - 确认数据目录路径正确
   - 验证Docker Desktop共享驱动器设置

2. **"数据集目录不存在"错误:**
   - 检查Windows主机上的数据目录是否存在
   - 确认路径格式正确（使用正斜杠）

3. **"无法访问目录内容"错误:**
   - 检查目录权限
   - 确认Docker有足够权限访问数据目录

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
