"""compute_report_range: every preset + edge cases."""
from datetime import date

from app import compute_report_range


TODAY = date(2026, 7, 13)  # a Monday


def test_this_month():
    assert compute_report_range("this_month", TODAY) == ("2026-07-01", "2026-07-13")


def test_this_week_starts_monday():
    assert compute_report_range("this_week", TODAY) == ("2026-07-13", "2026-07-13")
    # Mid-week: Wednesday should reach back to Monday
    assert compute_report_range("this_week", date(2026, 7, 15)) == ("2026-07-13", "2026-07-15")


def test_last_month_full_span():
    assert compute_report_range("last_month", TODAY) == ("2026-06-01", "2026-06-30")


def test_last_month_handles_february():
    assert compute_report_range("last_month", date(2026, 3, 5)) == ("2026-02-01", "2026-02-28")


def test_last_3_months_crosses_year_boundary():
    assert compute_report_range("last_3_months", date(2026, 1, 15)) == ("2025-11-01", "2026-01-15")


def test_this_year():
    assert compute_report_range("this_year", TODAY) == ("2026-01-01", "2026-07-13")


def test_custom_passes_dates_through():
    assert compute_report_range("custom", TODAY, "2026-05-01", "2026-05-31") == ("2026-05-01", "2026-05-31")


def test_custom_missing_dates_returns_none():
    assert compute_report_range("custom", TODAY, None, "2026-05-31") is None
    assert compute_report_range("custom", TODAY, "2026-05-01", "") is None


def test_unknown_range_defaults_to_this_month():
    assert compute_report_range("garbage", TODAY) == ("2026-07-01", "2026-07-13")
