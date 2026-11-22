from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal
from enum import Enum
from typing import Iterable


class TimePeriod(Enum):
    MTD = "month_to_date"
    QTD = "quarter_to_date"
    YTD = "year_to_date"


@dataclass(frozen=True)
class SalesRecord:
    transaction_id: int
    transaction_date: date
    product: str
    region: str
    amount: Decimal

    def __post_init__(self):
        if self.transaction_id <= 0:
            raise ValueError("Transaction ID must be positive.")
        if not self.product.strip() or not self.region.strip():
            raise ValueError("Product and region are required.")
        if self.amount < 0:
            raise ValueError("Sales amount cannot be negative.")


@dataclass(frozen=True)
class DateDimension:
    calendar_date: date

    @property
    def year(self) -> int:
        return self.calendar_date.year

    @property
    def month(self) -> int:
        return self.calendar_date.month

    @property
    def quarter(self) -> int:
        return (self.month - 1) // 3 + 1

    @property
    def year_month(self) -> str:
        return self.calendar_date.strftime("%Y-%m")

    @property
    def day_of_year(self) -> int:
        return self.calendar_date.timetuple().tm_yday


class CalendarTable:
    """Continuous calendar dimension with validated date boundaries."""

    def __init__(self, start: date, end: date):
        if start > end:
            raise ValueError("Calendar start must not exceed end.")

        self.start = start
        self.end = end
        self.dates = tuple(
            DateDimension(start + timedelta(days=i))
            for i in range((end - start).days + 1)
        )
        self.date_set = {row.calendar_date for row in self.dates}

    def validate(self, selected: Iterable[date]) -> list[date]:
        result = sorted(set(selected))

        if not result:
            raise ValueError("Date selection cannot be empty.")

        if any(d not in self.date_set for d in result):
            raise ValueError("Selected date is outside the calendar.")

        return result

    def full_year(self, year: int) -> list[date]:
        return [
            row.calendar_date
            for row in self.dates
            if row.year == year
        ]


