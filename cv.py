import torch
import pandas as pd
import os
import shutil
import random
from ultralytics import YOLO

# Настройки
DATA_DIR = "dataset/"
TRAIN_DIR = os.path.join(DATA_DIR, "train")
VAL_DIR = os.path.join(DATA_DIR, "val")
BATCH_SIZE = 16
EPOCHS = 10
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
MODEL_PATH = "yolov8n-cls.pt"  # Используем предобученную YOLOv8 для классификации
VAL_SPLIT = 0.2  # 20% данных отдаем на валидацию

# Функция для разбиения данных на train/val
if not os.path.exists(VAL_DIR):
    os.makedirs(VAL_DIR)
    for class_name in os.listdir(TRAIN_DIR):
        class_path = os.path.join(TRAIN_DIR, class_name)
        val_class_path = os.path.join(VAL_DIR, class_name)
        if os.path.isdir(class_path):
            os.makedirs(val_class_path, exist_ok=True)
            images = os.listdir(class_path)
            random.shuffle(images)
            val_size = int(len(images) * VAL_SPLIT)
            for img in images[:val_size]:
                shutil.move(os.path.join(class_path, img), os.path.join(val_class_path, img))

# Загрузка модели YOLO (при появлении YOLOv11 заменить путь на соответствующую версию)
model = YOLO(MODEL_PATH)

# Обучение модели на кастомном датасете с валидационной выборкой
model.train(data=TRAIN_DIR, epochs=EPOCHS, imgsz=224, batch=BATCH_SIZE, device=DEVICE, val=VAL_DIR)

# Функция предсказания на тестовых данных
def predict():
    test_images = sorted(os.listdir(os.path.join(DATA_DIR, "test")))  # Загружаем список изображений из тестовой папки
    predictions = []
    for img_name in test_images:
        img_path = os.path.join(DATA_DIR, "test", img_name)
        results = model(img_path)  # Делаем предсказание YOLO
        predicted_label = results[0].probs.top1  # Получаем индекс предсказанного класса
        predictions.append((img_name, model.names[predicted_label]))  # Преобразуем индекс в имя класса
    return predictions

# Сохранение предсказаний в CSV
def save_predictions(predictions, filename="submission.csv"):
    df = pd.DataFrame(predictions, columns=["name", "label"])
    df.to_csv(filename, index=False)
    print(f"Predictions saved to {filename}")

# Запуск
if __name__ == "__main__":
    preds = predict()
    save_predictions(preds)
