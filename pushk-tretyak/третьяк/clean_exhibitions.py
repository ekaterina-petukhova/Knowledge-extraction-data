import pandas as pd

def clean_description(text):
    if not isinstance(text, str):
        return text

    marker = "Описание Фото"
    
    if marker in text:
        return text.split(marker, 1)[1].strip()
    

    trash_start = "КУПИТЬ БИЛЕТ"
    if trash_start in text:
        return text.rsplit(trash_start, 1)[1].strip()
        
    return text

def main():
    input_file = 'final_analysis_fixed.csv'
    output_file = 'final_analysis_cleaned.csv'
    
    try:
        df = pd.read_csv(input_file)
        
        if 'text_to_analyze' in df.columns:
            df['text_to_analyze'] = df['text_to_analyze'].apply(clean_description)
            df.to_csv(output_file, index=False)
            print(f"Готово! Очищенный файл сохранен как {output_file}")
        else:
            print(f"Колонка 'text_to_analyze' не найдена.")
            
    except Exception as e:
        print(f"Ошибка: {e}")

if __name__ == "__main__":
    main()
    