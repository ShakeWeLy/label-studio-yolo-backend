import os
import requests
import os
import shutil
from pathlib import Path

from PIL import Image, ImageOps

import numpy as np
import ultralytics

from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse

from label_studio_sdk._extensions.label_studio_tools.core.utils.io import get_local_path


class YOLO(LabelStudioMLBase):
    def setup(self) -> None:
        # Task type
        self.task_types = ["detection", "segmentation"]
        self.set_task_type()

        # Model and labels
        self.model = self.load_model()
        self.labels = self.model.names
        self.from_name = "label"
        self.to_name = "image"

    def set_task_type(self) -> None:
        self.task_type = os.getenv("TASK_TYPE")
        assert self.task_type in self.task_types, \
            f"Task type must be one \
                of {self.task_types}, set TASK_TYPE in your .env file."

        # Pred func
        self.pred_funcs = {"detection": self.detect,
                           "segmentation": self.segment}
        self.pred_func = self.pred_funcs[self.task_type]

    def load_model(self) -> ultralytics.YOLO:
        model_dir = os.getenv("MODEL_DIR")
        model_filename = os.getenv("MODEL_FILENAME")
        model_filepath = os.path.join(model_dir, model_filename)
        model = ultralytics.YOLO(model_filepath)
        self.set("model_version", f"yolo-{model.task}")

        return model

    def load_image(self,
                   task: dict) -> Image.Image:
        # Get image path and task id
        image_path = task.get("data").get("image")
        task_id = task.get("id")

        # Extract local image path
        file_path = self.get_local_path(image_path,
                                        task_id=task_id)

        # Open image
        image = Image.open(file_path)
        image = ImageOps.exif_transpose(image)

        return image

    def predict(self,
                tasks: list[dict],
                **kwargs) -> ModelResponse:
        predictions = self.pred_func(tasks, **kwargs)

        return predictions

    def detect(self, tasks: list[dict], **kwargs) -> ModelResponse:
        # Create blank list with results
        results = []

        # Create variable to calcualte scores
        score = 0
        counter = 0

        for task in tasks:
            # Load image
            image = self.load_image(task=task)

            # Height and width of image
            image_width, image_height = image.size

            # Getting prediction using model
            model_prediction = self.model.predict(image)

            # Getting boxes from model prediction
            for pred in model_prediction:
                for i, box in enumerate(pred.boxes):

                    # Points
                    xyxy = box.xyxy[0].tolist()
                    x = xyxy[0] / image_width * 100
                    y = xyxy[1] / image_height * 100
                    width = (xyxy[2] - xyxy[0]) / image_width * 100
                    height = (xyxy[3] - xyxy[1]) / image_height * 100

                    # Label
                    labels = [self.labels[int(box.cls.item())]]

                    result = {"from_name": self.from_name,
                              "to_name": self.to_name,
                              "id": str(i),
                              "type": "rectanglelabels",
                              "score": box.conf.item(),
                              "original_width": image_width,
                              "original_height": image_height,
                              "image_rotation": 0,
                              "value": {
                                  "rotation": 0,
                                  "x": x,
                                  "y": y,
                                  "width": width,
                                  "height":  height,
                                  "rectanglelabels": labels}}

                    # Append prediction to predictions
                    results.append(result)

                    # Add score
                    score += box.conf.item()
                    counter += 1

        predictions = [{"result": results,
                       "score": score / counter,
                        "model_version": self.model_version}]

        return ModelResponse(predictions=predictions)

    def segment(self, tasks: list[dict], **kwargs) -> ModelResponse:
        # Create blank list with results
        results = []

        # Create variable to calcualte scores
        score = 0
        counter = 0

        for task in tasks:
            # Load image
            image = self.load_image(task=task)
            print("load_image")
            # Height and width of image
            image_width, image_height = image.size

            # Getting prediction using model
            model_prediction = self.model.predict(image)

            # Getting mask segments, boxes from model prediction
            for pred in model_prediction:
                for i, (box, segm) in enumerate(zip(pred.boxes, pred.masks.xy)):

                    # 2D array with poligon points
                    points = segm / \
                        np.array([image_width, image_height]) * 100
                    points = points.tolist()

                    # Label
                    labels = [self.labels[int(box.cls.item())]]

                    # Regions and predictions
                    result = {"from_name": self.from_name,
                              "to_name": self.to_name,
                              "id": str(i),
                              "type": "polygonlabels",
                              "score": box.conf.item(),
                              "original_width": image_width,
                              "original_height": image_height,
                              "image_rotation": 0,
                              "value": {"points": points,
                                        "polygonlabels": labels}}

                    # Append prediction to predictions
                    results.append(result)

                    # Add score
                    score += box.conf.item()
                    counter += 1

        predictions = [{"result": results,
                       "score": score / counter,
                        "model_version": self.model_version}]

        return ModelResponse(predictions=predictions)

    def fit(self, event, data, **kwargs):
        if event == 'START_TRAINING':
            try:
                # 获取项目信息
                project_id = data['project']['id']
                project_title = data['project']['title']
                print("=== 开始训练 ===")
                print(f'开始训练项目: {project_title} (ID: {project_id})')
                
                # 生成训练数据
                if self.gen_train_data(project_id):
                    # 获取训练数据路径
                    dataset_dir = os.getenv("DATASET_DIR")
                    data_yaml_path = os.path.join(dataset_dir, "data.yaml")
                    print(f"使用训练数据路径: {dataset_dir}")
                    print(f"data.yaml路径: {data_yaml_path}")
                    
                    # 检查数据文件是否存在
                    if not os.path.exists(data_yaml_path):
                        raise FileNotFoundError(f"训练数据文件不存在: {data_yaml_path}")
                    
                    # 加载本地模型进行finetune
                    model_dir = os.getenv("MODEL_DIR", "./models")
                    model_filename = os.getenv("MODEL_FILENAME", "best.pt")
                    model_path = os.path.join(model_dir, model_filename)
                    print(f"加载模型进行finetune: {model_path}")
                    
                    # 检查模型文件是否存在
                    if not os.path.exists(model_path):
                        print(f"警告: 模型文件不存在 {model_path}，将使用默认模型")
                        model = ultralytics.YOLO("yolov11n.pt") # 使用默认模型作为项目初始化
                    else:
                        model = ultralytics.YOLO(model_path)
                    
                    # 训练参数
                    epochs = int(os.getenv("TRAIN_EPOCHS", "10"))
                    imgsz = int(os.getenv("TRAIN_IMGSZ", "640"))
                    batch_size = int(os.getenv("TRAIN_BATCH_SIZE", "16"))
                    print(f"开始训练，参数: epochs={epochs}, imgsz={imgsz}, batch_size={batch_size}")
                    
                    # 开始训练
                    results = model.train(
                        data=data_yaml_path,
                        epochs=epochs,
                        imgsz=imgsz,
                        batch=batch_size,
                        save=True,
                        project=os.path.join(dataset_dir, "runs"),
                        name=f"project_{project_id}_{project_title}"
                    )
                    
                    print(f"训练完成!")
                    # 保存训练好的模型到MODEL_DIR
                    # best_model_path = Path(model.trainer.save_dir) / "weights" / "best.pt"
                    # if best_model_path.exists():
                    #     # 保存到MODEL_DIR目录
                    #     final_model_path = os.path.join(model_dir, model_filename)
                    #     shutil.copy(str(best_model_path), final_model_path)
                        
                    #     # 更新模型版本信息
                    #     self.set("model_version", f"trained-{project_id}")
                    #     self.set("model_path", final_model_path)
                        
                    #     print(f"模型训练完成，保存至: {final_model_path}")
                    #     print(f"训练结果: {results}")
                        
                    #     # 重新加载模型
                    #     self.model = ultralytics.YOLO(final_model_path)
                    #     print("模型已重新加载")
                        
                else:
                    raise RuntimeError("生成训练数据失败")
            except Exception as e:
                print(f"训练过程中发生错误: {str(e)}")
                raise e

    def gen_train_data(self, project_id):
        import zipfile
        import random
        from datetime import datetime
        import json
        import urllib.parse

        try:
            HOSTNAME = os.getenv("LABEL_STUDIO_URL")
            API_KEY = os.getenv("LABEL_STUDIO_API_KEY")
            dataset_dir = os.getenv("DATASET_DIR", "/data/dataset")
            
            print(f"=== 环境变量信息 ===")
            print(f"HOSTNAME: {HOSTNAME}")
            print(f"API_KEY: {API_KEY[:10]}..." if API_KEY else "API_KEY: None")
            print(f"DATASET_DIR: {dataset_dir}")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"容器内环境: {'Docker' if os.path.exists('/.dockerenv') else '本地'}")
            
            # 检查必要的环境变量
            if not HOSTNAME or not API_KEY:
                raise ValueError("缺少必要的环境变量: LABEL_STUDIO_URL 或 LABEL_STUDIO_API_KEY")
            
            # 创建数据集目录
            os.makedirs(dataset_dir, exist_ok=True)
            print(f"数据集目录已创建/确认: {dataset_dir}")
            
            # 目录名
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            train_dir_name = f"project_{project_id}_{timestamp}"
            train_path = os.path.join(dataset_dir, train_dir_name)
            os.makedirs(train_path, exist_ok=True)
            print(f"训练目录路径: {train_path}")
            
            # 1. 首先获取项目中的任务列表
            print("=== 获取项目任务 ===")
            tasks_url = f'{HOSTNAME.rstrip("/")}/api/projects/{project_id}/tasks/'
            print(f"任务列表URL: {tasks_url}")
            
            tasks_response = requests.get(tasks_url, headers={'Authorization': f'Token {API_KEY}'})
            print(f"任务列表响应状态码: {tasks_response.status_code}")
            
            if tasks_response.status_code != 200:
                print(f"获取任务列表失败: {tasks_response.status_code} {tasks_response.text}")
                return False
            
            tasks = tasks_response.json()
            if len(tasks) == 0:
                print("警告: 项目中没有任务！")
                return False
            else:
                print(f"找到 {len(tasks)} 个任务")
            
            # 2. 下载YOLO格式的标签数据
            print("=== 下载YOLO标签 ===")
            download_url = f'{HOSTNAME.rstrip("/")}/api/projects/{project_id}/export?export_type=YOLO&download_all_tasks=true'
            print(f"下载URL: {download_url}")
            
            response = requests.get(download_url, headers={'Authorization': f'Token {API_KEY}'})
            print(f"下载响应状态码: {response.status_code}")
            if response.status_code != 200:
                print(f"下载数据失败: {response.status_code} {response.text}")
                return False
            zip_path = os.path.join(dataset_dir, f"{train_dir_name}.zip")
            print(f"ZIP文件路径: {zip_path}")
            print(f"下载数据大小: {len(response.content)} 字节")

            # 标签数据解压和保存
            with open(zip_path, 'wb') as file:
                file.write(response.content)
            print(f"ZIP文件已保存: {zip_path}")
            with zipfile.ZipFile(zip_path) as f:
                print(f"ZIP文件内容:")
                for item in f.namelist():
                    print(f"  - {item}")
                f.extractall(train_path)
            
            os.remove(zip_path)
            print(f"ZIP文件已解压并删除")

            # 3. 单独下载图像
            print("=== 下载图像 ===")
            image_dir = os.path.join(train_path, "images")
            label_dir = os.path.join(train_path, "labels")
            os.makedirs(image_dir, exist_ok=True)
            if not os.path.exists(label_dir):
                print(f"警告: 标签目录不存在: {label_dir}")
                return False
            
            # 获取标签文件列表
            label_files = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
            print(f"标签文件数量: {len(label_files)}")
            
            # 下载对应的图像文件
            downloaded_images = []
            for task in tasks:
                task_id = task.get('id')
                task_data = task.get('data', {})
                image_url = task_data.get('image')
                
                if not image_url:
                    print(f"任务 {task_id} 没有图像URL")
                    continue
                
                # 构建完整的图像URL
                if image_url.startswith('http'):
                    full_image_url = image_url
                else:
                    full_image_url = f"{HOSTNAME.rstrip('/')}{image_url}"
                
                # 从URL中提取文件名
                parsed_url = urllib.parse.urlparse(full_image_url)
                image_filename = os.path.basename(parsed_url.path)
                
                # 如果没有扩展名，尝试从任务数据中获取
                if not any(image_filename.lower().endswith(ext) for ext in ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.tif']):
                    # 尝试从标签文件名推断图像文件名
                    for label_file in label_files:
                        if label_file.endswith('.txt'):
                            # 假设图像文件名与标签文件名相同（除了扩展名）
                            potential_image_name = label_file[:-4] + '.jpg'  # 尝试.jpg
                            if os.path.exists(os.path.join(image_dir, potential_image_name)):
                                image_filename = potential_image_name
                                break
                            potential_image_name = label_file[:-4] + '.png'  # 尝试.png
                            if os.path.exists(os.path.join(image_dir, potential_image_name)):
                                image_filename = potential_image_name
                                break
                
                # 下载图像文件
                try:
                    print(f"下载图像: {image_filename}")
                    image_response = requests.get(full_image_url, headers={'Authorization': f'Token {API_KEY}'})
                    if image_response.status_code == 200:
                        image_path = os.path.join(image_dir, image_filename)
                        with open(image_path, 'wb') as f:
                            f.write(image_response.content)
                        downloaded_images.append(image_filename)
                        print(f"✓ 成功下载: {image_filename}")
                    else:
                        print(f"✗ 下载失败: {image_filename} (状态码: {image_response.status_code})")
                except Exception as e:
                    print(f"✗ 下载错误: {image_filename} - {e}")
            print(f"成功下载 {len(downloaded_images)} 个图像文件")
            
            # 检查下载的图像文件
            images = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"))]
            labels = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
            
            print(f"最终图像文件数量: {len(images)}")
            print(f"最终标签文件数量: {len(labels)}")
            
            if len(images) == 0:
                print("警告: 没有找到图像文件！")
                return False
            
            # 数据集分割
            random.shuffle(images)
            total_images = len(images)
            train_count = int(total_images * 0.7)
            val_count = int(total_images * 0.2)
            test_count = total_images - train_count - val_count

            train_images = images[:train_count]
            val_images = images[train_count:train_count + val_count]
            test_images = images[train_count + val_count:]
            print(f"数据集分割: 训练集 {len(train_images)}, 验证集 {len(val_images)}, 测试集 {len(test_images)}")

            # 清理旧文件夹并创建新的
            for split in ["train", "val", "test"]:
                for sub in ["images", "labels"]:
                    p = os.path.join(train_path, split, sub)
                    if os.path.exists(p):
                        shutil.rmtree(p)
                    os.makedirs(p, exist_ok=True)

            def move_files(image_list, split):
                for image in image_list:
                    # 移动图像文件
                    src_img = os.path.join(image_dir, image)
                    dst_img = os.path.join(train_path, split, "images", image)
                    shutil.move(src_img, dst_img)
                    
                    # 移动对应的标签文件
                    label_file = image[:-4] + '.txt'
                    src_label = os.path.join(label_dir, label_file)
                    dst_label = os.path.join(train_path, split, "labels", label_file)
                    if os.path.exists(src_label):
                        shutil.move(src_label, dst_label)

            move_files(train_images, "train")
            move_files(val_images, "val")
            move_files(test_images, "test")

            # 创建或更新 data.yaml
            data_yaml_path = os.path.join(train_path, "data.yaml")
            if os.path.exists(data_yaml_path):
                os.remove(data_yaml_path)
            
            # 获取类别名称（从classes.txt、notes.json或标签文件中获取）
            class_names = self._get_class_names_from_labels(os.path.join(train_path, "train", "labels"))
            
            # 创建 data.yaml 内容
            yaml_content = f"""# YOLO 数据集配置文件
                                path: {train_path}  # 数据集根目录
                                train: train/images  # 训练图像相对路径
                                val: val/images      # 验证图像相对路径
                                test: test/images    # 测试图像相对路径

                                # 类别数量
                                nc: {len(class_names)}

                                # 类别名称
                                names: {class_names}
                                """
                                            
            with open(data_yaml_path, 'w', encoding='utf-8') as f:
                f.write(yaml_content)
            
            print(f"训练数据准备完成: {train_path}")
            print(f"训练集: {len(train_images)} 张图像")
            print(f"验证集: {len(val_images)} 张图像") 
            print(f"测试集: {len(test_images)} 张图像")
            print(f"类别: {class_names}")
            print(f"data.yaml 已创建: {data_yaml_path}")
            
            # 更新环境变量，让训练使用这个路径
            os.environ["DATASET_DIR"] = train_path
            print(f"已设置DATASET_DIR为: {train_path}")
            
            return True

        except Exception as e:
            print(f"生成训练数据时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

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

