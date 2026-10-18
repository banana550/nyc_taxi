-- Схема базы данных SQLite в третьей нормальной форме (3НФ) для NYC Taxi

DROP TABLE IF EXISTS trips;
DROP TABLE IF EXISTS payment_types;
DROP TABLE IF EXISTS rate_codes;
DROP TABLE IF EXISTS vendors;

-- 1. Справочник вендоров
CREATE TABLE vendors (
    vendor_id INTEGER PRIMARY KEY,
    vendor_name TEXT
);

-- 2. Справочник тарифных кодов
CREATE TABLE rate_codes (
    rate_code_id INTEGER PRIMARY KEY,
    rate_name TEXT
);

-- 3. Справочник типов оплаты
CREATE TABLE payment_types (
    payment_type_id INTEGER PRIMARY KEY,
    payment_name TEXT
);

-- 4. Основная таблица фактов поездок
CREATE TABLE trips (
    trip_id INTEGER PRIMARY KEY AUTOINCREMENT,
    vendor_id INTEGER,
    rate_code_id INTEGER,
    payment_type_id INTEGER,
    tpep_pickup_datetime TEXT NOT NULL,
    tpep_dropoff_datetime TEXT NOT NULL,
    passenger_count INTEGER,
    trip_distance REAL,
    fare_amount REAL,
    FOREIGN KEY (vendor_id) REFERENCES vendors(vendor_id),
    FOREIGN KEY (rate_code_id) REFERENCES rate_codes(rate_code_id),
    FOREIGN KEY (payment_type_id) REFERENCES payment_types(payment_type_id)
);