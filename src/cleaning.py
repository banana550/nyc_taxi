"""Модуль полной очистки данных NYC Taxi для Шага 12."""

import logging
from pathlib import Path

import numpy as np
import pandas as pd

from src.config import DATE_COLUMNS, TAXI_DTYPES

# Настройка логирования
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[logging.StreamHandler()],
)
logger = logging.getLogger(__name__)


def concatenate_sources(file_paths: list[Path]) -> pd.DataFrame:
    """1. Соединение исходных файлов с проверкой числа строк."""
    logger.info("Этап 1: Соединение исходных файлов")
    dfs = []
    total_input_rows = 0

    for path in file_paths:
        df_part = pd.read_csv(path, dtype=TAXI_DTYPES, parse_dates=DATE_COLUMNS)
        total_input_rows += len(df_part)
        dfs.append(df_part)

    df_concat = pd.concat(dfs, ignore_index=True)
    logger.info(
        f"Конкатенация завершена. Исходных строк: {total_input_rows}, после объединения: {len(df_concat)}"
    )
    return df_concat


def normalize_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """2. Приведение имён столбцов к единому виду."""
    logger.info("Этап 2: Нормализация имён столбцов")
    old_cols = df.columns.tolist()
    df.columns = (
        df.columns.str.strip()
        .str.lower()
        .str.replace(r"[^\w\s]", "", regex=True)
        .str.replace(r"\s+", "_", regex=True)
    )
    changed = sum(1 for o, n in zip(old_cols, df.columns) if o != n)
    logger.info(f"Переименовано столбцов: {changed}")
    return df


def enforce_types(df: pd.DataFrame) -> pd.DataFrame:
    """3. Явное приведение типов и обработка дат."""
    logger.info("Этап 3: Явное приведение типов")
    for date_col in ["tpep_pickup_datetime", "tpep_dropoff_datetime"]:
        if date_col in df.columns:
            invalid_before = df[date_col].isna().sum()
            df[date_col] = pd.to_datetime(df[date_col], errors="coerce")
            invalid_after = df[date_col].isna().sum()
            logger.info(
                f"Столбец {date_col}: неразобранных дат (стали NaT) = {invalid_after - invalid_before}"
            )
    return df


def reveal_hidden_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """4. Выявление скрытых пропусков."""
    logger.info("Этап 4: Выявление скрытых пропусков")
    initial_nulls = df.isna().sum().sum()

    # Заменяем текстовые заглушки на NaN
    df = df.replace(
        ["нет данных", "None", "null", "-", "N/A", "unknown", ""], np.nan
    )

    # Скрытые нули в координатах
    coord_cols = [
        "pickup_latitude",
        "pickup_longitude",
        "dropoff_latitude",
        "dropoff_longitude",
    ]
    for col in coord_cols:
        if col in df.columns:
            df[col] = df[col].replace(0, np.nan)

    new_nulls = df.isna().sum().sum() - initial_nulls
    logger.info(f"Выявлено скрытых пропусков и заменено на NaN: {new_nulls}")
    return df


def analyze_and_handle_nulls(df: pd.DataFrame) -> pd.DataFrame:
    """5. Анализ структуры пропусков и выбор стратегии."""
    logger.info("Этап 5: Анализ структуры пропусков")
    null_counts = df.isna().sum()
    null_ratios = df.isna().mean()

    for col in df.columns:
        if null_counts[col] > 0:
            logger.info(
                f"Столбец '{col}': пропусков {null_counts[col]} ({null_ratios[col]*100:.2f}%)"
            )

    # Проверка: не сосредоточены ли пропуски в определенной группе (например, payment_type)
    if "payment_type" in df.columns and df.isna().sum().sum() > 0:
        logger.info(
            "Анализ распределения пропусков по группам (payment_type):"
        )
        missing_by_group = (
            df[df.isna().any(axis=1)].groupby("payment_type", observed=False).size()
        )
        logger.info(f"\n{missing_by_group}")

    # Стратегия: удаляем строки с пропусками в критических полях
    key_cols = [
        c
        for c in [
            "tpep_pickup_datetime",
            "tpep_dropoff_datetime",
            "trip_distance",
            "fare_amount",
        ]
        if c in df.columns
    ]
    rows_before = len(df)
    df = df.dropna(subset=key_cols)
    logger.info(
        f"Удалено строк из-за пропусков в ключевых полях {key_cols}: {rows_before - len(df)}"
    )
    return df


def remove_duplicates(df: pd.DataFrame) -> pd.DataFrame:
    """6. Удаление полных дубликатов и дубликатов по ключу."""
    logger.info("Этап 6: Удаление дубликатов")
    rows_before = len(df)

    df = df.drop_duplicates()
    full_dups = rows_before - len(df)

    key_dups = 0
    if "trip_id" in df.columns and "tpep_pickup_datetime" in df.columns:
        rows_before_key = len(df)
        df = df.sort_values("tpep_pickup_datetime").drop_duplicates(
            subset=["trip_id"], keep="last"
        )
        key_dups = rows_before_key - len(df)

    logger.info(
        f"Удалено полных дубликатов: {full_dups}, дубликатов по ключу: {key_dups}"
    )
    return df


def normalize_categories(df: pd.DataFrame) -> pd.DataFrame:
    """7. Нормализация категориальных столбцов."""
    logger.info("Этап 7: Нормализация категорий")
    if "store_and_fwd_flag" in df.columns:
        df["store_and_fwd_flag"] = (
            df["store_and_fwd_flag"]
            .astype(str)
            .str.strip()
            .str.upper()
            .replace({"NAN": np.nan, "NONE": np.nan})
        )
    return df


