import re
import pandas as pd

INPUT_FILE = 'tretyakov_exhibitions_2014_2026.csv'
OUTPUT_FILE = 'tretyakov_cleaned.csv'

# Наблюдение по сырым данным: реальный кураторский текст на странице
# Третьяковки всегда идёт после одного из этих заголовков-маркеров
# ("О мероприятии" — почти везде, "Описание" — у части старых страниц),
# а до него — сплошное меню/билеты/часы работы/адрес.
START_MARKERS = ["О мероприятии", "Описание"]

# После реального текста снова начинается мусор: список программ/экскурсий
# к выставке, кнопка "поделиться" и т.п.
END_MARKERS = ["ПОДЕЛИТЬСЯ", "Программа к выставке", "ЧИТАТЬ ДАЛЕЕ"]


def extract_real_description(text):
    if not isinstance(text, str):
        return ""

    start = -1
    for marker in START_MARKERS:
        idx = text.find(marker)
        if idx != -1:
            start = idx + len(marker)
            break

    if start == -1:
        # Маркер не найден вообще — на всякий случай возвращаем как есть,
        # чтобы не терять запись молча (таких случаев в датасете не было,
        # но если появятся на новых данных, лучше не терять текст).
        return re.sub(r"\s+", " ", text).strip()

    end = len(text)
    for marker in END_MARKERS:
        idx = text.find(marker, start)
        if idx != -1:
            end = min(end, idx)

    cleaned = text[start:end]
    return re.sub(r"\s+", " ", cleaned).strip()


def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Загружено записей: {len(df)}")

    df['description'] = df['description'].apply(extract_real_description)

    empty = (df['description'].str.len() < 20).sum()
    print(f"Записей с очень коротким/пустым описанием после чистки: {empty}")

    lens = df['description'].str.len()
    print(f"Средняя длина описания после чистки: {lens.mean():.0f} символов")
    print(f"Медиана: {lens.median():.0f} символов")

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\nСохранено: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()