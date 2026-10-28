#!/usr/bin/env python3
"""
Statistical Visualization Toolkit

Self-contained standard-library implementation of:
- histograms
- box plots
- violin plots
- scatter plots
- density plots
- categorical plots

The script computes descriptive statistics, validates observations, detects
outliers with the IQR rule, and exports a multi-panel SVG without external
dependencies.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from math import exp, pi, sqrt
from pathlib import Path
from statistics import mean, median, pstdev
from typing import Iterable, Sequence


class PlotType(Enum):
    HISTOGRAM = "histogram"
    BOX = "box"
    VIOLIN = "violin"
    SCATTER = "scatter"
    DENSITY = "density"
    CATEGORICAL = "categorical"


class VisualizationError(ValueError):
    pass


@dataclass(frozen=True)
class FiveNumberSummary:
    minimum: float
    q1: float
    median: float
    q3: float
    maximum: float
    lower_fence: float
    upper_fence: float
    outliers: tuple[float, ...]


@dataclass(frozen=True)
class Histogram:
    edges: tuple[float, ...]
    counts: tuple[int, ...]


@dataclass(frozen=True)
class CategorySummary:
    category: str
    count: int
    percentage: float


@dataclass(frozen=True)
class Dataset:
    values: tuple[float, ...]

    def __post_init__(self) -> None:
        if not self.values:
            raise VisualizationError("Dataset must contain at least one value.")
        if not all(isinstance(x, (int, float)) for x in self.values):
            raise VisualizationError("All observations must be numeric.")
        if not all(float("-inf") < float(x) < float("inf") for x in self.values):
            raise VisualizationError("NaN and infinite values are not allowed.")

    @property
    def n(self) -> int:
        return len(self.values)

    @property
    def average(self) -> float:
        return mean(self.values)

    @property
    def standard_deviation(self) -> float:
        return pstdev(self.values)

    @staticmethod
    def percentile(values: Sequence[float], p: float) -> float:
        if not values:
            raise VisualizationError("Cannot calculate a percentile of empty data.")
        if not 0 <= p <= 100:
            raise VisualizationError("Percentile must be between 0 and 100.")

        ordered = sorted(values)
        position = (len(ordered) - 1) * p / 100
        lower = int(position)
        upper = min(lower + 1, len(ordered) - 1)
        fraction = position - lower
        return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction

    def five_number_summary(self) -> FiveNumberSummary:
        q1 = self.percentile(self.values, 25)
        med = self.percentile(self.values, 50)
        q3 = self.percentile(self.values, 75)
        iqr = q3 - q1
        lower = q1 - 1.5 * iqr
        upper = q3 + 1.5 * iqr
        outliers = tuple(x for x in self.values if x < lower or x > upper)

        return FiveNumberSummary(
            minimum=min(self.values),
            q1=q1,
            median=med,
            q3=q3,
            maximum=max(self.values),
            lower_fence=lower,
            upper_fence=upper,
            outliers=outliers,
        )

    def histogram(self, bins: int = 10) -> Histogram:
        if bins < 1:
            raise VisualizationError("Number of bins must be positive.")

        low, high = min(self.values), max(self.values)
        if low == high:
            return Histogram(
                edges=tuple(low + i - 0.5 for i in range(bins + 1)),
                counts=(self.n,) + (0,) * (bins - 1),
            )

        width = (high - low) / bins
        counts = [0] * bins

        for value in self.values:
            index = int((value - low) / width)
            index = min(index, bins - 1)
            counts[index] += 1

        edges = tuple(low + i * width for i in range(bins + 1))
        return Histogram(edges=edges, counts=tuple(counts))

    def kde(self, points: int = 80) -> tuple[tuple[float, float], ...]:
        if points < 2:
            raise VisualizationError("Density requires at least two points.")

        low, high = min(self.values), max(self.values)
        sigma = self.standard_deviation

        if sigma == 0:
            sigma = max(abs(low) * 0.05, 1.0)

        bandwidth = 1.06 * sigma * self.n ** (-1 / 5)
        bandwidth = max(bandwidth, 1e-9)

        padding = 3 * bandwidth
        start = low - padding
        end = high + padding

        result = []
        normalizer = self.n * bandwidth * sqrt(2 * pi)

        for i in range(points):
            x = start + (end - start) * i / (points - 1)
            density = sum(
                exp(-0.5 * ((x - value) / bandwidth) ** 2)
                for value in self.values
            ) / normalizer
            result.append((x, density))

        return tuple(result)


def validate_xy(x: Sequence[float], y: Sequence[float]) -> None:
    if len(x) != len(y):
        raise VisualizationError("Scatter plot requires equal x and y lengths.")
    Dataset(tuple(x))
    Dataset(tuple(y))


def categorical_counts(categories: Sequence[str]) -> tuple[CategorySummary, ...]:
    if not categories:
        raise VisualizationError("At least one category is required.")

    counts: dict[str, int] = {}
    for category in categories:
        normalized = str(category).strip()
        if not normalized:
            raise VisualizationError("Category labels cannot be empty.")
        counts[normalized] = counts.get(normalized, 0) + 1

    total = len(categories)
    return tuple(
        CategorySummary(k, v, 100 * v / total)
        for k, v in sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    )


def svg_header(width: int, height: int, title: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="white"/>',
        f'<text x="30" y="32" font-family="sans-serif" font-size="20" '
        f'font-weight="bold">{title}</text>',
    ]


def esc(text: object) -> str:
    return (
        str(text)
        .replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def axes(parts: list[str], x: float, y: float, width: float, height: float) -> None:
    parts.append(
        f'<line x1="{x}" y1="{y + height}" x2="{x + width}" y2="{y + height}" '
        'stroke="black"/>'
    )
    parts.append(
        f'<line x1="{x}" y1="{y}" x2="{x}" y2="{y + height}" stroke="black"/>'
    )


def histogram_svg(data: Dataset, x: float, y: float, w: float, h: float) -> list[str]:
    hist = data.histogram(8)
    parts: list[str] = []
    axes(parts, x, y, w, h)

    max_count = max(hist.counts)
    plot_w = w / len(hist.counts)

    for i, count in enumerate(hist.counts):
        bar_h = h * count / max_count if max_count else 0
        bx = x + i * plot_w
        by = y + h - bar_h
        parts.append(
            f'<rect x="{bx:.2f}" y="{by:.2f}" width="{plot_w - 2:.2f}" '
            f'height="{bar_h:.2f}" fill="#4c78a8"/>'
        )

    parts.append(f'<text x="{x}" y="{y - 8}" font-family="sans-serif">Histogram</text>')
    return parts


def box_svg(data: Dataset, x: float, y: float, w: float, h: float) -> list[str]:
    s = data.five_number_summary()
    parts: list[str] = []
    axes(parts, x, y, w, h)

    scale_min, scale_max = s.minimum, s.maximum
    if scale_min == scale_max:
        scale_max += 1
        scale_min -= 1

    def sx(value: float) -> float:
        return x + (value - scale_min) / (scale_max - scale_min) * w

    cy = y + h / 2
    q1, q3 = sx(s.q1), sx(s.q3)

    parts.append(f'<line x1="{sx(s.minimum):.2f}" y1="{cy:.2f}" '
                 f'x2="{q1:.2f}" y2="{cy:.2f}" stroke="black"/>')
    parts.append(f'<line x1="{q3:.2f}" y1="{cy:.2f}" '
                 f'x2="{sx(s.maximum):.2f}" y2="{cy:.2f}" stroke="black"/>')
    parts.append(
        f'<rect x="{q1:.2f}" y="{y + h * .25:.2f}" width="{q3-q1:.2f}" '
        f'height="{h*.5:.2f}" fill="#72b7b2" stroke="black"/>'
    )
    parts.append(
        f'<line x1="{sx(s.median):.2f}" y1="{y+h*.25:.2f}" '
        f'x2="{sx(s.median):.2f}" y2="{y+h*.75:.2f}" stroke="black" stroke-width="2"/>'
    )

    for value in s.outliers:
        parts.append(
            f'<circle cx="{sx(value):.2f}" cy="{cy:.2f}" r="4" fill="#e45756"/>'
        )

    parts.append(f'<text x="{x}" y="{y - 8}" font-family="sans-serif">Box Plot</text>')
    return parts


def violin_svg(data: Dataset, x: float, y: float, w: float, h: float) -> list[str]:
    density = data.kde(60)
    maximum = max(v for _, v in density)
    center = x + w / 2

    low, high = density[0][0], density[-1][0]
    if high == low:
        high += 1

    def sy(value: float) -> float:
        return y + h - (value - low) / (high - low) * h

    scale = w * 0.45 / maximum
    left = []
    right = []

    for value, d in density:
        yy = sy(value)
        half = d * scale
        left.append((center - half, yy))
        right.append((center + half, yy))

    points = left + list(reversed(right))
    polygon = " ".join(f"{px:.2f},{py:.2f}" for px, py in points)

    return [
        f'<polygon points="{polygon}" fill="#f2cf5b" stroke="black"/>',
        f'<line x1="{center}" y1="{y}" x2="{center}" y2="{y+h}" stroke="black" opacity=".25"/>',
        f'<text x="{x}" y="{y - 8}" font-family="sans-serif">Violin Plot</text>',
    ]


def scatter_svg(
    x_values: Sequence[float],
    y_values: Sequence[float],
    x: float,
    y: float,
    w: float,
    h: float,
) -> list[str]:
    validate_xy(x_values, y_values)
    xmin, xmax = min(x_values), max(x_values)
    ymin, ymax = min(y_values), max(y_values)

    if xmin == xmax:
        xmax += 1
    if ymin == ymax:
        ymax += 1

    parts: list[str] = []
    axes(parts, x, y, w, h)

    for xv, yv in zip(x_values, y_values):
        px = x + (xv - xmin) / (xmax - xmin) * w
        py = y + h - (yv - ymin) / (ymax - ymin) * h
        parts.append(f'<circle cx="{px:.2f}" cy="{py:.2f}" r="3.5" fill="#54a24b"/>')

    parts.append(f'<text x="{x}" y="{y - 8}" font-family="sans-serif">Scatter Plot</text>')
    return parts


def density_svg(data: Dataset, x: float, y: float, w: float, h: float) -> list[str]:
    density = data.kde()
    max_density = max(v for _, v in density)
    low, high = density[0][0], density[-1][0]
    parts: list[str] = []
    axes(parts, x, y, w, h)

    points = []
    for value, d in density:
        px = x + (value - low) / (high - low) * w
        py = y + h - d / max_density * h
        points.append(f"{px:.2f},{py:.2f}")

    parts.append(
        f'<polyline points="{" ".join(points)}" fill="none" '
        'stroke="#b279a2" stroke-width="2"/>'
    )
    parts.append(f'<text x="{x}" y="{y - 8}" font-family="sans-serif">Density Plot</text>')
    return parts


def categorical_svg(
    categories: Sequence[str], x: float, y: float, w: float, h: float
) -> list[str]:
    summaries = categorical_counts(categories)
    parts: list[str] = []
    axes(parts, x, y, w, h)
    max_count = max(s.count for s in summaries)
    bar_w = w / len(summaries)

    for i, item in enumerate(summaries):
        bar_h = h * item.count / max_count
        bx = x + i * bar_w + 4
        by = y + h - bar_h
        parts.append(
            f'<rect x="{bx:.2f}" y="{by:.2f}" width="{bar_w-8:.2f}" '
            f'height="{bar_h:.2f}" fill="#ff9da6"/>'
        )
        parts.append(
            f'<text x="{bx:.2f}" y="{y+h+18:.2f}" font-family="sans-serif" '
            f'font-size="11">{esc(item.category)}</text>'
        )

    parts.append(
        f'<text x="{x}" y="{y - 8}" font-family="sans-serif">Categorical Plot</text>'
    )
    return parts


def build_report() -> str:
    # A deliberately skewed dataset makes differences among plot types visible.
    measurements = Dataset((
        42, 45, 47, 48, 49, 50, 51, 52, 52, 53,
        54, 55, 56, 57, 58, 59, 61, 62, 63, 65,
        68, 70, 74, 79, 91
    ))

    x_values = tuple(range(1, measurements.n + 1))
    y_values = measurements.values
    categories = (
        "API", "API", "Web", "Web", "Web", "Mobile", "API",
        "Mobile", "Web", "API", "Desktop", "Web", "Mobile", "API"
    )

    width, height = 1100, 900
    parts = svg_header(width, height, "Statistical Visualization Report")

    panels = [
        histogram_svg(measurements, 50, 70, 300, 220),
        box_svg(measurements, 400, 70, 300, 220),
        violin_svg(measurements, 750, 70, 300, 220),
        scatter_svg(x_values, y_values, 50, 390, 300, 220),
        density_svg(measurements, 400, 390, 300, 220),
        categorical_svg(categories, 750, 390, 300, 220),
    ]

    for panel in panels:
        parts.extend(panel)

    summary = measurements.five_number_summary()
    parts.extend([
        '<text x="50" y="680" font-family="sans-serif" font-size="14">'
        f'Count: {measurements.n} | Mean: {measurements.average:.2f} | '
        f'SD: {measurements.standard_deviation:.2f}</text>',
        '<text x="50" y="710" font-family="sans-serif" font-size="14">'
        f'Q1: {summary.q1:.2f} | Median: {summary.median:.2f} | '
        f'Q3: {summary.q3:.2f} | Outliers: {len(summary.outliers)}</text>',
        '<text x="50" y="750" font-family="sans-serif" font-size="13">'
        'IQR fences identify observations outside Q1 - 1.5×IQR and Q3 + 1.5×IQR.</text>',
        '</svg>',
    ])

    return "\n".join(parts)


def main() -> None:
    output = Path("statistical_visualization_report.svg")
    output.write_text(build_report(), encoding="utf-8")

    data = Dataset((10, 11, 12, 12, 13, 14, 15, 20, 35))
    summary = data.five_number_summary()

    assert summary.q1 <= summary.median <= summary.q3
    assert len(data.histogram(4).counts) == 4
    assert len(data.kde(20)) == 20

    print(f"Wrote {output.resolve()}")
    print(f"n={data.n}, mean={data.average:.2f}, sd={data.standard_deviation:.2f}")
    print(f"median={summary.median:.2f}, outliers={summary.outliers}")


if __name__ == "__main__":
    main()
