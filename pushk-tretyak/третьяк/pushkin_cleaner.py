import re
import pandas as pd

INPUT_FILE = 'pushkin_exhibitions_with_descriptions.csv'
OUTPUT_FILE = 'pushkin_cleaned.csv'

# Самый надёжный якорь на странице Пушкинского музея: кнопка "Стать другом"
# встречается ровно один раз в 216 из 225 страниц, прямо перед местом,
# где начинается реальный кураторский текст (после блока с покупкой
# билетов/экскурсий/программы к выставке).
PRIMARY_MARKER = "Стать другом"

# После самого якоря иногда остаются ещё несколько коротких фраз
# ("Сувениры", "Поделиться", "Доступно по Пушкинской карте",
# "Узнать больше", "Правила посещения") — их вырезаем отдельно.
TRAILING_PHRASES = [
    "Сувениры",
    "Поделиться",
    "Доступно по Пушкинской карте",
    "Узнать больше",
    "Правила посещения",
]

# Запасной маркер (используется, только если "Стать другом" не найден вовсе)
FALLBACK_MARKER = "Правила посещения"


def strip_trailing_phrases(text):
    """Убирает короткие мусорные фразы, которые могут идти сразу после якоря."""
    changed = True
    while changed:
        changed = False
        stripped = text.lstrip()
        for phrase in TRAILING_PHRASES:
            if stripped.startswith(phrase):
                stripped = stripped[len(phrase):]
                changed = True
        text = stripped
    return text


def extract_real_description(text):
    if not isinstance(text, str):
        return ""

    idx = text.rfind(PRIMARY_MARKER)

    if idx == -1:
        idx = text.rfind(FALLBACK_MARKER)
        if idx == -1:
            # Ни один маркер не найден — возвращаем как есть, чтобы не
            # терять запись молча.
            return re.sub(r"\s+", " ", text).strip()
        start = idx + len(FALLBACK_MARKER)
    else:
        start = idx + len(PRIMARY_MARKER)

    remainder = text[start:]
    remainder = strip_trailing_phrases(remainder)

    return re.sub(r"\s+", " ", remainder).strip()


def main():
    df = pd.read_csv(INPUT_FILE)
    print(f"Загружено записей: {len(df)}")

    df['description'] = df['description'].apply(extract_real_description)

    short = (df['description'].str.len() < 60).sum()
    print(f"Записей с очень коротким описанием после чистки (<60 симв.): {short}")

    lens = df['description'].str.len()
    print(f"Средняя длина после чистки: {lens.mean():.0f} символов")
    print(f"Медиана: {lens.median():.0f} символов")

    df.to_csv(OUTPUT_FILE, index=False, encoding='utf-8-sig')
    print(f"\nСохранено: {OUTPUT_FILE}")


if __name__ == "__main__":
    main()