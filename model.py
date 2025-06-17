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
                
                print(f'开始训练项目: {project_title} (ID: {project_id})')
                
                # 生成训练数据
                if self.gen_train_data(project_id):
                    print("=== 开始训练 ===")
                    # 使用 yolo 的方法训练模型
                    from ultralytics import YOLO
                    
                    # 获取训练数据路径 - 使用更新后的DATASET_DIR
                    dataset_dir = os.getenv("DATASET_DIR",)
                    data_yaml_path = os.path.join(dataset_dir, "data.yaml")
                    
                    print(f"使用训练数据路径: {dataset_dir}")
                    print(f"data.yaml路径: {data_yaml_path}")
                    
                    # 检查数据文件是否存在
                    if not os.path.exists(data_yaml_path):
                        raise FileNotFoundError(f"训练数据文件不存在: {data_yaml_path}")
                    
                    # 创建新模型或加载现有模型
                    model_path = os.getenv("MODEL_PATH", "yolov11n.pt")
                    model = YOLO(model_path)
                    
                    # 训练参数
                    epochs = int(os.getenv("TRAIN_EPOCHS", "5"))
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
                    
                    # 保存训练好的模型
                    best_model_path = Path(model.trainer.save_dir) / "weights" / "best.pt"
                    if best_model_path.exists():
                        model_save_dir = os.getenv("MODEL_SAVE_DIR", dataset_dir)
                        final_model_path = os.path.join(model_save_dir, f"trained_model_{project_id}.pt")
                        shutil.copy(str(best_model_path), final_model_path)
                        
                        # 更新模型版本信息
                        self.set("model_version", f"trained-{project_id}")
                        self.set("model_path", final_model_path)
                        
                        print(f"模型训练完成，保存至: {final_model_path}")
                        print(f"训练结果: {results}")
                    else:
                        raise RuntimeError("训练完成但未找到最佳模型文件")
                        
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

        try:
            HOSTNAME = os.getenv("LABEL_STUDIO_URL")
            API_KEY = os.getenv("LABEL_STUDIO_API_KEY")
            dataset_dir = os.getenv("DATASET_DIR", "/data/dataset")
            
            print(f"=== 环境变量调试信息 ===")
            print(f"HOSTNAME: {HOSTNAME}")
            print(f"API_KEY: {API_KEY[:10]}..." if API_KEY else "API_KEY: None")
            print(f"DATASET_DIR: {dataset_dir}")
            print(f"当前工作目录: {os.getcwd()}")
            print(f"容器内环境: {'Docker' if os.path.exists('/.dockerenv') else '本地'}")
            
            # 检查数据集目录是否存在
            if not os.path.exists(dataset_dir):
                print(f"警告: 数据集目录不存在: {dataset_dir}")
                print("尝试创建目录...")
                os.makedirs(dataset_dir, exist_ok=True)
            
            # 检查训练数据目录结构
            train_path = os.path.join(dataset_dir, "train")
            image_dir = os.path.join(train_path, "images")
            label_dir = os.path.join(train_path, "labels")
            # 创建目录
            os.makedirs(image_dir, exist_ok=True)
            os.makedirs(label_dir, exist_ok=True)
            
            print(f"=== 训练数据目录检查 ===")
            print(f"训练路径: {train_path}")
            print(f"图像目录: {image_dir}")
            print(f"标签目录: {label_dir}")
            
            # 检查目录是否存在
            print(f"训练路径存在: {os.path.exists(train_path)}")
            print(f"图像目录存在: {os.path.exists(image_dir)}")
            print(f"标签目录存在: {os.path.exists(label_dir)}")

            # 检查图像文件
            if os.path.exists(image_dir):
                images = [f for f in os.listdir(image_dir) if f.lower().endswith((".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif"))]
                print(f"图像目录中的文件数量: {len(images)}")
                if len(images) > 0:
                    print(f"前5个图像文件: {images[:5]}")
                else:
                    print("警告: 图像目录为空！")
                    print("可能的原因:")
                    print("1. Docker挂载路径配置不正确")
                    print("2. Windows路径格式问题")
                    print("3. 数据目录权限问题")
                    return False
            
            else:
                print(f"图像目录不存在: {image_dir}")
                return False
            
            # 检查标签文件
            if os.path.exists(label_dir):
                labels = [f for f in os.listdir(label_dir) if f.endswith('.txt')]
                print(f"标签目录中的文件数量: {len(labels)}")
                if len(labels) > 0:
                    print(f"前5个标签文件: {labels[:5]}")
                else:
                    print("警告: 标签目录为空！")
            
            # 创建data.yaml
            data_yaml_path = os.path.join(dataset_dir, "data.yaml")
            if not os.path.exists(data_yaml_path):
                print(f"未找到data.yaml，请检查数据集目录结构")
            else:
                print(f"已存在data.yaml: {data_yaml_path}")
            
            print(f"=== 训练数据准备完成 ===")
            print(f"数据集目录: {dataset_dir}")
            print(f"图像数量: {len(images)}")
            print(f"标签数量: {len(labels) if 'labels' in locals() else 0}")
            
            return True

        except Exception as e:
            print(f"生成训练数据时发生错误: {str(e)}")
            import traceback
            traceback.print_exc()
            return False

