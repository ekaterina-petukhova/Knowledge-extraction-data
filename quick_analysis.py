import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import sys

def main():
    # 1. Загрузка данных
    try:
        df = pd.read_csv('final_analysis_cleaned.csv')
    except FileNotFoundError:
        print("Ошибка: Файл final_analysis_cleaned.csv не найден.")
        return

    df['year'] = pd.to_numeric(df['year'], errors='coerce')

    # 2. Разделение на периоды
    before = df[df['year'] < 2022]
    after = df[df['year'] >= 2022]

    print(f"Загружено записей: {len(df)}")
    print(f"Период ДО 2022: {len(before)} записей")
    print(f"Период ПОСЛЕ 2022: {len(after)} записей\n")

    # 3. Список стоп-слов
    # 3. Обновленный список стоп-слов
    my_stop_words = [
        'exhibition', 'presents', 'суть', 'выставки', 'выставке', 
        'showcasing', 'featuring', 'artistic', 'explores',
        'the', 'of', 'and', 'to', 'is', 'in', 'from', 'are', 'with', 'this',
        'by', 'his', 'that', 'из', 'его', 'their', 'through', 'show'
    ]

    # 4. Функция анализа
    def get_top_keywords(text_series, n=15):
        # Используем параметр для обработки слов
        vec = TfidfVectorizer(stop_words=my_stop_words, max_features=1000)
        tfidf = vec.fit_transform(text_series.fillna("").astype(str))
        
        words = vec.get_feature_names_out()
        sums = tfidf.sum(axis=0)
        
        # Создаем список пар (слово, вес)
        data = []
        for i in range(len(words)):
            data.append((words[i], sums[0, i]))
        
        # Сортировка по весу TF-IDF
        return sorted(data, key=lambda x: x[1], reverse=True)[:n]

    # 5. Вывод результатов
    print("--- Ключевые слова ДО 2022 ---")
    results_before = get_top_keywords(before['text_to_analyze'])
    for word, score in results_before:
        print(f"{word}: {score:.4f}")

    print("\n--- Ключевые слова ПОСЛЕ 2022 ---")
    results_after = get_top_keywords(after['text_to_analyze'])
    for word, score in results_after:
        print(f"{word}: {score:.4f}")

if __name__ == "__main__":
    main()