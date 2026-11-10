#!/usr/bin/env python3
"""
ANOVA Statistical Analysis Toolkit
===================================

Implements:
- One-way ANOVA
- Two-way ANOVA with interaction
- ANOVA assumptions and diagnostics
- Levene's variance homogeneity test
- Jarque-Bera residual normality diagnostic
- Tukey-style pairwise comparisons using pooled-variance t tests
- Welch pairwise comparisons with Holm correction
- Effect sizes: eta-squared and omega-squared
- Confidence intervals and descriptive statistics
- CSV import/export
- Validation, exception handling and automated tests

Dependencies: Python 3.10+ standard library only.
"""

from __future__ import annotations

import csv
import json
import math
import random
import statistics
import logging

from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
from collections import defaultdict
from typing import Iterable, Optional


logging.basicConfig(
    level=logging.INFO,
    format="%(levelname)s: %(message)s"
)

LOGGER = logging.getLogger("anova")


# ============================================================
# 1. DOMAIN TYPES
# ============================================================

class ANOVAError(Exception):
    """Base exception for statistical analysis errors."""


class ValidationError(ANOVAError):
    """Invalid statistical input."""


class AnalysisType(Enum):
    ONE_WAY = "one_way"
    TWO_WAY = "two_way"


class AssumptionStatus(Enum):
    PASS = "pass"
    WARNING = "warning"
    FAIL = "fail"


@dataclass(frozen=True)
class Observation:
    value: float
    group: str
    factor_b: Optional[str] = None

    def __post_init__(self):
        if not math.isfinite(self.value):
            raise ValidationError("Observation must be finite.")

        if not self.group.strip():
            raise ValidationError("Factor A cannot be empty.")

        if self.factor_b is not None and not self.factor_b.strip():
            raise ValidationError("Factor B cannot be empty.")


@dataclass
class ANOVAResult:
    analysis: str
    source: str
    df_between: int
    df_within: int
    ss_between: float
    ss_within: float
    ms_between: float
    ms_within: float
    f_statistic: float
    p_value: float
    eta_squared: float
    omega_squared: float

    def to_dict(self):
        return asdict(self)


@dataclass
class AssumptionResult:
    name: str
    statistic: float
    p_value: float
    status: str
    interpretation: str


@dataclass
class PairwiseResult:
    group_a: str
    group_b: str
    mean_difference: float
    statistic: float
    raw_p_value: float
    adjusted_p_value: float
    significant: bool
    method: str


# ============================================================
# 2. SPECIAL FUNCTIONS
# ============================================================

def regularized_beta(x: float, a: float, b: float) -> float:
    """Regularized incomplete beta function."""

    if a <= 0 or b <= 0:
        raise ValueError("Beta parameters must be positive.")

    if x <= 0:
        return 0.0

    if x >= 1:
        return 1.0

    def continued_fraction(a_, b_, x_):
        qab = a_ + b_
        qap = a_ + 1.0
        qam = a_ - 1.0

        c = 1.0
        d = 1.0 - qab * x_ / qap

        if abs(d) < 1e-30:
            d = 1e-30

        d = 1.0 / d
        h = d

        for m in range(1, 301):
            m2 = 2 * m

            aa = (
                m * (b_ - m) * x_
                / ((qam + m2) * (a_ + m2))
            )

            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30

            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30

            d = 1.0 / d
            h *= d * c

            aa = (
                -(a_ + m) * (qab + m) * x_
                / ((a_ + m2) * (qap + m2))
            )

            d = 1.0 + aa * d
            if abs(d) < 1e-30:
                d = 1e-30

            c = 1.0 + aa / c
            if abs(c) < 1e-30:
                c = 1e-30

            d = 1.0 / d

            delta = d * c
            h *= delta

            if abs(delta - 1.0) < 3e-14:
                break

        return h

    front = math.exp(
        math.lgamma(a + b)
        - math.lgamma(a)
        - math.lgamma(b)
        + a * math.log(x)
        + b * math.log1p(-x)
    )

    if x < (a + 1) / (a + b + 2):
        return front * continued_fraction(a, b, x) / a

    return 1.0 - (
        front * continued_fraction(b, a, 1.0 - x) / b
    )


