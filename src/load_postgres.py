import time
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text

print("ТЕСТИРОВАНИЕ И ЗАГРУЗКА В POSTGRESQL")

# Читаем подготовленные данные
parquet_path = Path("data/processed/clean.parquet")
if not parquet_path.exists():
    raise FileNotFoundError(f"Файл не найден: {parquet_path}")

df = pd.read_parquet(parquet_path)

# Отбираем и переименовываем нужные колонки под схему
cols_to_load = [
    "vendorid", "ratecodeid", "payment_type",
    "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "fare_amount"
]
df_sub = df[cols_to_load].copy()
df_sub.columns = [
    "vendor_id", "rate_code_id", "payment_type_id",
    "tpep_pickup_datetime", "tpep_dropoff_datetime",
    "passenger_count", "trip_distance", "fare_amount"
]

# Приводим ID к целым числам
for col in ["vendor_id", "rate_code_id", "payment_type_id"]:
    df_sub[col] = pd.to_numeric(df_sub[col], errors="coerce").fillna(0).astype(int)

# Подключение к PostgreSQL
engine = create_engine("postgresql+psycopg://postgres:secret@127.0.0.1:5432/nyc_taxi")
schema_sql = Path("sql/schema_postgres.sql").read_text(encoding="utf-8")

# Пересоздаем чистую таблицу перед загрузкой
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS trips CASCADE;"))
    conn.execute(text(schema_sql))

# 1. Замер времени загрузки (пакетная вставка)
start_time = time.time()
df_sub.to_sql("trips", engine, if_exists="append", index=False, chunksize=50000)
load_time = time.time() - start_time
print(f"Время загрузки: {load_time:.2f} сек.")

# 2. Измеряем объем хранилища базы данных в МБ
with engine.connect() as conn:
    size_bytes = conn.execute(text("SELECT pg_database_size('nyc_taxi');")).scalar()
    size_mb = size_bytes / (1024 * 1024)
print(f"Объём хранилища: {size_mb:.2f} МБ")

# 3. Запрос с агрегированием
start_time = time.time()
with engine.begin() as conn:
    conn.execute(text("SELECT payment_type_id, AVG(fare_amount), COUNT(*) FROM trips GROUP BY payment_type_id;"))
agg_time = time.time() - start_time
print(f"Запрос с агрегированием: {agg_time:.4f} сек.")

# 4. Выборка по диапазону дат БЕЗ индекса
with engine.begin() as conn:
    conn.execute(text("DROP INDEX IF EXISTS idx_pickup_time;"))

query_date = "SELECT * FROM trips WHERE tpep_pickup_datetime BETWEEN '2015-01-01 00:00:00' AND '2015-01-07 23:59:59';"

start_time = time.time()
with engine.begin() as conn:
    conn.execute(text(query_date))
no_idx_time = time.time() - start_time
print(f"Выборка без индекса: {no_idx_time:.4f} сек.")

# 5. Выборка по диапазону дат С индексом
with engine.begin() as conn:
    conn.execute(text("CREATE INDEX idx_pickup_time ON trips(tpep_pickup_datetime);"))

start_time = time.time()
with engine.begin() as conn:
    conn.execute(text(query_date))
with_idx_time = time.time() - start_time
print(f"Выборка с индексом: {with_idx_time:.4f} сек.")