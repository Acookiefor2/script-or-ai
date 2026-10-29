import pytest

from src.stats import bootstrap_ci_diff, mean_diff, permutation_p


def test_mean_diff():
    assert mean_diff([0.5, 0.5], [0.25, 0.25]) == pytest.approx(0.25)


def test_identical_groups_have_p_of_one():
    a = [0.1, 0.2, 0.3] * 5
    assert permutation_p(a, list(a), n=2000) == pytest.approx(1.0)


def test_clearly_different_groups_have_small_p():
    assert permutation_p([0.9] * 10, [0.1] * 10, n=2000) < 0.01


def test_permutation_is_reproducible_with_a_seed():
    a, b = [0.1, 0.4, 0.8, 0.3], [0.2, 0.2, 0.3, 0.1]
    assert permutation_p(a, b, n=500, seed=3) == permutation_p(a, b, n=500, seed=3)


def test_ci_of_constant_groups_is_the_difference():
    lo, hi = bootstrap_ci_diff([0.5] * 20, [0.3] * 20, n=500)
    assert lo == pytest.approx(0.2)
    assert hi == pytest.approx(0.2)


def test_ci_for_noisy_equal_groups_contains_zero():
    a = [0.1, 0.5, 0.9, 0.3, 0.7, 0.2, 0.6, 0.4]
    b = [0.2, 0.4, 0.8, 0.3, 0.6, 0.1, 0.7, 0.5]
    lo, hi = bootstrap_ci_diff(a, b, n=2000)
    assert lo < 0 < hi