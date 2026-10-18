"""Модуль очистки данных NYC Taxi для Шага 12."""

from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATE_COLUMNS, TAXI_DTYPES


def clean_taxi_data(file_paths: list[Path], output_path: Path) -> pd.DataFrame:
    print("ЗАПУСК ПАЙПЛАЙНА ОЧИСТКИ ДАННЫХ")
    
    # 1. Соединение файлов
    print("Этап 1: Соединение исходных файлов...")
    dfs = []
    total_input_rows = 0
    for path in file_paths:
        df_part = pd.read_csv(path, dtype=TAXI_DTYPES, parse_dates=DATE_COLUMNS)
        total_input_rows += len(df_part)
        dfs.append(df_part)
        
    df = pd.concat(dfs, ignore_index=True)
    print(f"  -> Исходных строк: {total_input_rows}, после объединения: {len(df)}")

    # 2. Нормализация имён столбцов
    print("Этап 2: Нормализация имён столбцов...")
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
    )

    # 3. Приведение типов и дат
    print("Этап 3: Приведение типов и дат...")
    for date_col in ["tpep_pickup_datetime", "tpep_dropoff_datetime"]:
        if date_col in df.columns:
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")

    # 4. Выявление скрытых пропусков
    print("Этап 4: Выявление скрытых пропусков...")
    df = df.replace(["нет данных", "None", "null", "-", "N/A", "unknown", ""], np.nan)
    coord_cols = ["pickup_latitude", "pickup_longitude", "dropoff_latitude", "dropoff_longitude"]
    for col in coord_cols:
        if col in df.columns:
            df[col] = df[col].replace(0, np.nan)

    # 5. Обработка пропусков в ключевых полях
    print("Этап 5: Удаление строк с пропусками в ключевых полях...")
    key_cols = ["tpep_pickup_datetime", "tpep_dropoff_datetime", "trip_distance", "fare_amount"]
    rows_before = len(df)
    df = df.dropna(subset=[c for c in key_cols if c in df.columns])
    print(f"  -> Удалено строк: {rows_before - len(df)}")

    # 6. Удаление дубликатов
    print("Этап 6: Удаление дубликатов...")
    rows_before = len(df)
    df = df.drop_duplicates()
    print(f"  -> Удалено полных дубликатов: {rows_before - len(df)}")

    # 7. Нормализация категорий
    print("Этап 7: Нормализация категорий...")
    if "store_and_fwd_flag" in df.columns:
        df["store_and_fwd_flag"] = (
            df["store_and_fwd_flag"].astype(str)
            .str.strip()
            .str.upper()
            .replace({"NAN": np.nan, "NONE": np.nan})
        )

    # 8. Проверка предметных ограничений (бизнес-правил)
    print("Этап 8: Проверка предметных ограничений...")
    rows_before = len(df)
    mask = (df["trip_distance"] >= 0) & (df["fare_amount"] >= 0)
    if "tpep_pickup_datetime" in df.columns and "tpep_dropoff_datetime" in df.columns:
        mask &= df["tpep_pickup_datetime"] <= df["tpep_dropoff_datetime"]
    df = df[mask]
    print(f"  -> Удалено строк с нарушением правил: {rows_before - len(df)}")

    # 9. Выявление выбросов по методу IQR
    print("Этап 9: Фильтрация выбросов (метод IQR)...")
    rows_before = len(df)
    if "fare_amount" in df.columns:
        q1 = df["fare_amount"].quantile(0.25)
        q3 = df["fare_amount"].quantile(0.75)
        iqr = q3 - q1
        lower_bound = q1 - 1.5 * iqr
        upper_bound = q3 + 1.5 * iqr
        df = df[(df["fare_amount"] >= lower_bound) & (df["fare_amount"] <= upper_bound)]
    print(f"  -> Удалено выбросов: {rows_before - len(df)}")

    # Итоговая сводка
    final_count = len(df)
    lost_rows = total_input_rows - final_count
    loss_ratio = (lost_rows / total_input_rows) * 100

    print("\n==========================================")
    print("ИТОГОВАЯ СВОДКА «БЫЛО - СТАЛО»:")
    print(f"Исходное число записей (Было): {total_input_rows}")
    print(f"Итоговое число записей (Стало): {final_count}")
    print(f"Всего удалено записей:         {lost_rows}")
    print(f"Доля потерянных строк:         {loss_ratio:.2f}%")
    print("==========================================")

    if loss_ratio > 10.0:
        print("ВНИМАНИЕ: Потеряно более 10% данных! Требуется обоснование в отчёте.")

    # Сохранение результата
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, compression="snappy", index=False)
    print(f"Чистый датасет успешно сохранён в: {output_path}")

    return df

if __name__ == "__main__":
    input_paths = [Path("data/interim/sample_200k.csv")]
    output_parquet = Path("data/processed/clean.parquet")
    clean_taxi_data(input_paths, output_parquet)