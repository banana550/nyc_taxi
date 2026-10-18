from pathlib import Path

import polars as pl

RAW_DIR = Path("data/raw")
INTERIM_DIR = Path("data/interim")

input_file = RAW_DIR / "yellow_tripdata_2015-01.csv"
output_file = INTERIM_DIR / "sample_200k.csv"

INTERIM_DIR.mkdir(parents=True, exist_ok=True)

print(f"Чтение файла {input_file}...")
df = pl.read_csv(input_file, n_rows=200_000)

df.write_csv(output_file)
print(f"Срез сохранен в {output_file}")
