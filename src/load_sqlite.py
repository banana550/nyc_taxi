"""Пакетная загрузка очищенных данных в SQLite с измерением времени."""

import sqlite3
import time
from pathlib import Path

import pandas as pd


def find_file_upwards(filename, max_levels=3):
    """Автоматический поиск файла в проекте вверх по древу директорий."""
    current = (
        Path(__file__).resolve().parent if "__file__" in locals() else Path.cwd()
    )
    for _ in range(max_levels):
        found = list(current.rglob(filename))
        if found:
            return found[0]
        current = current.parent
    return None


def load_data_to_sqlite(
    parquet_path: Path, db_path: Path, batch_size: int = 50000
):
    print("=== ЗАГРУЗКА ДАННЫХ В SQLITE ===")

    # Определяем корень проекта
    current_dir = Path(__file__).resolve().parent
    root_dir = current_dir.parent if current_dir.name == "src" else current_dir

    if not parquet_path.is_absolute():
        parquet_path = root_dir / parquet_path
    if not db_path.is_absolute():
        db_path = root_dir / db_path

    if not parquet_path.exists():
        raise FileNotFoundError(f"Файл не найден: {parquet_path}")

    # Читаем очищенный датасет
    df = pd.read_parquet(parquet_path)
    print(f"Загружено из Parquet строк для переноса: {len(df)}")

    # Подключаемся к SQLite
    db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Автоматический поиск файла схемы schema_sqlite.sql по всему проекту
    schema_path = find_file_upwards("schema_sqlite.sql")

    if schema_path and schema_path.exists():
        with open(schema_path, "r", encoding="utf-8") as f:
            cursor.executescript(f.read())
        print(f"Схема базы данных успешно применена из: {schema_path}")
    else:
        raise FileNotFoundError(
            "Не удалось найти файл схемы 'schema_sqlite.sql' ни в одной из папок проекта!"
        )

    # Заполняем справочники статическими данными
    vendors_data = [(1, "Creative Mobile Technologies"), (2, "VeriFone")]
    cursor.executemany(
        "INSERT OR IGNORE INTO vendors (vendor_id, vendor_name) VALUES (?, ?);",
        vendors_data,
    )

    rate_codes_data = [
        (1, "Standard rate"),
        (2, "JFK"),
        (3, "Newark"),
        (4, "Nassau or Westchester"),
        (5, "Negotiated fare"),
        (6, "Group ride"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO rate_codes (rate_code_id, rate_name) VALUES (?, ?);",
        rate_codes_data,
    )

    payment_types_data = [
        (1, "Credit card"),
        (2, "Cash"),
        (3, "No charge"),
        (4, "Dispute"),
        (5, "Unknown"),
        (6, "Voided trip"),
    ]
    cursor.executemany(
        "INSERT OR IGNORE INTO payment_types (payment_type_id, payment_name) VALUES (?, ?);",
        payment_types_data,
    )
    conn.commit()

    # Пакетная загрузка таблицы trips с использованием time.time()
    print(
        f"Начало пакетной загрузки (размер пачки: {batch_size} строк)..."
    )
    start_time = time.time()

    cols_to_load = [
        "vendorid",
        "ratecodeid",
        "payment_type",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "fare_amount",
    ]

    df_subset = df[cols_to_load].copy()
    df_subset.columns = [
        "vendor_id",
        "rate_code_id",
        "payment_type_id",
        "tpep_pickup_datetime",
        "tpep_dropoff_datetime",
        "passenger_count",
        "trip_distance",
        "fare_amount",
    ]

    total_rows = len(df_subset)
    for i in range(0, total_rows, batch_size):
        batch = df_subset.iloc[i : i + batch_size]
        batch.to_sql("trips", conn, if_exists="append", index=False)
        print(
            f"Загружено пачек: {min(i + batch_size, total_rows)} / {total_rows} строк..."
        )

    duration = time.time() - start_time
    print(f"Загрузка завершена за {duration:.2f} секунд.")

    conn.close()


if __name__ == "__main__":
    load_data_to_sqlite(
        Path("data/processed/clean.parquet"), Path("data/sqlite/nyc_taxi.db")
    )