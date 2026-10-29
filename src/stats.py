"""Tiny, dependency-free statistics helpers for comparing two groups of scores."""
import random
import statistics as st


def mean_diff(a: list, b: list) -> float:
    return st.mean(a) - st.mean(b)


def permutation_p(a: list, b: list, n: int = 20000, seed: int = 0) -> float:
    """Two-sided permutation p-value for the difference in means.

    Shuffles the pooled scores n times and counts how often a split is at least as
    extreme as the real one. The +1 in numerator and denominator keeps p above zero.
    """
    rng = random.Random(seed)
    observed = abs(mean_diff(a, b))
    pool = list(a) + list(b)
    k = len(a)
    hits = 0
    for _ in range(n):
        rng.shuffle(pool)
        if abs(mean_diff(pool[:k], pool[k:])) >= observed - 1e-12:
            hits += 1
    return (hits + 1) / (n + 1)


def bootstrap_ci_diff(a: list, b: list, n: int = 10000, seed: int = 0, alpha: float = 0.05) -> tuple:
    """Percentile bootstrap confidence interval for mean(a) - mean(b)."""
    rng = random.Random(seed)
    diffs = []
    for _ in range(n):
        ra = [rng.choice(a) for _ in a]
        rb = [rng.choice(b) for _ in b]
        diffs.append(mean_diff(ra, rb))
    diffs.sort()
    lo = diffs[int(n * alpha / 2)]
    hi = diffs[int(n * (1 - alpha / 2)) - 1]
    return lo, hi