#!/usr/bin/env python3

"""
Data Visualization with Matplotlib

A self-contained analytical visualization workflow covering:
- figures and axes
- labels and annotations
- legends
- linear and logarithmic scales
- subplots
- customization
- validation and edge cases
- saving figures safely
- basic visualization testing

The example models monthly software-delivery metrics for four teams.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

import math
import matplotlib.pyplot as plt
from matplotlib.ticker import FuncFormatter, MaxNLocator


@dataclass(frozen=True)
class MonthlyMetric:
    month: str
    deployments: int
    incidents: int
    lead_time_hours: float
    coverage_percent: float


@dataclass(frozen=True)
class TeamSeries:
    name: str
    metrics: tuple[MonthlyMetric, ...]

    def validate(self) -> None:
        if not self.name.strip():
            raise ValueError("Team name cannot be empty.")

        if not self.metrics:
            raise ValueError(f"{self.name}: at least one metric is required.")

        months = [m.month for m in self.metrics]
        if len(months) != len(set(months)):
            raise ValueError(f"{self.name}: duplicate months detected.")

        for metric in self.metrics:
            if metric.deployments < 0:
                raise ValueError(f"{self.name}: deployments cannot be negative.")
            if metric.incidents < 0:
                raise ValueError(f"{self.name}: incidents cannot be negative.")
            if metric.lead_time_hours <= 0:
                raise ValueError(f"{self.name}: lead time must be positive.")
            if not 0 <= metric.coverage_percent <= 100:
                raise ValueError(
                    f"{self.name}: coverage must be between 0 and 100."
                )

    @property
    def deployments(self) -> list[int]:
        return [m.deployments for m in self.metrics]

    @property
    def incidents(self) -> list[int]:
        return [m.incidents for m in self.metrics]

    @property
    def lead_time(self) -> list[float]:
        return [m.lead_time_hours for m in self.metrics]

    @property
    def coverage(self) -> list[float]:
        return [m.coverage_percent for m in self.metrics]


def build_data() -> tuple[TeamSeries, ...]:
    data = (
        TeamSeries(
            "Platform",
            (
                MonthlyMetric("Jan", 42, 8, 18.0, 76),
                MonthlyMetric("Feb", 48, 7, 16.0, 79),
                MonthlyMetric("Mar", 53, 6, 14.0, 82),
                MonthlyMetric("Apr", 61, 5, 12.0, 85),
                MonthlyMetric("May", 67, 4, 10.5, 88),
                MonthlyMetric("Jun", 74, 4, 9.2, 91),
            ),
        ),
        TeamSeries(
            "Payments",
            (
                MonthlyMetric("Jan", 31, 10, 24.0, 71),
                MonthlyMetric("Feb", 35, 9, 22.0, 74),
                MonthlyMetric("Mar", 39, 8, 19.0, 77),
                MonthlyMetric("Apr", 44, 7, 17.0, 80),
                MonthlyMetric("May", 49, 6, 15.0, 83),
                MonthlyMetric("Jun", 55, 5, 13.5, 86),
            ),
        ),
        TeamSeries(
            "Analytics",
            (
                MonthlyMetric("Jan", 25, 5, 20.0, 81),
                MonthlyMetric("Feb", 28, 5, 18.0, 83),
                MonthlyMetric("Mar", 34, 4, 15.5, 86),
                MonthlyMetric("Apr", 38, 3, 13.0, 89),
                MonthlyMetric("May", 43, 3, 11.5, 92),
                MonthlyMetric("Jun", 47, 2, 10.0, 94),
            ),
        ),
    )

    for team in data:
        team.validate()

    return data


def safe_percent_change(first: float, last: float) -> float:
    if first == 0:
        raise ValueError("Percentage change is undefined when the initial value is zero.")
    return (last - first) / first * 100


def annotate_extreme(
    ax: plt.Axes,
    x: int,
    y: float,
    text: str,
    *,
    offset: tuple[int, int] = (0, 10),
) -> None:
    ax.annotate(
        text,
        xy=(x, y),
        xytext=offset,
        textcoords="offset points",
        ha="center",
        arrowprops={
            "arrowstyle": "->",
            "connectionstyle": "arc3",
        },
    )


def create_dashboard(
    teams: Iterable[TeamSeries],
    output_file: Path,
) -> None:
    teams = tuple(teams)
    if not teams:
        raise ValueError("At least one team is required.")

    months = [m.month for m in teams[0].metrics]
    if any([m.month for m in team.metrics] != months for team in teams):
        raise ValueError("All teams must use the same monthly periods.")

    # A constrained layout avoids overlapping titles, labels, and legends.
    fig, axes = plt.subplots(
        2,
        2,
        figsize=(14, 9),
        constrained_layout=True,
    )

    ax_deployments = axes[0, 0]
    ax_incidents = axes[0, 1]
    ax_lead_time = axes[1, 0]
    ax_coverage = axes[1, 1]

    # Figure-level title is distinct from axes-level titles.
    fig.suptitle(
        "Software Delivery Performance Dashboard",
        fontsize=18,
        fontweight="bold",
    )

    x = list(range(len(months)))

    # 1. Line chart: deployments.
    for team in teams:
        ax_deployments.plot(
            x,
            team.deployments,
            marker="o",
            linewidth=2,
            label=team.name,
        )

    ax_deployments.set_title("Monthly Deployments")
    ax_deployments.set_xlabel("Month")
    ax_deployments.set_ylabel("Deployments")
    ax_deployments.set_xticks(x, months)
    ax_deployments.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax_deployments.grid(True, alpha=0.25)
    ax_deployments.legend(title="Team")

    # Annotate the highest deployment value.
    best_team = max(teams, key=lambda team: team.deployments[-1])
    best_value = best_team.deployments[-1]
    annotate_extreme(
        ax_deployments,
        x[-1],
        best_value,
        f"{best_team.name}: {best_value}",
    )

    # 2. Grouped bars: incidents.
    width = 0.22
    for index, team in enumerate(teams):
        positions = [value + (index - 1) * width for value in x]
        ax_incidents.bar(
            positions,
            team.incidents,
            width=width,
            label=team.name,
        )

    ax_incidents.set_title("Production Incidents")
    ax_incidents.set_xlabel("Month")
    ax_incidents.set_ylabel("Incidents")
    ax_incidents.set_xticks(x, months)
    ax_incidents.yaxis.set_major_locator(MaxNLocator(integer=True))
    ax_incidents.grid(axis="y", alpha=0.25)
    ax_incidents.legend(title="Team")

    # 3. Log-scale visualization.
    # Lead time remains positive, making logarithmic scaling valid.
    for team in teams:
        ax_lead_time.plot(
            x,
            team.lead_time,
            marker="s",
            linewidth=2,
            label=team.name,
        )

    ax_lead_time.set_yscale("log")
    ax_lead_time.set_title("Lead Time Distribution on Log Scale")
    ax_lead_time.set_xlabel("Month")
    ax_lead_time.set_ylabel("Lead Time (hours, logarithmic)")
    ax_lead_time.set_xticks(x, months)
    ax_lead_time.grid(True, which="both", alpha=0.25)
    ax_lead_time.legend(title="Team")

    # 4. Coverage percentages with a custom formatter.
    for team in teams:
        ax_coverage.plot(
            x,
            team.coverage,
            marker="^",
            linewidth=2,
            label=team.name,
        )

    ax_coverage.set_title("Automated Test Coverage")
    ax_coverage.set_xlabel("Month")
    ax_coverage.set_ylabel("Coverage")
    ax_coverage.set_xticks(x, months)
    ax_coverage.set_ylim(60, 100)
    ax_coverage.yaxis.set_major_formatter(
        FuncFormatter(lambda value, _: f"{value:.0f}%")
    )
    ax_coverage.grid(True, alpha=0.25)
    ax_coverage.legend(title="Team")

    # Security: avoid arbitrary paths and create only the requested output directory.
    output_file = output_file.resolve()
    output_file.parent.mkdir(parents=True, exist_ok=True)

    fig.savefig(
        output_file,
        dpi=160,
        bbox_inches="tight",
        metadata={
            "Title": "Software Delivery Performance Dashboard",
            "Author": "Matplotlib Visualization Workflow",
        },
    )

    plt.close(fig)


def print_analysis(teams: Iterable[TeamSeries]) -> None:
    print("Visualization analysis")
    print("=" * 60)

    for team in teams:
        deployment_change = safe_percent_change(
            team.deployments[0],
            team.deployments[-1],
        )
        lead_time_change = safe_percent_change(
            team.lead_time[0],
            team.lead_time[-1],
        )

        print(
            f"{team.name:12s} | "
            f"deployments change: {deployment_change:7.2f}% | "
            f"lead-time change: {lead_time_change:7.2f}% | "
            f"final coverage: {team.coverage[-1]:5.1f}%"
        )


def run_self_checks(teams: tuple[TeamSeries, ...]) -> None:
    assert teams
    assert all(team.metrics for team in teams)

    for team in teams:
        assert all(value >= 0 for value in team.deployments)
        assert all(value >= 0 for value in team.incidents)
        assert all(value > 0 for value in team.lead_time)
        assert all(0 <= value <= 100 for value in team.coverage)

    # Matplotlib's non-interactive backend can be used in CI environments.
    print("Validation checks passed.")


def main() -> None:
    teams = build_data()
    run_self_checks(teams)
    print_analysis(teams)

    output = Path("output") / "software_delivery_dashboard.png"
    create_dashboard(teams, output)

    print(f"Figure written to: {output.resolve()}")


if __name__ == "__main__":
    main()
