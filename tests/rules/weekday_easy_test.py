import pytest
from rules.weekday_easy import compute_effort, WeekdayEasyRule


@pytest.mark.parametrize(
    "recipe,expected",
    [
        ({"prep_time_minutes": 10, "cook_time_minutes": 0, "steps": []}, 1),   # 10min prep = score 1
        ({"prep_time_minutes": 0, "cook_time_minutes": 60, "steps": []}, 1),   # 60min cook = score 1
        ({"prep_time_minutes": 20, "cook_time_minutes": 30, "steps": ["a","b"]}, 2+0.5+2),
        ({"prep_time_minutes": 0, "cook_time_minutes": 120, "steps": [], "tools": ["slow_cooker"]}, 0), # Effort reduced, floored at 0
        ({"prep_time_minutes": 15, "cook_time_minutes": 30, "steps": ["a"], "tools": ["instant_pot"]}, 1.5+0.5+1-1),
    ]
)
def test_compute_effort(recipe, expected):
    assert compute_effort(recipe) == pytest.approx(expected)


def test_weekday_easy_rule_filters_easy_recipes():
    candidates = [
        {"name": "Easy salad", "prep_time_minutes": 5, "cook_time_minutes": 0, "steps": ["a"]},
        {"name": "Hard roast", "prep_time_minutes": 60, "cook_time_minutes": 120, "steps": ["a","b","c","d"]},
    ]
    rule = WeekdayEasyRule(max_effort=5)
    plan = [1, 2, 3, 4]  # len=4 => treated as weekday

    filtered = rule._apply(plan, candidates)

    assert any(r["name"] == "Easy salad" for r in filtered)
    assert all(compute_effort(r) <= 5 for r in filtered)


def test_weekday_easy_rule_does_not_filter_weekends():
    candidates = [
        {"name": "Hard roast", "prep_time_minutes": 60, "cook_time_minutes": 120, "steps": ["a","b","c","d"]},
    ]
    rule = WeekdayEasyRule(max_effort=5)
    plan = [1, 2, 3, 4, 5]  # len=5 => weekend or later

    filtered = rule._apply(plan, candidates)

    # Should not filter anything
    assert filtered == candidates


def test_weekday_easy_rule_all_filtered_out():
    candidates = [
        {"name": "Hard roast", "prep_time_minutes": 120, "cook_time_minutes": 300, "steps": ["a","b","c","d","e"]},
    ]
    rule = WeekdayEasyRule(max_effort=2)
    plan = [1]  # weekday

    filtered = rule._apply(plan, candidates)

    assert filtered == []  # Nothing meets the criteria