class SalesModel:
    """
    A small analytical model implementing common DAX-style
    time intelligence calculations.
    """

    def __init__(
        self,
        calendar: CalendarTable,
        transactions: Iterable[SalesRecord],
    ):
        self.calendar = calendar
        self.transactions = tuple(transactions)
        self.sales_by_date: dict[date, Decimal] = defaultdict(Decimal)

        seen_ids = set()

        for transaction in self.transactions:
            if transaction.transaction_id in seen_ids:
                raise ValueError("Duplicate transaction ID.")

            seen_ids.add(transaction.transaction_id)

            if transaction.transaction_date not in calendar.date_set:
                raise ValueError(
                    f"Transaction date outside calendar: "
                    f"{transaction.transaction_date}"
                )

            self.sales_by_date[transaction.transaction_date] += (
                transaction.amount
            )

    def sales(self, dates: Iterable[date]) -> Decimal:
        """Equivalent to evaluating SUM(Sales[Amount]) in a date context."""
        return sum(
            (self.sales_by_date[d] for d in set(dates)),
            Decimal("0")
        )

    @staticmethod
    def shift_year(d: date, years: int = -1) -> date:
        """Shift a date by years, clamping invalid leap-day dates."""
        target_year = d.year + years

        try:
            return d.replace(year=target_year)
        except ValueError:
            if d.month == 2 and d.day == 29:
                return date(target_year, 2, 28)
            raise

    @staticmethod
    def shift_month(d: date, months: int) -> date:
        """Shift a date by whole months while preserving end-of-month behavior."""
        month_index = d.year * 12 + d.month - 1 + months
        year, month_index = divmod(month_index, 12)
        month = month_index + 1

        import calendar

        last_day = calendar.monthrange(year, month)[1]

        if d.day == calendar.monthrange(d.year, d.month)[1]:
            day = last_day
        else:
            day = min(d.day, last_day)

        return date(year, month, day)

    def dateadd_year(
        self,
        selected_dates: Iterable[date],
        years: int = -1,
    ) -> list[date]:
        """DATEADD-style date shifting."""
        dates = self.calendar.validate(selected_dates)
        shifted = {
            self.shift_year(d, years)
            for d in dates
        }

        return sorted(d for d in shifted if d in self.calendar.date_set)

    def dateadd_month(
        self,
        selected_dates: Iterable[date],
        months: int,
    ) -> list[date]:
        dates = self.calendar.validate(selected_dates)
        shifted = {
            self.shift_month(d, months)
            for d in dates
        }

        return sorted(d for d in shifted if d in self.calendar.date_set)

    def sameperiodlastyear(
        self,
        selected_dates: Iterable[date],
    ) -> Decimal:
        """
        Equivalent to evaluating sales under SAMEPERIODLASTYEAR.
        """
        previous_dates = self.dateadd_year(selected_dates, -1)
        return self.sales(previous_dates)

    def totalytd(
        self,
        selected_dates: Iterable[date],
    ) -> Decimal:
        """Calculate sales from January 1 through the maximum selected date."""
        dates = self.calendar.validate(selected_dates)
        last_date = max(dates)

        start = date(last_date.year, 1, 1)

        return self.sales(
            d for d in self.calendar.date_set
            if start <= d <= last_date
        )

    def totalmtd(
        self,
        selected_dates: Iterable[date],
    ) -> Decimal:
        dates = self.calendar.validate(selected_dates)
        last_date = max(dates)

        start = date(last_date.year, last_date.month, 1)

        return self.sales(
            d for d in self.calendar.date_set
            if start <= d <= last_date
        )

    def totalqtd(
        self,
        selected_dates: Iterable[date],
    ) -> Decimal:
        dates = self.calendar.validate(selected_dates)
        last_date = max(dates)

        first_month = ((last_date.month - 1) // 3) * 3 + 1
        start = date(last_date.year, first_month, 1)

        return self.sales(
            d for d in self.calendar.date_set
            if start <= d <= last_date
        )

    def rolling_period(
        self,
        selected_dates: Iterable[date],
        days: int,
    ) -> Decimal:
        """
        Rolling window ending on the maximum selected date.
        The ending date is included.
        """
        if days <= 0:
            raise ValueError("Rolling period must be positive.")

        dates = self.calendar.validate(selected_dates)
        end = max(dates)
        start = end - timedelta(days=days - 1)

        return self.sales(
            d for d in self.calendar.date_set
            if start <= d <= end
        )

    def period_comparison(
        self,
        selected_dates: Iterable[date],
    ) -> dict[str, Decimal]:
        dates = self.calendar.validate(selected_dates)

        current = self.sales(dates)
        previous = self.sameperiodlastyear(dates)

        difference = current - previous

        percentage = (
            difference / previous * Decimal("100")
            if previous != 0
            else Decimal("0")
        )

        return {
            "current_period": current,
            "previous_year_period": previous,
            "difference": difference,
            "percentage_change": percentage,
        }


def create_sample_data() -> tuple[CalendarTable, list[SalesRecord]]:
    calendar = CalendarTable(
        date(2024, 1, 1),
        date(2026, 12, 31)
    )

    records = [
        SalesRecord(1, date(2024, 1, 15), "Laptop", "North", Decimal("12000")),
        SalesRecord(2, date(2024, 2, 10), "Phone", "South", Decimal("8000")),
        SalesRecord(3, date(2024, 3, 20), "Laptop", "West", Decimal("15000")),
        SalesRecord(4, date(2025, 1, 15), "Laptop", "North", Decimal("16000")),
        SalesRecord(5, date(2025, 2, 10), "Phone", "South", Decimal("11000")),
        SalesRecord(6, date(2025, 3, 20), "Laptop", "West", Decimal("18000")),
        SalesRecord(7, date(2025, 4, 12), "Tablet", "East", Decimal("9000")),
        SalesRecord(8, date(2025, 5, 18), "Phone", "North", Decimal("7000")),
        SalesRecord(9, date(2026, 1, 15), "Laptop", "North", Decimal("21000")),
        SalesRecord(10, date(2026, 2, 10), "Phone", "South", Decimal("14000")),
        SalesRecord(11, date(2026, 3, 20), "Laptop", "West", Decimal("24000")),
        SalesRecord(12, date(2026, 4, 12), "Tablet", "East", Decimal("12000")),
        SalesRecord(13, date(2026, 5, 18), "Phone", "North", Decimal("10000")),
        SalesRecord(14, date(2026, 6, 22), "Laptop", "South", Decimal("19000")),
        SalesRecord(15, date(2026, 7, 14), "Tablet", "West", Decimal("13000")),
        SalesRecord(16, date(2026, 8, 9), "Phone", "East", Decimal("8500")),
        SalesRecord(17, date(2026, 9, 11), "Laptop", "North", Decimal("22000")),
        SalesRecord(18, date(2026, 10, 19), "Tablet", "South", Decimal("11500")),
        SalesRecord(19, date(2026, 11, 5), "Phone", "West", Decimal("9500")),
        SalesRecord(20, date(2026, 11, 15), "Laptop", "East", Decimal("17000")),
    ]

    return calendar, records


def print_report(title: str, values: dict[str, Decimal]) -> None:
    print(f"\n{title}")
    print("-" * 55)

    for label, value in values.items():
        print(f"{label:30} {value:>15,.2f}")


def run_tests(model: SalesModel) -> None:
    assert model.sales([date(2026, 1, 15)]) == Decimal("21000")
    assert model.totalmtd([date(2026, 2, 10)]) == Decimal("14000")
    assert model.totalqtd([date(2026, 2, 10)]) == Decimal("14000")
    assert model.totalytd([date(2026, 2, 10)]) == Decimal("35000")

    assert model.sameperiodlastyear(
        [date(2026, 1, 15)]
    ) == Decimal("16000")

    assert model.rolling_period(
        [date(2026, 11, 15)], 11
    ) == Decimal("17000")

    try:
        model.rolling_period([date(2026, 11, 15)], 0)
        raise AssertionError("Expected invalid rolling period.")
    except ValueError:
        pass

    try:
        model.sales([date(2030, 1, 1)])
        raise AssertionError("Expected invalid calendar date.")
    except ValueError:
        pass

    print("\nAll validation tests passed.")


def main() -> None:
    calendar, records = create_sample_data()
    model = SalesModel(calendar, records)

    selected = [
        date(2026, 11, 1),
        date(2026, 11, 15),
    ]

    print_report(
        "CURRENT PERIOD VS PREVIOUS YEAR",
        model.period_comparison(selected)
    )

    print_report(
        "MONTH-TO-DATE",
        {"MTD Sales": model.totalmtd(selected)}
    )

    print_report(
        "QUARTER-TO-DATE",
        {"QTD Sales": model.totalqtd(selected)}
    )

    print_report(
        "YEAR-TO-DATE",
        {"YTD Sales": model.totalytd(selected)}
    )

    print_report(
        "ROLLING 30-DAY SALES",
        {"Rolling Sales": model.rolling_period(selected, 30)}
    )

    print_report(
        "DATEADD: PREVIOUS MONTH",
        {
            "Previous Month Sales": model.sales(
                model.dateadd_month(selected, -1)
            )
        }
    )

    run_tests(model)


if __name__ == "__main__":
    main()
