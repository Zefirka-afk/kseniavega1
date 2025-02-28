import pandas as pd
import numpy as np
import rectools as rt
from rectools.models import PopularModel, UserKNNModel
from rectools.dataset import Dataset
from rectools.metrics import precision_at_k, recall_at_k, map_at_k
from sklearn.model_selection import train_test_split

# Пути к файлам
DATA_PATH = "dataset/"
TRAIN_FILE = DATA_PATH + "train.csv"
TEST_FILE = DATA_PATH + "test.csv"
SUBMISSION_FILE = "submission.csv"

# Загрузка данных
train_df = pd.read_csv(TRAIN_FILE)
test_df = pd.read_csv(TEST_FILE)

# Разделение данных на train/val
train_data, val_data = train_test_split(train_df, test_size=0.2, random_state=42)

# Создание датасета
dataset = Dataset.construct(train_data, user_col="user_id", item_col="item_id", feedback_col="rating")
val_dataset = Dataset.construct(val_data, user_col="user_id", item_col="item_id", feedback_col="rating")

# Инициализация моделей
pop_model = PopularModel()
pop_model.fit(dataset)

knn_model = UserKNNModel(K=10, similarity="cosine")
knn_model.fit(dataset)

# Функция предсказания рекомендаций
def predict(model):
    user_ids = test_df["user_id"].unique()
    recommendations = model.recommend(user_ids, dataset, k=10)  # Топ-10 рекомендаций
    return recommendations

# Оценка моделей на валидации
def evaluate_model(model):
    user_ids = val_data["user_id"].unique()
    recs = model.recommend(user_ids, dataset, k=10)
    precision = precision_at_k(val_dataset, recs, k=10)
    recall = recall_at_k(val_dataset, recs, k=10)
    map_score = map_at_k(val_dataset, recs, k=10)
    print(f"Precision@10: {precision:.4f}, Recall@10: {recall:.4f}, MAP@10: {map_score:.4f}")

# Сохранение предсказаний в CSV
def save_predictions(predictions, filename=SUBMISSION_FILE):
    predictions.to_csv(filename, index=False)
    print(f"Predictions saved to {filename}")

# Запуск
if __name__ == "__main__":
    print("Evaluating Popular Model...")
    evaluate_model(pop_model)
    
    print("Evaluating UserKNN Model...")
    evaluate_model(knn_model)
    
    print("Generating final predictions...")
    preds = predict(knn_model)  # Используем UserKNN для финальных рекомендаций
    save_predictions(preds)