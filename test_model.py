import os
import re
import shutil
from typing import List, Dict, Optional

import cv2
import yaml
from label_studio_ml.model import LabelStudioMLBase
from label_studio_ml.response import ModelResponse
from label_studio_ml.utils import get_env,get_local_path
import requests

ROOT = os.path.join(os.path.dirname(__file__))
print('=> ROOT = ', ROOT)
os.environ['HOSTNAME'] = 'http://192.168.1.66:8080'
os.environ['API_KEY'] = '03420aa8db49e15aa10ae1b2c52c6ec3294ab8c9'
HOSTNAME = get_env('HOSTNAME')
API_KEY = get_env('API_KEY')
print('=> LABEL STUDIO HOSTNAME = ', HOSTNAME)
if not API_KEY:
    print('=> WARNING! API_KEY is not set')

with open(os.path.join(ROOT, "conf.yaml"), errors='ignore') as f:
    conf = yaml.safe_load(f)


class NewModel(LabelStudioMLBase):
    """Custom ML Backend model
    """
    
    def setup(self):
        """Configure any parameters of your model here
        """
        self.set("model_version", "0.0.1")

    def predict(self, tasks: List[Dict], context: Optional[Dict] = None, **kwargs) -> ModelResponse:
        """ Write your inference logic here
            :param tasks: [Label Studio tasks in JSON format](https://labelstud.io/guide/task_format.html)
            :param context: [Label Studio context in JSON format](https://labelstud.io/guide/ml_create#Implement-prediction-logic)
            :return model_response
                ModelResponse(predictions=predictions) with
                predictions: [Predictions array in JSON format](https://labelstud.io/guide/export.html#Label-Studio-JSON-format-of-annotated-tasks)
        """
        """print(f'''\
        Run prediction on {tasks}
        Received context: {context}
        Project ID: {self.project_id}
        Label config: {self.label_config}
        Parsed JSON Label config: {self.parsed_label_config}
        Extra params: {self.extra_params}''')
        """
        predictions = []

        #file_path = self.get_local_path(tasks[0]['data']['image'], task_id=tasks[0]['id'])
        in_file_path = tasks[0]['data']['image']
        print(f'''Run file_path on {in_file_path}''')
        file_path = in_file_path.replace("/data/", "/data/VideoInference/label-studio/data/media/")
        url = 'https://host1.connecttrend.cn/predict/predict'
        query_params = {
            'q': '框出图片中的火焰',
            'timeout': 15,
        }

        with open(file_path, 'rb') as f:
            files = {'file': f}
            response = requests.post(url, files=files, params=query_params, verify=False)

            if response.status_code == 200:
                # 处理响应数据
                """return response.json()"""
                print(f'''response.json() on {response.json()}''')
                box_pattern = r"<box>\((\d+),(\d+)\),\((\d+),(\d+)\)</box>"
                matches = re.findall(box_pattern, str(response.json()))
                image = cv2.imread(file_path)
                h, w = image.shape[0], image.shape[1]
                for match in matches:
                    box_area = [
                        int(float(match[0]) / 1000 * w),
                        int(float(match[1]) / 1000 * h),
                        int(float(match[2]) / 1000 * w),
                        int(float(match[3]) / 1000 * h),
                    ]
                    x1, y1, x2, y2 = float(box_area[0]/w*100), float(box_area[1]/h*100), float(box_area[2]/w*100), float(box_area[3]/h*100)
                    predictions.append({
                        "result": [
                            {
                                "from_name": "label",
                                "to_name": "image",
                                "type": "rectanglelabels",
                                "value": {
                                    "x": x1,
                                    "y": y1,
                                    "width": x2 - x1,
                                    "height": y2 - y1,
                                    "rectanglelabels": ["fire"],
                                },
                            }
                        ],
                        "score": 0.95,
                        "model_version": "yolo-v8",
                    })
            else:
                # 处理错误
                """raise Exception(f'http status code: {response.status_code}')"""
                print(response.status_code)

        # predictions = [
        #     {
        #       "result": [
        #         {
        #           "from_name": "label",
        #           "to_name": "image",
        #           "type": "rectanglelabels",
        #           "value": {
        #             "x": 10,
        #             "y": 30,
        #             "width": 50,
        #             "height": 60,
        #             "rectanglelabels": ["fire"],
        #           }
        #         }
        #       ],
        #       "score": 0.95,
        #       "model_version": "yolo-v8"
        #     }
        # ]
        print(predictions)
        return ModelResponse(predictions=predictions)
    
    def fit(self, event, data, **kwargs):
        """
        This method is called each time an annotation is created or updated
        You can run your logic here to update the model and persist it to the cache
        It is not recommended to perform long-running operations here, as it will block the main thread
        Instead, consider running a separate process or a thread (like RQ worker) to perform the training
        :param event: event type can be ('ANNOTATION_CREATED', 'ANNOTATION_UPDATED', 'START_TRAINING')
        :param data: the payload received from the event (check [Webhook event reference](https://labelstud.io/guide/webhook_reference.html))
        """

        if event == 'START_TRAINING':
            # use cache to retrieve the data from the previous fit() runs
            old_data = self.get('my_data')
            old_model_version = self.get('model_version')
            print(f'Old data: {old_data}')
            print(f'Old model version: {old_model_version}')

            # store new data to the cache
            self.set('my_data', 'my_new_data_value')
            self.set('model_version', 'my_new_model_version')
            print(f'New data: {self.get("my_data")}')
            print(f'New model version: {self.get("model_version")}')


            print('fit() completed successfully.')
            print(f'event--START_TRAINING: {event}')
            print(f'data--: {data}')
            print(f'**kwargs--: {kwargs}')

            project_id = data['project']['id']
            if self.gen_train_data(project_id):
                # 使用 yolo 的方法训练模型
                from ultralytics import YOLO

                model = YOLO("yolov8n.pt")
                model.info()
                results = model.train(data="/data/VideoInference/datasets/fire/data.yaml", epochs=100, imgsz=640)
                print(results)
                print("model train complete!")
            else:
                raise "gen_train_data error"
        # else:
        #     print(f'ANNOTATION_UPDATED OR ANNOTATION_CREATED: {event}')

    def gen_train_data(self, project_id):
        import zipfile
        download_url = f'{HOSTNAME.rstrip("/")}/api/projects/{project_id}/export?export_type=YOLO&download_all_tasks=true'
        response = requests.get(download_url, headers={'Authorization': f'Token {API_KEY}'})
        # print(response.json())
        zip_path = os.path.join(conf['datasetdir'], "fire.zip")
        train_path = os.path.join(conf['datasetdir'], "fire")

        with open(zip_path, 'wb') as file:
            file.write(response.content)  # 通过二进制写文件的方式保存获取的内容
            file.flush()
        f = zipfile.ZipFile(zip_path)  # 创建压缩包对象
        f.extractall(train_path)  # 压缩包解压缩
        f.close()
        os.remove(zip_path)

        import random

        # 设置目录路径
        image_dir = os.path.join(train_path, "images")
        label_dir = os.path.join(train_path, "labels")

        # 获取图片和txt文件列表
        images = os.listdir(image_dir)
        labels = os.listdir(label_dir)

        # 随机打乱图片列表
        random.shuffle(images)

        # 计算训练集、验证集和测试集的数量
        total_images = len(images)
        train_count = int(total_images * 0.7)
        val_count = int(total_images * 0.2)
        test_count = total_images - train_count - val_count

        # 分配文件到训练集、验证集和测试集
        train_images = images[:train_count]
        val_images = images[train_count:train_count + val_count]
        test_images = images[train_count + val_count:]

        shutil.rmtree(os.path.join(train_path, "train/images"))
        shutil.rmtree(os.path.join(train_path, "valid/images"))
        shutil.rmtree(os.path.join(train_path, "test/images"))
        shutil.rmtree(os.path.join(train_path, "train/labels"))
        shutil.rmtree(os.path.join(train_path, "valid/labels"))
        shutil.rmtree(os.path.join(train_path, "test/labels"))
        os.makedirs(os.path.join(train_path, "train/images"), exist_ok=True)
        os.makedirs(os.path.join(train_path, "valid/images"), exist_ok=True)
        os.makedirs(os.path.join(train_path, "test/images"), exist_ok=True)
        os.makedirs(os.path.join(train_path, "train/labels"), exist_ok=True)
        os.makedirs(os.path.join(train_path, "valid/labels"), exist_ok=True)
        os.makedirs(os.path.join(train_path, "test/labels"), exist_ok=True)
        # 移动文件到对应的目录
        # 移动文件到对应的目录
        for image in train_images:
            # 移动图片和标签到训练集目录
            shutil.move(os.path.join(image_dir, image), os.path.join(train_path, "train/images"))  # 请改成你自己的训练集存放图片的文件夹目录
            shutil.move(os.path.join(label_dir, image[:-4] + '.txt'),
                        os.path.join(train_path, "train/labels"))  # 请改成你自己的训练集存放标签的文件夹目录

        for image in val_images:
            # 移动图片和标签到验证集目录
            shutil.move(os.path.join(image_dir, image), os.path.join(train_path, "valid/images"))  # 请改成你自己的验证集存放图片的文件夹目录
            shutil.move(os.path.join(label_dir, image[:-4] + '.txt'),
                        os.path.join(train_path, "valid/labels"))  # 请改成你自己的验证集存放标签的文件夹目录

        for image in test_images:
            # 移动图片和标签到测试集目录
            shutil.move(os.path.join(image_dir, image), os.path.join(train_path, "test/images"))  # 请改成你自己的测试集存放图片的文件夹目录
            shutil.move(os.path.join(label_dir, image[:-4] + '.txt'),
                        os.path.join(train_path, "test/labels"))  # 请改成你自己的测试集存放标签的文件夹目录
        if os.path.exists(os.path.join(train_path, "data.yaml")):
            os.remove(os.path.join(train_path, "data.yaml"))
        shutil.copy(os.path.join(conf['datasetdir'], "data.yaml"), train_path)
        return True
