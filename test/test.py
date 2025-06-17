import os

# 检查是否存在images和labels目录
train_path = r'F:/_Work/data_/haoyi/dataset/train'
image_dir = os.path.join(train_path, "images")
label_dir = os.path.join(train_path, "labels")

# 如果目录不存在，则创建
if not os.path.exists(image_dir):
    os.makedirs(image_dir, exist_ok=True)
    print(f"创建图像目录: {image_dir}")
else:
    print(f"图像目录已存在: {image_dir}")
if not os.path.exists(label_dir):
    os.makedirs(label_dir, exist_ok=True)
    print(f"创建标签目录: {label_dir}")
else:
    print(f"标签目录已存在: {label_dir}")

images = os.listdir(image_dir)
print(f"图像目录中的文件数量: {len(images)}")  # 这里出问题了
if len(images) > 0:
    print(f"前5个图像文件: {images[:5]}")
else:
    print("警告: 图像目录为空！")
    print("可能的原因:")
    print("1. Label Studio 项目中没有上传图像")
    print("2. 图像文件路径配置不正确")
    print("3. 导出格式问题")