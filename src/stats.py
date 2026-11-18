import numpy as np
import pandas as pd


def calc_distribution_stats(series: pd.Series) -> dict:
    """Считает среднее, медиану и коэффициент асимметрии до и после log1p."""
    clean_s = series.dropna().astype("float64")
    log_s = np.log1p(clean_s)

    return {
        "mean": float(clean_s.mean()),
        "median": float(clean_s.median()),
        "skew_raw": float(clean_s.skew()),
        "skew_log1p": float(log_s.skew()),
    }


def bootstrap_median(values, n_boot: int = 2000, seed: int = 42) -> tuple[float, float]:
    """Оценивает 95% доверительный интервал медианы методом бутстрапа."""
    rng = np.random.default_rng(seed)
    arr = np.asarray(values, dtype="float64")
    arr = arr[~np.isnan(arr)]

    # Если набор огромный (> 200 тыс. строк), берем случайную подвыборку для быстрого расчёта
    if len(arr) > 200_000:
        arr = rng.choice(arr, size=200_000, replace=False)

    medians = np.empty(n_boot, dtype="float64")
    n = len(arr)
    for i in range(n_boot):
        sample = rng.choice(arr, size=n, replace=True)
        medians[i] = np.median(sample)

    low, high = np.percentile(medians, [2.5, 97.5])
    return float(low), float(high)


## ----------------------------------- ##
from scipy.stats import kruskal, mannwhitneyu
from statsmodels.stats.multitest import multipletests
from statsmodels.stats.proportion import proportions_ztest


def test_two_groups_mw(
    group_a: pd.Series, group_b: pd.Series, n_boot: int = 500, seed: int = 42
) -> dict:
    """Тест Манна-Уитни и бутстрап-оценка разности медиан двух групп."""
    a = group_a.dropna().to_numpy(dtype="float64")
    b = group_b.dropna().to_numpy(dtype="float64")

    _, p_val = mannwhitneyu(a, b, alternative="two-sided")
    med_diff = float(np.median(a) - np.median(b))

    # Бутстрап разности медиан на подвыборках для скорости
    rng = np.random.default_rng(seed)
    a_sub = rng.choice(a, size=min(100_000, len(a)), replace=False)
    b_sub = rng.choice(b, size=min(100_000, len(b)), replace=False)
    diffs = np.empty(n_boot, dtype="float64")
    for i in range(n_boot):
        s_a = rng.choice(a_sub, size=len(a_sub), replace=True)
        s_b = rng.choice(b_sub, size=len(b_sub), replace=True)
        diffs[i] = np.median(s_a) - np.median(s_b)
    ci_low, ci_high = np.percentile(diffs, [2.5, 97.5])

    return {
        "p_value": float(p_val),
        "median_a": float(np.median(a)),
        "median_b": float(np.median(b)),
        "diff": med_diff,
        "ci_low": float(ci_low),
        "ci_high": float(ci_high),
    }


def test_multigroup_kw(df: pd.DataFrame, group_col: str, target_col: str) -> dict:
    """Тест Краскела-Уоллиса и попарные тесты Манна-Уитни с поправкой Холма."""
    groups = {
        name: part[target_col].dropna().to_numpy(dtype="float64")
        for name, part in df.groupby(group_col, observed=False)
    }
    _, kw_pval = kruskal(*groups.values())

    names = list(groups.keys())
    pairs = [(a, b) for i, a in enumerate(names) for b in names[i + 1 :]]
    raw_pvals = [
        mannwhitneyu(groups[a], groups[b], alternative="two-sided").pvalue
        for a, b in pairs
    ]
    reject, adjusted_pvals, _, _ = multipletests(raw_pvals, alpha=0.05, method="holm")

    medians = {k: float(np.median(v)) for k, v in groups.items()}
    max_diff = max(medians.values()) - min(medians.values())

    return {
        "kw_pvalue": float(kw_pval),
        "n_pairs": len(pairs),
        "n_significant": int(reject.sum()),
        "max_median_diff": float(max_diff),
        "medians": medians,
        "adjusted_pvals": list(zip(pairs, adjusted_pvals, reject)),
    }


def test_two_proportions(count_a: int, n_a: int, count_b: int, n_b: int) -> dict:
    """z-тест для двух долей и разница в процентных пунктах."""
    _, p_val = proportions_ztest([count_a, count_b], [n_a, n_b])
    share_a = count_a / n_a
    share_b = count_b / n_b
    diff_pp = (share_a - share_b) * 100.0

    return {
        "p_value": float(p_val),
        "share_a_pct": float(share_a * 100.0),
        "share_b_pct": float(share_b * 100.0),
        "diff_pp": float(diff_pp),
    }


## -------------------------------------------------------- ##
def compute_correlation_matrices(df: pd.DataFrame, numeric_cols: list) -> dict:
    """Вычисление матриц Пирсона и Спирмена, а также поиск наибольшего расхождения."""
    sub_df = df[numeric_cols].dropna()

    corr_pearson = sub_df.corr(method="pearson")
    corr_spearman = sub_df.corr(method="spearman")

    # Разность матриц в абсолютном выражении
    diff_matrix = (corr_pearson - corr_spearman).abs()

    # Создаем полностью независимый массив и обнуляем диагональ через маску, без fill_diagonal
    vals = diff_matrix.to_numpy(copy=True)
    np.fill_diagonal(vals, -1.0)  # теперь это точно безопасная копия

    row_idx, col_idx = np.unravel_index(vals.argmax(), vals.shape)
    pair = (diff_matrix.index[row_idx], diff_matrix.columns[col_idx])

    p_val = corr_pearson.loc[pair[0], pair[1]]
    s_val = corr_spearman.loc[pair[0], pair[1]]

    return {
        "pearson": corr_pearson,
        "spearman": corr_spearman,
        "diff": diff_matrix,
        "max_pair": pair,
        "pearson_val": float(p_val),
        "spearman_val": float(s_val),
    }


def check_simpson_paradox(
    df: pd.DataFrame, flag_col: str, target_col: str, group_col: str
) -> dict:
    """Проверка на парадокс Симпсона по методике подраздела 2.3 (разность медиан)."""
    overall = df.groupby(flag_col, observed=False)[target_col].median()
    overall_diff = float(overall[True] - overall[False])

    inside = (
        df.groupby([group_col, flag_col], observed=False)[target_col].median().unstack()
    )
    group_diffs = (inside[True] - inside[False]).sort_values()

    return {
        "overall_medians": overall,
        "overall_diff": overall_diff,
        "inside_medians": inside,
        "group_diffs": group_diffs,
    }