def f_survival(f_value: float, df1: int, df2: int) -> float:
    """Upper-tail probability of the F distribution."""

    if df1 <= 0 or df2 <= 0:
        raise ValidationError("F distribution degrees of freedom must be positive.")

    if f_value <= 0:
        return 1.0

    x = df2 / (df2 + df1 * f_value)

    return regularized_beta(x, df2 / 2, df1 / 2)


def t_cdf(t_value: float, df: float) -> float:
    """Student's t cumulative distribution function."""

    if df <= 0:
        raise ValidationError("Degrees of freedom must be positive.")

    x = df / (df + t_value * t_value)
    ib = regularized_beta(x, df / 2, 0.5)

    if t_value >= 0:
        return 1.0 - 0.5 * ib

    return 0.5 * ib


def two_tailed_t_p(t_value: float, df: float) -> float:
    return min(1.0, 2.0 * (1.0 - t_cdf(abs(t_value), df)))


def chi_square_survival(x: float, df: int) -> float:
    """Chi-square survival function using the incomplete gamma function."""

    if x <= 0:
        return 1.0

    if df <= 0:
        raise ValidationError("Chi-square degrees of freedom must be positive.")

    a = df / 2.0
    xx = x / 2.0

    if xx < a + 1:

        term = 1.0 / a
        total = term
        ap = a

        for _ in range(1000):
            ap += 1
            term *= xx / ap
            total += term

            if abs(term) < abs(total) * 1e-14:
                break

        p = total * math.exp(
            -xx + a * math.log(xx) - math.lgamma(a)
        )

        return max(0.0, min(1.0, 1.0 - p))

    b = xx + 1.0 - a
    c = 1e30
    d = 1.0 / b
    h = d

    for i in range(1, 1000):
        an = -i * (i - a)
        b += 2

        d = an * d + b
        if abs(d) < 1e-30:
            d = 1e-30

        c = b + an / c
        if abs(c) < 1e-30:
            c = 1e-30

        d = 1.0 / d
        delta = d * c
        h *= delta

        if abs(delta - 1.0) < 1e-14:
            break

    return max(
        0.0,
        min(
            1.0,
            math.exp(
                -xx + a * math.log(xx) - math.lgamma(a)
            ) * h
        )
    )


# ============================================================
# 3. DATA MANAGEMENT
# ============================================================

class Dataset:
    def __init__(self, observations: Iterable[Observation]):
        self.observations = list(observations)

        if not self.observations:
            raise ValidationError("Dataset cannot be empty.")

    @classmethod
    def from_csv(cls, file_path: str):
        records = []

        with open(file_path, newline="", encoding="utf-8") as file:
            reader = csv.DictReader(file)

            required = {"value", "group"}

            if not reader.fieldnames or not required.issubset(
                reader.fieldnames
            ):
                raise ValidationError(
                    "CSV requires value and group columns."
                )

            for row in reader:
                records.append(
                    Observation(
                        value=float(row["value"]),
                        group=row["group"],
                        factor_b=row.get("factor_b") or None
                    )
                )

        return cls(records)

    def grouped(self):
        groups = defaultdict(list)

        for obs in self.observations:
            groups[obs.group].append(obs.value)

        return dict(groups)

    def two_factor_grouped(self):
        groups = defaultdict(list)

        for obs in self.observations:
            if obs.factor_b is None:
                raise ValidationError(
                    "Two-way ANOVA requires factor_b for every observation."
                )

            groups[(obs.group, obs.factor_b)].append(obs.value)

        return dict(groups)

    def validate_minimum_groups(self):
        groups = self.grouped()

        if len(groups) < 2:
            raise ValidationError(
                "ANOVA requires at least two groups."
            )

        if any(len(values) < 2 for values in groups.values()):
            raise ValidationError(
                "Every group requires at least two observations."
            )

        return groups


