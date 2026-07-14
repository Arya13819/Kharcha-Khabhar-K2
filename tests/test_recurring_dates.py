"""advance_due_date: month-end and leap-year edge cases."""
from datetime import date

from recurring import advance_due_date


def test_weekly_adds_seven_days():
    assert advance_due_date(date(2026, 7, 10), "Weekly") == date(2026, 7, 17)


def test_monthly_simple():
    assert advance_due_date(date(2026, 7, 15), "Monthly") == date(2026, 8, 15)


def test_monthly_jan_31_clamps_to_feb_end():
    assert advance_due_date(date(2026, 1, 31), "Monthly") == date(2026, 2, 28)


def test_monthly_jan_31_leap_year():
    assert advance_due_date(date(2028, 1, 31), "Monthly") == date(2028, 2, 29)


def test_monthly_31_to_30_day_month():
    assert advance_due_date(date(2026, 3, 31), "Monthly") == date(2026, 4, 30)


def test_monthly_december_rolls_year():
    assert advance_due_date(date(2026, 12, 15), "Monthly") == date(2027, 1, 15)


def test_yearly_simple():
    assert advance_due_date(date(2026, 7, 10), "Yearly") == date(2027, 7, 10)


def test_yearly_from_leap_day():
    assert advance_due_date(date(2028, 2, 29), "Yearly") == date(2029, 2, 28)
