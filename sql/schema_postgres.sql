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
    payment_name VARCHAR(100)
);

CREATE TABLE IF NOT EXISTS trips (
    trip_id SERIAL PRIMARY KEY,
    vendor_id INT REFERENCES vendors(vendor_id),
    rate_code_id INT REFERENCES rate_codes(rate_code_id),
    payment_type_id INT REFERENCES payment_types(payment_type_id),
    tpep_pickup_datetime TIMESTAMP,
    tpep_dropoff_datetime TIMESTAMP,
    passenger_count INT,
    trip_distance FLOAT,
    fare_amount FLOAT
);

INSERT INTO vendors (vendor_id, vendor_name) VALUES 
(1, 'Creative Mobile Technologies, LLC'),
(2, 'VeriFone Inc.')
ON CONFLICT (vendor_id) DO NOTHING;

INSERT INTO rate_codes (rate_code_id, rate_code_name) VALUES 
(1, 'Standard rate'),
(2, 'JFK'),
(3, 'Newark'),
(4, 'Nassau or Westchester'),
(5, 'Negotiated fare'),
(6, 'Group ride'),
(99, 'Unknown / Other')
ON CONFLICT (rate_code_id) DO NOTHING;

INSERT INTO payment_types (payment_type_id, payment_name) VALUES 
(1, 'Credit card'),
(2, 'Cash'),
(3, 'No charge'),
(4, 'Dispute'),
(5, 'Unknown'),
(6, 'Voided trip')
ON CONFLICT (payment_type_id) DO NOTHING;