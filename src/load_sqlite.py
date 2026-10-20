import sqlite3
import time
from pathlib import Path

import pandas as pd

print("ТЕСТИРОВАНИЕ И ЗАГРУЗКА В SQLITE")

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

# Настройка базы данных
db_path = Path("sql/database.db")
db_path.parent.mkdir(parents=True, exist_ok=True)
if db_path.exists():
    db_path.unlink() # Очищаем старую базу для честного замера

conn = sqlite3.connect(db_path)
schema_sql = Path("sql/schema_sqlite.sql").read_text(encoding="utf-8")
conn.executescript(schema_sql)

# 1. Замер времени загрузки
start_time = time.time()
df_sub.to_sql("trips", conn, if_exists="append", index=False, chunksize=50000)
load_time = time.time() - start_time
print(f"Время загрузки: {load_time:.2f} сек.")

# 2. Измеряем объем хранилища (файла на диске) в МБ
size_mb = db_path.stat().st_size / (1024 * 1024)
print(f"Объём хранилища: {size_mb:.2f} МБ")

# 3. Запрос с агрегированием
cursor = conn.cursor()
start_time = time.time()
cursor.execute("SELECT payment_type_id, AVG(fare_amount), COUNT(*) FROM trips GROUP BY payment_type_id;")
cursor.fetchall()
agg_time = time.time() - start_time
print(f"Запрос с агрегированием: {agg_time:.4f} сек.")

# 4. Выборка по диапазону дат БЕЗ индекса
cursor.execute("DROP INDEX IF EXISTS idx_pickup_time;")
query_date = "SELECT * FROM trips WHERE tpep_pickup_datetime BETWEEN '2015-01-01 00:00:00' AND '2015-01-07 23:59:59';"

start_time = time.time()
cursor.execute(query_date)
cursor.fetchall()
no_idx_time = time.time() - start_time
print(f"Выборка без индекса: {no_idx_time:.4f} сек.")

# 5. Выборка по диапазону дат С индексом
cursor.execute("CREATE INDEX idx_pickup_time ON trips(tpep_pickup_datetime);")
start_time = time.time()
cursor.execute(query_date)
cursor.fetchall()
with_idx_time = time.time() - start_time
print(f"Выборка с индексом: {with_idx_time:.4f} сек.")

conn.close()