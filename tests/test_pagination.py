"""page_count: ceil-division behaviour."""
from app import page_count


def test_zero_rows_is_one_page():
    assert page_count(0, 20) == 1


def test_exact_page_boundary():
    assert page_count(20, 20) == 1
    assert page_count(40, 20) == 2


def test_one_over_boundary_adds_page():
    assert page_count(21, 20) == 2
    assert page_count(41, 20) == 3


def test_large_totals():
    assert page_count(399, 20) == 20
    assert page_count(400, 20) == 20
    assert page_count(401, 20) == 21
