import pandas as pd
from statsmodels.tsa.seasonal import seasonal_decompose


def build_series(df: pd.DataFrame, date_col: str, freq: str = "W") -> pd.Series:
    """Сбор временного ряда с заполнением пустых периодов нулями через resample."""
    counts = df.set_index(date_col).resample(freq).size()
    return counts.rename("records")


def smooth_series(
    series: pd.Series, window: int = 4, alpha: float = 0.3
) -> pd.DataFrame:
    """Расчет скользящего среднего, медианы и экспоненциального сглаживания."""
    return pd.DataFrame(
        {
            "series": series,
            "rolling_mean": series.rolling(window, center=True).mean(),
            "rolling_median": series.rolling(window, center=True).median(),
            "ewm": series.ewm(alpha=alpha).mean(),
        }
    )


def find_outliers_and_breaks(series: pd.Series, period: int = 52):
    """Декомпозиция ряда, поиск выбросов по остатку и точек перелома."""
    # Декомпозиция (если длина ряда позволяет)
    decomposition = seasonal_decompose(series, model="additive", period=period)
    resid = decomposition.resid.dropna()

    # Поиск выбросов по робастному стандартному отклонению (MAD * 1.4826)
    med_resid = resid.median()
    spread = 1.4826 * (resid - med_resid).abs().median()
    outliers = resid[(resid - med_resid).abs() > 3 * spread]

    return decomposition, outliers