# ============================================================
# 4. DESCRIPTIVE STATISTICS
# ============================================================

def descriptive_statistics(values):
    if not values:
        raise ValidationError("Cannot summarize an empty group.")

    return {
        "count": len(values),
        "mean": statistics.mean(values),
        "median": statistics.median(values),
        "variance": statistics.variance(values) if len(values) > 1 else 0,
        "standard_deviation": statistics.stdev(values) if len(values) > 1 else 0,
        "minimum": min(values),
        "maximum": max(values)
    }


# ============================================================
# 5. ONE-WAY ANOVA
# ============================================================

def one_way_anova(dataset: Dataset) -> ANOVAResult:

    groups = dataset.validate_minimum_groups()

    k = len(groups)
    all_values = [
        value
        for group in groups.values()
        for value in group
    ]

    n = len(all_values)
    grand_mean = statistics.mean(all_values)

    ss_between = sum(
        len(values) * (statistics.mean(values) - grand_mean) ** 2
        for values in groups.values()
    )

    ss_within = sum(
        sum(
            (value - statistics.mean(values)) ** 2
            for value in values
        )
        for values in groups.values()
    )

    df_between = k - 1
    df_within = n - k

    if df_within <= 0:
        raise ValidationError("Insufficient residual degrees of freedom.")

    ms_between = ss_between / df_between
    ms_within = ss_within / df_within

    if ms_within <= 0:
        if ms_between <= 0:
            f_value = 0.0
            p_value = 1.0
        else:
            f_value = math.inf
            p_value = 0.0
    else:
        f_value = ms_between / ms_within
        p_value = f_survival(f_value, df_between, df_within)

    ss_total = ss_between + ss_within

    eta = ss_between / ss_total if ss_total else 0.0

    omega = (
        (ss_between - df_between * ms_within)
        / (ss_total + ms_within)
        if ss_total + ms_within > 0
        else 0.0
    )

    return ANOVAResult(
        analysis="One-way ANOVA",
        source="Group",
        df_between=df_between,
        df_within=df_within,
        ss_between=ss_between,
        ss_within=ss_within,
        ms_between=ms_between,
        ms_within=ms_within,
        f_statistic=f_value,
        p_value=p_value,
        eta_squared=eta,
        omega_squared=omega
    )


# ============================================================
# 6. TWO-WAY ANOVA WITH INTERACTION
# ============================================================

@dataclass
class TwoWayResult:
    source: str
    df: int
    sum_squares: float
    mean_square: float
    f_statistic: float
    p_value: float


