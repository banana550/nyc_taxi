"""Сквозной пайплайн обработки данных с поддержкой CLI (argparse) и логирования в файл."""

import argparse
import logging
import sys
from pathlib import Path

import pandas as pd

# Добавляем корень проекта в путь поиска модулей
sys.path.append(str(Path(__file__).resolve().parent.parent))

from src.cleaning import (
    analyze_and_handle_nulls,
    clean_text_column,
    concatenate_sources,
    enforce_types,
    normalize_categories,
    normalize_column_names,
    remove_duplicates,
    remove_outliers_combined,
    reveal_hidden_nulls,
    scale_numeric_columns,
    validate_domain_rules,
)

# Настройка логирования в файл и консоль
log_dir = Path("logs")
log_dir.mkdir(exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    handlers=[
        logging.FileHandler(log_dir / "pipeline.log", encoding="utf-8"),
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("PipelineCLI")


def run_pipeline(
    input_path: Path, output_path: Path, mode: str = "full", stage: str | None = None
):
    """Основная функция запуска конвейера с обработкой ошибок."""
    logger.info(f"Запуск пайплайна. Режим: {mode}, Этап: {stage or 'все'}")

    try:
        # Проверка существования файла
        if not input_path.exists():
            raise FileNotFoundError(
                f"Входной файл не найден по пути: {input_path}"
            )

        # 1. Загрузка / Конкатенация
        if mode == "debug":
            logger.info("Отладочный режим: загрузка среза (первые 10 000 строк)")
            df = pd.read_csv(input_path, nrows=10000)
        else:
            df = concatenate_sources([input_path])

        if stage == "load":
            logger.info("Выполнен только этап загрузки.")
            return df

        # Последовательное применение этапов очистки
        df = normalize_column_names(df)
        if stage == "normalize_columns":
            return df

        df = enforce_types(df)
        if stage == "types":
            return df

        df = reveal_hidden_nulls(df)
        if stage == "hidden_nulls":
            return df

        df = analyze_and_handle_nulls(df)
        if stage == "nulls":
            return df

        df = remove_duplicates(df)
        if stage == "duplicates":
            return df

        df = normalize_categories(df)
        if stage == "categories":
            return df

        df = clean_text_column(df)
        if stage == "text":
            return df

        df = scale_numeric_columns(df)
        if stage == "scale":
            return df

        df = validate_domain_rules(df)
        if stage == "domain":
            return df

        df = remove_outliers_combined(df)
        if stage == "outliers":
            return df

        # Сохранение результата
        output_path.parent.mkdir(parents=True, exist_ok=True)
        df.to_parquet(output_path, compression="snappy", index=False)
        logger.info(f"Пайплайн успешно завершён. Результат сохранён в {output_path}")

    except FileNotFoundError as e:
        logger.error(f"Ошибка файла: {e}")
        sys.exit(1)
    except pd.errors.ParserError as e:
        logger.error(f"Ошибка формата CSV (поврежденная строка/структура): {e}")
        sys.exit(1)
    except Exception as e:  # noqa: BLE001
        logger.error(f"Непредвиденная ошибка в процессе выполнения: {e}")
        sys.exit(1)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Сквозной конвейер обработки данных NYC Taxi"
    )
    parser.add_argument(
        "--input",
        type=Path,
        default=Path("data/interim/sample_200k.csv"),
        help="Путь к исходному файлу",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=Path("data/processed/clean.parquet"),
        help="Путь к результирующему файлу",
    )
    parser.add_argument(
        "--mode",
        choices=["full", "debug"],
        default="full",
        help="Режим работы: полный или отладочный (срез)",
    )
    parser.add_argument(
        "--stage",
        type=str,
        default=None,
        help="Запуск отдельного этапа (load, normalize_columns, types, nulls, duplicates, outliers)",
    )

    args = parser.parse_args()
    run_pipeline(
        input_path=args.input,
        output_path=args.output,
        mode=args.mode,
        stage=args.stage,
    )