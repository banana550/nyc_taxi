from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_RAW = BASE_DIR / "data" / "raw"
DATA_INTERIM = BASE_DIR / "data" / "interim"
DATA_PROCESSED = BASE_DIR / "data" / "processed"



#Конфигурация типов данных для оптимизации памяти датасета NYC Taxi.

# Оптимизированная схема типов данных на основе предметной области
TAXI_DTYPES = {
    # Категориальные столбцы с малым числом уникальных значений
    "VendorID": "category",
    "RateCodeID": "category",
    "store_and_fwd_flag": "category",
    "payment_type": "category",
    # Малые целые числа (downcasting: uint8 от 0 до 255)
    "passenger_count": "uint8",
    # Дробные числа: точности float32 (4 байта) достаточно для GPS и цен
    "trip_distance": "float32",
    "pickup_longitude": "float32",
    "pickup_latitude": "float32",
    "dropoff_longitude": "float32",
    "dropoff_latitude": "float32",
    "fare_amount": "float32",
    "extra": "float32",
    "mta_tax": "float32",
    "tip_amount": "float32",
    "tolls_amount": "float32",
    "improvement_surcharge": "float32",
    "total_amount": "float32",
}

# Столбцы, приводимые к формату Datetime при чтении
DATE_COLUMNS = ["tpep_pickup_datetime", "tpep_dropoff_datetime"]