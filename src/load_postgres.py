"""Загрузка данных в PostgreSQL с замером времени (Batch vs COPY) через psycopg (v3)."""

import time
from pathlib import Path

import pandas as pd
import psycopg


def get_connection():
    return psycopg.connect(
        host="127.0.0.1",
        port=5432,
        dbname="nyc_taxi",
        user="postgres",
        password="secret",
    )


def load_postgres(parquet_path: Path, method: str = "copy"):
    print(f"=== ЗАГРУЗКА В POSTGRESQL (Метод: {method.upper()}) ===")

    if not parquet_path.exists():
        raise FileNotFoundError(f"Файл не найден: {parquet_path}")

    df = pd.read_parquet(parquet_path)
    print(f"Загружено из Parquet строк: {len(df)}")

    root_dir = Path(__file__).resolve().parent.parent
    schema_path = root_dir / "sql" / "schema_postgres.sql"

    if not schema_path.exists():
        raise FileNotFoundError(f"Файл схемы не найден: {schema_path}")

    with get_connection() as conn:
        # Выполняем создание таблиц через соединение
        with open(schema_path, "r", encoding="utf-8") as f:
            conn.execute(f.read())
        conn.commit()

        # Открываем курсор для вставки справочников и данных
        with conn.cursor() as cursor:
            cursor.execute(
                "INSERT INTO vendors VALUES (1, 'Creative Mobile Technologies'), (2, 'VeriFone') ON CONFLICT DO NOTHING;"
            )
            cursor.execute("""
                INSERT INTO rate_codes VALUES 
                (1, 'Standard rate'), (2, 'JFK'), (3, 'Newark'), 
                (4, 'Nassau or Westchester'), (5, 'Negotiated fare'), (6, 'Group ride') 
                ON CONFLICT DO NOTHING;
            """)
            cursor.execute("""
                INSERT INTO payment_types VALUES 
                (1, 'Credit card'), (2, 'Cash'), (3, 'No charge'), 
                (4, 'Dispute'), (5, 'Unknown'), (6, 'Voided trip') 
                ON CONFLICT DO NOTHING;
            """)
            conn.commit()

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
            df_sub = df[cols_to_load].copy()
            df_sub.columns = [
                "vendor_id",
                "rate_code_id",
                "payment_type_id",
                "tpep_pickup_datetime",
                "tpep_dropoff_datetime",
                "passenger_count",
                "trip_distance",
                "fare_amount",
            ]

            start_time = time.time()

            if method == "copy":
                query = "COPY trips(vendor_id, rate_code_id, payment_type_id, tpep_pickup_datetime, tpep_dropoff_datetime, passenger_count, trip_distance, fare_amount) FROM STDIN"
                
                with cursor.copy(query) as copyp:
                    for row in df_sub.itertuples(index=False, name=None):
                        copyp.write_row(row)
                        
                conn.commit()

            duration = time.time() - start_time
            print(f"Загрузка через {method.upper()} завершена за {duration:.2f} секунд.")


if __name__ == "__main__":
    load_postgres(Path("data/processed/clean.parquet"), method="batch")