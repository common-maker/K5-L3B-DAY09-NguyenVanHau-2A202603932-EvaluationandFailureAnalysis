"""Statistics students implement (M2 judge calibration, M4 paired bootstrap).

Rules: a judge is a classifier -- measure it like one. A higher mean is not
"better" until the paired CI of the difference excludes 0.
Reference values to self-check are in tests/test_lab9_stats.py.
"""

from __future__ import annotations

import math
from collections.abc import Sequence

import numpy as np
from scipy.stats import bootstrap

POS = "FAIL"   # the judge's job is to FIND failures, so FAIL is the positive class


def confusion(human: Sequence[str], judge: Sequence[str]) -> dict[str, int]:
    """tp/fp/fn/tn with FAIL as positive."""
    if len(human) != len(judge):
        raise ValueError(f"length mismatch: human={len(human)} vs judge={len(judge)}")
    tp = fp = fn = tn = 0
    for h, j in zip(human, judge):
        h_pos = str(h).strip().upper() == POS
        j_pos = str(j).strip().upper() == POS
        if h_pos and j_pos:
            tp += 1
        elif not h_pos and j_pos:
            fp += 1
        elif h_pos and not j_pos:
            fn += 1
        else:
            tn += 1
    return {"tp": tp, "fp": fp, "fn": fn, "tn": tn}


def precision_recall(human: Sequence[str], judge: Sequence[str]) -> tuple[float, float]:
    cm = confusion(human, judge)
    p_den = cm["tp"] + cm["fp"]
    r_den = cm["tp"] + cm["fn"]
    precision = cm["tp"] / p_den if p_den else 0.0
    recall = cm["tp"] / r_den if r_den else 0.0
    return (precision, recall)


def cohen_kappa(human: Sequence[str], judge: Sequence[str]) -> float:
    """kappa = (p_o - p_e) / (1 - p_e). Raise ValueError when undefined (p_e == 1):
    a constant judge has no signal and must FAIL calibration, not pass on a technicality."""
    cm = confusion(human, judge)
    n = len(human)
    if n == 0:
        raise ValueError("cannot compute kappa on empty sequences")
    p_o = (cm["tp"] + cm["tn"]) / n
    p_pos_h = (cm["tp"] + cm["fn"]) / n
    p_pos_j = (cm["tp"] + cm["fp"]) / n
    p_neg_h = (cm["fp"] + cm["tn"]) / n
    p_neg_j = (cm["fn"] + cm["tn"]) / n
    p_e = p_pos_h * p_pos_j + p_neg_h * p_neg_j
    if p_e >= 1.0 or math.isclose(p_e, 1.0, abs_tol=1e-12):
        raise ValueError("Cohen's kappa is undefined when p_e == 1")
    return (p_o - p_e) / (1.0 - p_e)


def rogan_gladen(observed_rate: float, sensitivity: float, specificity: float) -> float:
    """Correct an observed failure rate for judge error; clip to [0, 1]."""
    denom = sensitivity + specificity - 1.0
    if denom <= 0.0 or math.isclose(denom, 0.0, abs_tol=1e-12):
        return 0.0
    est = (observed_rate + specificity - 1.0) / denom
    return min(1.0, max(0.0, est))


def paired_bootstrap(a: Sequence[float], b: Sequence[float], *, n_resamples: int = 1000,
                     rng: int = 2027, confidence: float = 0.95) -> tuple[float, float, float]:
    """a[i], b[i] = per-item mean over seeds, SAME items, SAME order.
    Return (mean(a)-mean(b), lo, hi) with scipy.stats.bootstrap(paired=True, method="percentile",
    rng=numpy.random.default_rng(rng)). If a == b everywhere return (0.0, 0.0, 0.0)."""
    arr_a = np.asarray(a, dtype=float)
    arr_b = np.asarray(b, dtype=float)
    if arr_a.shape != arr_b.shape or arr_a.size == 0:
        raise ValueError("a and b must be non-empty sequences of equal length")
    if np.array_equal(arr_a, arr_b):
        return (0.0, 0.0, 0.0)
    diffs = arr_a - arr_b
    mean_diff = float(np.mean(diffs))
    if np.all(diffs == diffs[0]):
        return (mean_diff, mean_diff, mean_diff)
    res = bootstrap(
        (arr_a, arr_b),
        lambda x, y: np.mean(x - y, axis=-1),
        paired=True,
        method="percentile",
        n_resamples=n_resamples,
        rng=np.random.default_rng(rng),
        confidence_level=confidence,
    )
    return (mean_diff, float(res.confidence_interval.low), float(res.confidence_interval.high))


def _validate_pass_k_args(n: int, c: int, k: int) -> None:
    if n <= 0 or k <= 0 or k > n or c < 0 or c > n:
        raise ValueError(f"invalid arguments for pass@k/pass^k: n={n}, c={c}, k={k}")


def pass_at_k(n: int, c: int, k: int) -> float:
    """Probability that AT LEAST ONE of k trials drawn from n (c of them passing) passes.
    Unbiased estimator (Chen et al. 2021): 1 - C(n-c, k) / C(n, k). Raise ValueError if k > n."""
    _validate_pass_k_args(n, c, k)
    if n - c < k:
        return 1.0
    return 1.0 - math.comb(n - c, k) / math.comb(n, k)


def pass_hat_k(n: int, c: int, k: int) -> float:
    """pass^k (tau-bench, Yao et al. 2024): probability that ALL k trials drawn from n pass.
    Unbiased estimator: C(c, k) / C(n, k). Raise ValueError if k > n.
    pass^k <= pass@1 <= pass@k; a reliable agent keeps pass^k close to pass@1."""
    _validate_pass_k_args(n, c, k)
    if c < k:
        return 0.0
    return math.comb(c, k) / math.comb(n, k)