def two_way_anova(dataset: Dataset):

    cells = dataset.two_factor_grouped()

    factor_a = sorted({a for a, b in cells})
    factor_b = sorted({b for a, b in cells})

    a_count = len(factor_a)
    b_count = len(factor_b)

    if a_count < 2 or b_count < 2:
        raise ValidationError(
            "Two-way ANOVA requires at least two levels per factor."
        )

    cell_sizes = {len(values) for values in cells.values()}

    if len(cells) != a_count * b_count:
        raise ValidationError(
            "The factorial design contains missing cells."
        )

    if len(cell_sizes) != 1:
        raise ValidationError(
            "This implementation requires a balanced factorial design."
        )

    replication = next(iter(cell_sizes))

    if replication < 2:
        raise ValidationError(
            "At least two observations per cell are required."
        )

    all_values = [
        value
        for values in cells.values()
        for value in values
    ]

    grand_mean = statistics.mean(all_values)

    means_a = {
        a: statistics.mean(
            [
                x
                for (aa, bb), values in cells.items()
                if aa == a
                for x in values
            ]
        )
        for a in factor_a
    }

    means_b = {
        b: statistics.mean(
            [
                x
                for (aa, bb), values in cells.items()
                if bb == b
                for x in values
            ]
        )
        for b in factor_b
    }

    means_cell = {
        key: statistics.mean(values)
        for key, values in cells.items()
    }

    ss_a = (
        b_count * replication
        * sum((means_a[a] - grand_mean) ** 2 for a in factor_a)
    )

    ss_b = (
        a_count * replication
        * sum((means_b[b] - grand_mean) ** 2 for b in factor_b)
    )

    ss_interaction = replication * sum(
        (
            means_cell[(a, b)]
            - means_a[a]
            - means_b[b]
            + grand_mean
        ) ** 2
        for a in factor_a
        for b in factor_b
    )

    ss_error = sum(
        sum((x - means_cell[key]) ** 2 for x in values)
        for key, values in cells.items()
    )

    df_a = a_count - 1
    df_b = b_count - 1
    df_interaction = df_a * df_b
    df_error = a_count * b_count * (replication - 1)

    ms_error = ss_error / df_error

    def calculate(source, df, ss):
        ms = ss / df

        if ms_error == 0:
            f_value = math.inf if ms > 0 else 0.0
            p_value = 0.0 if ms > 0 else 1.0
        else:
            f_value = ms / ms_error
            p_value = f_survival(f_value, df, df_error)

        return TwoWayResult(
            source,
            df,
            ss,
            ms,
            f_value,
            p_value
        )

    return {
        "factor_a": calculate("Factor A", df_a, ss_a),
        "factor_b": calculate("Factor B", df_b, ss_b),
        "interaction": calculate(
            "A x B",
            df_interaction,
            ss_interaction
        ),
        "error": {
            "sum_squares": ss_error,
            "degrees_of_freedom": df_error,
            "mean_square": ms_error
        }
    }


# ============================================================
# 7. ASSUMPTION DIAGNOSTICS
# ============================================================

def levene_test(groups):

    if len(groups) < 2:
        raise ValidationError("Levene's test requires at least two groups.")

    deviations = {}

    for name, values in groups.items():
        if len(values) < 2:
            raise ValidationError("Levene's test requires two values per group.")

        center = statistics.median(values)

        deviations[name] = [
            abs(x - center) for x in values
        ]

    return one_way_anova(
        Dataset([
            Observation(value, group)
            for group, values in deviations.items()
            for value in values
        ])
    )


def jarque_bera_test(values):

    if len(values) < 3:
        raise ValidationError("At least three residuals are required.")

    mean = statistics.mean(values)

    variance = sum(
        (x - mean) ** 2 for x in values
    ) / len(values)

    if variance == 0:
        return 0.0, 1.0

    skewness = (
        sum((x - mean) ** 3 for x in values)
        / len(values)
        / variance ** 1.5
    )

    kurtosis = (
        sum((x - mean) ** 4 for x in values)
        / len(values)
        / variance ** 2
    )

    jb = len(values) / 6.0 * (
        skewness ** 2
        + (kurtosis - 3.0) ** 2 / 4.0
    )

    return jb, chi_square_survival(jb, 2)


def assumption_report(dataset, alpha=0.05):

    groups = dataset.validate_minimum_groups()

    residuals = [
        x - statistics.mean(values)
        for values in groups.values()
        for x in values
    ]

    levene = levene_test(groups)

    jb, normality_p = jarque_bera_test(residuals)

    return [
        AssumptionResult(
            "Independence",
            0.0,
            float("nan"),
            AssumptionStatus.WARNING.value,
            "Must be established through study design; "
            "it cannot be proven from these observations."
        ),
        AssumptionResult(
            "Equal variances (median-centered Levene)",
            levene.f_statistic,
            levene.p_value,
            (
                AssumptionStatus.PASS.value
                if levene.p_value >= alpha
                else AssumptionStatus.WARNING.value
            ),
            "No statistically significant variance difference detected."
            if levene.p_value >= alpha
            else "Evidence of unequal group variances."
        ),
        AssumptionResult(
            "Residual normality (Jarque-Bera)",
            jb,
            normality_p,
            (
                AssumptionStatus.PASS.value
                if normality_p >= alpha
                else AssumptionStatus.WARNING.value
            ),
            "No significant deviation detected."
            if normality_p >= alpha
            else "Residual normality may be questionable."
        )
    ]


