"""Выполнение контрольных запросов и замер производительности до/после индексов."""

import sqlite3
import time
from pathlib import Path


def run_queries(db_path: Path, phase_name: str):
    print(f"\n ВЫПОЛНЕНИЕ КОНТРОЛЬНЫХ ЗАПРОСОВ ({phase_name}) ")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    queries = {
        "1. Подсчет общего числа записей": "SELECT COUNT(*) FROM trips;",
        "2. Агрегация по типу оплаты (средний fare)": """
            SELECT PT.payment_name, AVG(T.fare_amount), COUNT(*) 
            FROM trips T JOIN payment_types PT ON T.payment_type_id = PT.payment_type_id 
            GROUP BY PT.payment_name;
        """,
        "3. Выборка по диапазону дат": """
            SELECT COUNT(*) FROM trips 
            WHERE tpep_pickup_datetime BETWEEN '2016-01-01 00:00:00' AND '2016-01-07 23:59:59';
        """,
    }

    for name, query in queries.items():
        start = time.time()  # <--- Вызываем без аргументов!
        cursor.execute(query)
        cursor.fetchall()
        duration = time.time() - start
        print(f"  [{name}] Время выполнения: {duration:.4f} сек.")

    conn.close()


def create_indexes(db_path: Path):
    print("\n СОЗДАНИЕ ИНДЕКСОВ")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE INDEX IF NOT EXISTS idx_trips_pickup_date ON trips(tpep_pickup_datetime);
        CREATE INDEX IF NOT EXISTS idx_trips_payment ON trips(payment_type_id);
    """)
    conn.commit()
    conn.close()
    print("Индексы успешно созданы.")


if __name__ == "__main__":
    db_file = Path("data/sqlite/nyc_taxi.db")

    # 1. Запросы ДО создания индексов
    run_queries(db_file, "ДО ИНДЕКСАЦИИ")

    # 2. Создание индексов
    create_indexes(db_file)

    # 3. Запросы ПОСЛЕ создания индексов
    run_queries(db_file, "ПОСЛЕ ИНДЕКСАЦИИ")