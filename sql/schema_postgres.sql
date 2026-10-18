CREATE TABLE IF NOT EXISTS vendors (
    vendor_id INT PRIMARY KEY,
    vendor_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS rate_codes (
    rate_code_id INT PRIMARY KEY,
    rate_code_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS payment_types (
    payment_type_id INT PRIMARY KEY,
    payment_type_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id SERIAL PRIMARY KEY,
    vendor_id INT,
    rate_code_id INT,
    payment_type_id INT,
    tpep_pickup_datetime TIMESTAMP,
    tpep_dropoff_datetime TIMESTAMP,
    passenger_count INT,
    trip_distance FLOAT,
    fare_amount FLOAT
);