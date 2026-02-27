import pytest
from rules.weekday_easy import compute_effort, WeekdayEasyRule


@pytest.mark.parametrize(
    "recipe,expected",
    [
        ({ "totalTime": "", "steps": []}, 0),   # 10min prep = score 1
        ({ "totalTime": "1 hour", "steps": []}, 1),   # 60min cook = score 1
        ({ "totalTime": "30 minutes", "steps": ["a","b"]}, 0.5),
        ({ "totalTime": "2 hours", "steps": [], "tools": ["slow_cooker"]}, 0), # Effort reduced, floored at 0
    ]
)
def test_compute_effort(recipe, expected):
    assert compute_effort(recipe) == pytest.approx(expected)


def test_weekday_easy_rule_filters_easy_recipes():
    candidates = [
        {"name": "Easy salad",  "totalTime": "", "steps": ["a"]},
        {"name": "Hard roast",  "totalTime": "2 hours", "steps": ["a","b","c","d"]},
    ]
    rule = WeekdayEasyRule(max_effort=5)
    plan = [1, 2, 3, 4]  # len=4 => treated as weekday

    filtered = rule._apply(plan, candidates)

    assert any(r["name"] == "Easy salad" for r in filtered)
    assert all(compute_effort(r) <= 5 for r in filtered)


def test_weekday_easy_rule_does_not_filter_weekends():
    candidates = [
        {"name": "Hard roast",  "totalTime": "2 hours", "steps": ["a","b","c","d"]},
    ]
    rule = WeekdayEasyRule(max_effort=5)
    plan = [1, 2, 3, 4, 5]  # len=5 => weekend or later

    filtered = rule._apply(plan, candidates)

    # Should not filter anything
    assert filtered == candidates


def test_weekday_easy_rule_all_filtered_out():
    candidates = [
        {"name": "Hard roast",  "totalTime": "5 hours", "steps": ["a","b","c","d","e"]},
    ]
    rule = WeekdayEasyRule(max_effort=2)
    plan = [1]  # weekday

    filtered = rule._apply(plan, candidates)

    assert filtered == []  # Nothing meets the criteria