# ============================================================
# 8. MULTIPLE COMPARISON CORRECTION
# ============================================================

def holm_adjust(p_values):

    indexed = sorted(
        enumerate(p_values),
        key=lambda item: item[1]
    )

    adjusted = [0.0] * len(p_values)
    running_max = 0.0
    total = len(p_values)

    for rank, (index, p_value) in enumerate(indexed):
        corrected = min(1.0, (total - rank) * p_value)
        running_max = max(running_max, corrected)
        adjusted[index] = running_max

    return adjusted


def pairwise_posthoc(dataset, alpha=0.05, equal_variances=True):

    groups = dataset.validate_minimum_groups()

    names = sorted(groups)
    comparisons = []

    for i in range(len(names)):
        for j in range(i + 1, len(names)):

            name_a = names[i]
            name_b = names[j]

            a = groups[name_a]
            b = groups[name_b]

            mean_difference = statistics.mean(a) - statistics.mean(b)

            if equal_variances:

                pooled_df = len(a) + len(b) - 2

                pooled_variance = (
                    (len(a) - 1) * statistics.variance(a)
                    + (len(b) - 1) * statistics.variance(b)
                ) / pooled_df

                standard_error = math.sqrt(
                    pooled_variance * (
                        1 / len(a) + 1 / len(b)
                    )
                )

                df = pooled_df
                method = "Pooled-variance pairwise t"

            else:

                va = statistics.variance(a) / len(a)
                vb = statistics.variance(b) / len(b)

                standard_error = math.sqrt(va + vb)

                denominator = (
                    va ** 2 / (len(a) - 1)
                    + vb ** 2 / (len(b) - 1)
                )

                df = (
                    (va + vb) ** 2 / denominator
                    if denominator > 0
                    else 1
                )

                method = "Welch pairwise t"

            if standard_error == 0:
                t_value = (
                    math.copysign(math.inf, mean_difference)
                    if mean_difference != 0
                    else 0.0
                )
                p_value = 0.0 if mean_difference != 0 else 1.0
            else:
                t_value = mean_difference / standard_error
                p_value = two_tailed_t_p(t_value, df)

            comparisons.append({
                "a": name_a,
                "b": name_b,
                "difference": mean_difference,
                "t": t_value,
                "p": p_value,
                "method": method
            })

    adjusted = holm_adjust(
        [item["p"] for item in comparisons]
    )

    return [
        PairwiseResult(
            group_a=item["a"],
            group_b=item["b"],
            mean_difference=item["difference"],
            statistic=item["t"],
            raw_p_value=item["p"],
            adjusted_p_value=adjusted[index],
            significant=adjusted[index] < alpha,
            method=item["method"] + " with Holm correction"
        )
        for index, item in enumerate(comparisons)
    ]


# ============================================================
# 9. REPORTING
# ============================================================

class ANOVAReport:

    @staticmethod
    def display(result):

        print("\nANOVA RESULTS")
        print("=" * 65)

        if isinstance(result, ANOVAResult):
            print(f"Analysis: {result.analysis}")
            print(f"F statistic: {result.f_statistic:.6f}")
            print(f"P value: {result.p_value:.8f}")
            print(f"Between-group SS: {result.ss_between:.6f}")
            print(f"Within-group SS: {result.ss_within:.6f}")
            print(f"Eta squared: {result.eta_squared:.6f}")
            print(f"Omega squared: {result.omega_squared:.6f}")

        else:
            for name, item in result.items():
                print(f"\n{name}: {item}")

    @staticmethod
    def export_json(data, file_path):

        def serialize(obj):
            if hasattr(obj, "__dataclass_fields__"):
                return asdict(obj)

            if isinstance(obj, Enum):
                return obj.value

            raise TypeError(f"Unsupported type: {type(obj)}")

        Path(file_path).write_text(
            json.dumps(
                data,
                indent=2,
                default=serialize,
                allow_nan=False
            ),
            encoding="utf-8"
        )


