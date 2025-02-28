import pandas as pd
import numpy as np
import re
import string
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
import nltk
from nltk.corpus import stopwords
from pymorphy2 import MorphAnalyzer
import torch
from sentence_transformers import SentenceTransformer

nltk.download("stopwords")

# Загрузка данных
DATA_PATH = "dataset/"
TEXT_FILE = DATA_PATH + "text_data.csv"
RESULT_FILE = DATA_PATH + "similar_texts.csv"

# Инициализация модели эмбеддингов для русского языка
embedding_model = SentenceTransformer("sentence-transformers/distiluse-base-multilingual-cased-v1")

# Инициализация морфологического анализатора и стоп-слов
morph = MorphAnalyzer()
stop_words = set(stopwords.words("russian"))

# Предобработка текста
def preprocess_text(text):
    text = text.lower()
    text = re.sub(f"[{string.punctuation}]", "", text)  # Удаляем знаки препинания
    text = re.sub(r"\d+", "", text)  # Удаляем цифры
    words = text.split()
    words = [morph.parse(word)[0].normal_form for word in words if word not in stop_words]
    return " ".join(words)

# Загрузка и обработка данных
df = pd.read_csv(TEXT_FILE)
df.dropna(subset=["text"], inplace=True)  # Удаляем пустые строки
df.drop_duplicates(subset=["text"], inplace=True)  # Убираем дубликаты

df["clean_text"] = df["text"].apply(preprocess_text)

# Разделение данных на тренировочные и тестовые
train_texts, test_texts = train_test_split(df["clean_text"], test_size=0.2, random_state=42)

# Векторизация текста (TF-IDF)
vectorizer = TfidfVectorizer()
text_vectors = vectorizer.fit_transform(df["clean_text"])

# Генерация эмбеддингов
embeddings = embedding_model.encode(df["clean_text"].tolist(), convert_to_tensor=True)

# Функция для поиска похожих текстов и сохранения результатов в CSV
def find_similar(text, top_n=5, save_to_csv=False, use_embeddings=True):
    text = preprocess_text(text)
    
    if use_embeddings:
        text_vector = embedding_model.encode([text], convert_to_tensor=True)
        similarities = cosine_similarity(text_vector.cpu().numpy(), embeddings.cpu().numpy()).flatten()
    else:
        text_vector = vectorizer.transform([text])
        similarities = cosine_similarity(text_vector, text_vectors).flatten()
    
    top_indices = np.argsort(similarities)[-top_n:][::-1]
    result_df = df.iloc[top_indices][["text", "clean_text"]].copy()
    result_df["similarity"] = similarities[top_indices]
    
    if save_to_csv:
        result_df.to_csv(RESULT_FILE, index=False)
        print(f"Results saved to {RESULT_FILE}")
    
    return result_df

# Оценка точности модели
sample_test_texts = test_texts[:10].tolist()
predictions = [find_similar(text, top_n=1, use_embeddings=True).iloc[0]["clean_text"] for text in sample_test_texts]
accuracy = accuracy_score(sample_test_texts, predictions)
print(f"Model Accuracy: {accuracy:.4f}")

# Тест примера
if __name__ == "__main__":
    sample_text = "Мне нужен ноутбук с хорошей батареей и легким корпусом."
    similar_texts = find_similar(sample_text, save_to_csv=True, use_embeddings=True)
    print("Top similar texts:")
    print(similar_texts)