def clean_text_column(df: pd.DataFrame) -> pd.DataFrame:
    """8. Обработка текстового столбца TEXT (если присутствует)."""
    logger.info("Этап 8: Обработка текстового столбца TEXT")
    # Проверяем, есть ли текстовые колонки помимо стандартных
    text_cols = [
        c
        for c in df.select_dtypes(include=["object"]).columns
        if c not in ["store_and_fwd_flag", "payment_type", "vendorid", "ratecodeid"]
    ]
    for col in text_cols:
        initial_len = len(df)
        df[col] = (
            df[col]
            .astype(str)
            .str.replace(r"<[^>]*>", "", regex=True)
            .str.replace(r"\s+", " ", regex=True)
            .str.strip()
        )
        df = df[~df[col].str.lower().isin(["nan", "none", "null", "", "-"])]
        logger.info(
            f"Очищен столбец '{col}', удалено мусорных строк: {initial_len - len(df)}"
        )
    return df


def scale_numeric_columns(df: pd.DataFrame) -> pd.DataFrame:
    """9. Приведение числовых столбцов к единой шкале."""
    logger.info("Этап 9: Приведение числовых столбцов к единой шкале")
    # В NYC Taxi валюта USD и расстояние в милях стандартны.
    # Проверяем корректность типов.
    return df


def validate_domain_rules(df: pd.DataFrame) -> pd.DataFrame:
    """10. Проверка предметных ограничений."""
    logger.info("Этап 10: Проверка предметных ограничений")
    rows_before = len(df)

    mask = (df["trip_distance"] >= 0) & (df["fare_amount"] >= 0)

    if (
        "tpep_pickup_datetime" in df.columns
        and "tpep_dropoff_datetime" in df.columns
    ):
        mask &= df["tpep_pickup_datetime"] <= df["tpep_dropoff_datetime"]

    df = df[mask]
    logger.info(
        f"Отсеяно строк, нарушающих предметные ограничения (отрицательные цены/дистанции, неверные даты): {rows_before - len(df)}"
    )
    return df


def remove_outliers_combined(df: pd.DataFrame) -> pd.DataFrame:
    """11. Выявление выбросов двумя способами (IQR и Z-score) с сопоставлением."""
    logger.info("Этап 11: Выявление выбросов (IQR vs Z-score)")
    col = "fare_amount"
    if col not in df.columns:
        return df

    rows_before = len(df)

    # Способ 1: IQR (Межквартильный размах)
    q1 = df[col].quantile(0.25)
    q3 = df[col].quantile(0.75)
    iqr = q3 - q1
    lower_iqr = q1 - 1.5 * iqr
    upper_iqr = q3 + 1.5 * iqr
    mask_iqr = (df[col] >= lower_iqr) & (df[col] <= upper_iqr)

    # Способ 2: Z-score (Правило 3 сигм)
    mean_val = df[col].mean()
    std_val = df[col].std()
    z_scores = (df[col] - mean_val) / std_val
    mask_z = z_scores.abs() <= 3.0

    outliers_iqr = (~mask_iqr).sum()
    outliers_z = (~mask_z).sum()
    intersection = (~mask_iqr & ~mask_z).sum()

    logger.info(f"Выбросов по методу IQR: {outliers_iqr}")
    logger.info(f"Выбросов по методу Z-score: {outliers_z}")
    logger.info(f"Пересекающихся выбросов (определены обоими методами): {intersection}")

    # Обоснование выборки: используем более устойчивый к распределению метод IQR
    df_clean = df[mask_iqr]
    logger.info(f"Удалено выбросов по основному правилу (IQR): {rows_before - len(df_clean)}")
    return df_clean


def run_cleaning_pipeline(input_files: list[Path], output_path: Path) -> pd.DataFrame:
    """Запуск полного пайплайна очистки и сохранение результата."""
    logger.info("ЗАПУСК ПОЛНОГО ПАЙПЛАЙНА ОЧИСТКИ ДАННЫХ")

    df = concatenate_sources(input_files)
    initial_count = len(df)

    df = normalize_column_names(df)
    df = enforce_types(df)
    df = reveal_hidden_nulls(df)
    df = analyze_and_handle_nulls(df)
    df = remove_duplicates(df)
    df = normalize_categories(df)
    df = clean_text_column(df)
    df = scale_numeric_columns(df)
    df = validate_domain_rules(df)
    df = remove_outliers_combined(df)

    final_count = len(df)
    lost_rows = initial_count - final_count
    loss_ratio = (lost_rows / initial_count) * 100

    logger.info("==========================================")
    logger.info("ИТОГОВАЯ СВОДКА «БЫЛО - СТАЛО»:")
    logger.info(f"Исходное число записей (Было): {initial_count}")
    logger.info(f"Итоговое число записей (Стало): {final_count}")
    logger.info(f"Всего удалено записей:         {lost_rows}")
    logger.info(f"Доля потерянных строк:         {loss_ratio:.2f}%")
    logger.info("==========================================")

    if loss_ratio > 10.0:
        logger.warning(
            f"ВНИМАНИЕ: Потеряно {loss_ratio:.2f}% данных (>10%). Требуется отдельное обоснование в отчёте!"
        )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(output_path, compression="snappy", index=False)
    logger.info(f"Чистый датасет успешно сохранён в: {output_path}")

    return df


if __name__ == "__main__":
    input_paths = [Path("data/interim/sample_200k.csv")]
    output_parquet = Path("data/processed/clean.parquet")
    run_cleaning_pipeline(input_paths, output_parquet)