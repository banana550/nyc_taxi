import time

import numpy as np
import pandas as pd


def calc_group_aggregates(
    df: pd.DataFrame, group_col: str, target_col: str
) -> pd.DataFrame:
    """Быстрый расчет агрегатов по группам с использованием встроенных оптимизированных методов."""

    # Считаем количество, медиану и среднее за один проход через agg (добавили observed=False)
    agg_df = df.groupby(group_col, dropna=False, observed=False).agg(
        count=(target_col, "count"),
        median=(target_col, "median"),
        mean=(target_col, "mean"),
    )

    # Долю пропусков считаем быстро через общую длину группы и количество непустых (count) (добавили observed=False)
    total_rows = df.groupby(group_col, dropna=False, observed=False).size()
    agg_df["missing_share"] = 1.0 - (agg_df["count"] / total_rows)

    return agg_df.reset_index()


def detect_anomalies_iqr(series: pd.Series, multiplier: float = 1.5):
    """Первое правило: межквартильный размах (IQR)."""
    q1 = series.quantile(0.25)
    q3 = series.quantile(0.75)
    iqr = q3 - q1
    lower_bound = q1 - multiplier * iqr
    upper_bound = q3 + multiplier * iqr

    # Маска: True, если значение является выбросом
    mask = (series < lower_bound) | (series > upper_bound)
    return mask, int(mask.sum())


def detect_anomalies_domain(series: pd.Series):
    """Второе правило: предметное ограничение (fare_amount <= 0 или > 300)."""
    mask = (series <= 0) | (series > 300)
    return mask, int(mask.sum())


def mean_loop(values):
    """Вычисление среднего циклом Python."""
    total = 0.0
    count = 0
    for value in values:
        if value == value:  # отсекаем NaN  # noqa: PLR0124
            total += float(value)
            count += 1
    return total / count


def mean_numpy(values):
    """Вычисление среднего средствами NumPy."""
    array = np.asarray(values, dtype="float64")
    return float(np.nanmean(array))


def median_seconds(func, values):
    """Замер времени: 1 прогревочный прогон + 3 повтора, возвращает медиану."""
    func(values)  # разогрев кэша
    marks = []
    for _ in range(3):
        started = time.perf_counter()
        func(values)
        marks.append(time.perf_counter() - started)
    marks.sort()
    return marks[1]  # медиана из трех замеров
