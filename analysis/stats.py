"""Run-level intervals/tests with a small stdlib incomplete-beta implementation."""
import math


def wilson(x, n, z=1.959963984540054):
    if n == 0:
        return (None, None)
    p = x / n
    denominator = 1 + z * z / n
    center = (p + z * z / (2 * n)) / denominator
    margin = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / denominator
    return (max(0.0, center - margin), min(1.0, center + margin))


def beta_fraction(a, b, x):
    if x <= 0:
        return 0.0
    if x >= 1:
        return 1.0
    def fraction():
        qab, qap, qam = a + b, a + 1, a - 1
        c = 1.0
        d = 1.0 - qab * x / qap
        if abs(d) < 1e-300:
            d = 1e-300
        d = 1.0 / d
        result = d
        for m in range(1, 201):
            m2 = 2 * m
            aa = m * (b - m) * x / ((qam + m2) * (a + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-300:
                d = 1e-300
            c = 1.0 + aa / c
            if abs(c) < 1e-300:
                c = 1e-300
            d = 1.0 / d
            result *= c * d
            aa = -(a + m) * (qab + m) * x / ((a + m2) * (qap + m2))
            d = 1.0 + aa * d
            if abs(d) < 1e-300:
                d = 1e-300
            c = 1.0 + aa / c
            if abs(c) < 1e-300:
                c = 1e-300
            d = 1.0 / d
            delta = c * d
            result *= delta
            if abs(delta - 1.0) < 3e-14:
                return result
        raise ArithmeticError("beta continued fraction did not converge")
    front = math.exp(math.lgamma(a + b) - math.lgamma(a) - math.lgamma(b) + a * math.log(x) + b * math.log1p(-x))
    return front * fraction() / a


def beta_ppf(probability, a, b):
    low, high = 0.0, 1.0
    for _ in range(100):
        middle = (low + high) / 2
        if beta_fraction(a, b, middle) < probability:
            low = middle
        else:
            high = middle
    return (low + high) / 2


def clopper_pearson(x, n, alpha=0.05):
    if n == 0:
        return (None, None)
    lower = 0.0 if x == 0 else beta_ppf(alpha / 2, x, n - x + 1)
    upper = 1.0 if x == n else beta_ppf(1 - alpha / 2, x + 1, n - x)
    return (lower, upper)


def one_sided_zero_upper(n, alpha=0.05):
    return 1.0 if n == 0 else 1.0 - alpha ** (1.0 / n)


def fisher_exact_two_sided(a, b, c, d):
    """2x2 table [[a,b],[c,d]], fixed margins, probability-ordering definition."""
    row1, row2 = a + b, c + d
    col1, n = a + c, a + b + c + d
    def probability(x):
        return math.comb(row1, x) * math.comb(row2, col1 - x) / math.comb(n, col1)
    observed = probability(a)
    low, high = max(0, col1 - row2), min(row1, col1)
    return min(1.0, sum(probability(x) for x in range(low, high + 1) if probability(x) <= observed * (1 + 1e-12)))


def holm(p_values):
    ordered = sorted(enumerate(p_values), key=lambda item: item[1])
    adjusted = [0.0] * len(p_values)
    running = 0.0
    for rank, (index, value) in enumerate(ordered):
        running = max(running, min(1.0, (len(p_values) - rank) * value))
        adjusted[index] = running
    return adjusted


def cohen_kappa(labels_a, labels_b):
    if len(labels_a) != len(labels_b):
        raise ValueError("coder label counts differ")
    pairs = [(a, b) for a, b in zip(labels_a, labels_b) if a is not None and b is not None]
    if not pairs:
        return None
    observed = sum(a == b for a, b in pairs) / len(pairs)
    labels = set(a for a, _ in pairs) | set(b for _, b in pairs)
    expected = sum((sum(a == label for a, _ in pairs) / len(pairs)) * (sum(b == label for _, b in pairs) / len(pairs)) for label in labels)
    return None if expected == 1.0 else (observed - expected) / (1 - expected)