# ============================================================
# 10. SAMPLE EXPERIMENTS
# ============================================================

def build_one_way_dataset():

    random.seed(42)

    measurements = {
        "Control": [21, 23, 22, 24, 20, 22, 21, 23],
        "Treatment_A": [25, 27, 26, 28, 24, 27, 26, 25],
        "Treatment_B": [30, 32, 29, 31, 33, 30, 32, 31]
    }

    return Dataset([
        Observation(value, group)
        for group, values in measurements.items()
        for value in values
    ])


def build_two_way_dataset():

    values = {
        ("Traditional", "Low"): [10, 11, 9, 10],
        ("Traditional", "High"): [15, 14, 16, 15],
        ("Modern", "Low"): [13, 12, 14, 13],
        ("Modern", "High"): [23, 22, 24, 23]
    }

    return Dataset([
        Observation(value, factor_a, factor_b)
        for (factor_a, factor_b), observations in values.items()
        for value in observations
    ])


# ============================================================
# 11. AUTOMATED TESTS
# ============================================================

def run_tests():

    sample = Dataset([
        Observation(1, "A"),
        Observation(2, "A"),
        Observation(3, "B"),
        Observation(4, "B")
    ])

    result = one_way_anova(sample)

    assert result.df_between == 1
    assert result.df_within == 2
    assert result.f_statistic > 0
    assert 0 <= result.p_value <= 1

    two_way = two_way_anova(build_two_way_dataset())

    assert two_way["factor_a"].df == 1
    assert two_way["factor_b"].df == 1
    assert two_way["interaction"].df == 1

    corrected = holm_adjust([0.01, 0.04, 0.03])

    assert all(0 <= value <= 1 for value in corrected)
    assert corrected[0] <= corrected[1]

    assert f_survival(0, 1, 10) == 1.0
    assert math.isclose(t_cdf(0, 10), 0.5)

    try:
        Dataset([
            Observation(float("nan"), "A")
        ])
    except ValidationError:
        pass
    else:
        raise AssertionError("Non-finite values must be rejected.")

    LOGGER.info("All automated tests passed.")


# ============================================================
# 12. APPLICATION ENTRY POINT
# ============================================================

def main():

    print("\nANOVA STATISTICAL ANALYSIS TOOLKIT")

    run_tests()

    # One-way ANOVA
    one_way_data = build_one_way_dataset()
    one_way_result = one_way_anova(one_way_data)

    ANOVAReport.display(one_way_result)

    print("\nDESCRIPTIVE STATISTICS")

    for name, values in one_way_data.grouped().items():
        print(name, descriptive_statistics(values))

    print("\nASSUMPTION DIAGNOSTICS")

    for item in assumption_report(one_way_data):
        print(item)

    print("\nPOST-HOC PAIRWISE COMPARISONS")

    for comparison in pairwise_posthoc(
        one_way_data,
        equal_variances=True
    ):
        print(comparison)

    # Unequal-variance post-hoc alternative
    print("\nWELCH POST-HOC COMPARISONS")

    for comparison in pairwise_posthoc(
        one_way_data,
        equal_variances=False
    ):
        print(comparison)

    # Two-way ANOVA
    print("\nTWO-WAY ANOVA")

    two_way_result = two_way_anova(build_two_way_dataset())

    for key, value in two_way_result.items():
        print(key, value)

    # Export reproducible result
    output = {
        "one_way_anova": one_way_result.to_dict(),
        "two_way_anova": {
            key: asdict(value) if isinstance(value, TwoWayResult)
            else value
            for key, value in two_way_result.items()
        },
        "post_hoc": [
            asdict(item)
            for item in pairwise_posthoc(one_way_data)
        ]
    }

    ANOVAReport.export_json(
        output,
        "anova_report.json"
    )

    print("\nReport exported to anova_report.json")


if __name__ == "__main__":
    main()
