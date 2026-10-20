"""Сквозной пайплайн обработки данных NYC Taxi (Шаг 13)."""

import argparse
from pathlib import Path

from src.cleaning import clean_taxi_data


def run_pipeline(input_file: str, output_file: str):
    print("ЗАПУСК СКВОЗНОГО ПАЙПЛАЙНА (ШАГ 13)")
    
    input_path = Path(input_file)
    output_path = Path(output_file)
    
    if not input_path.exists():
        print(f"Ошибка: Входной файл '{input_path}' не найден!")
        return

    # Запускаем нашу функцию очистки из модуля src/cleaning.py
    cleaned_df = clean_taxi_data([input_path], output_path)
    
    print("\nСквозной пайплайн успешно выполнен!")
    print(f"Итоговый размер датасета: {len(cleaned_df)} строк.")
    print(f"Результат сохранён в: {output_path}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Запуск сквозного пайплайна очистки NYC Taxi")
    parser.add_argument(
        "--input", 
        type=str, 
        default="data/raw/yellow_tripdata_2015-01.csv", 
        help="Путь к входному файлу"
    )
    parser.add_argument(
        "--output", 
        type=str, 
        default="data/processed/clean.parquet", 
        help="Путь для сохранения результата"
    )
    
    args = parser.parse_args()
    run_pipeline(args.input, args.output)