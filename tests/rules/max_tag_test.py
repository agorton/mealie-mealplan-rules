import pytest
from rules.max_tag import MaxTagPerWeek

def test_max_tag_per_week_rule():
    # Sample plan: last 7 meals
    plan = [
        {"name": "Meal1", "tags": [{"name": "vegetarian"}]},
        {"name": "Meal2", "tags": [{"name": "vegetarian"}]},
        {"name": "Meal3", "tags": [{"name": "dinner"}]},
        {"name": "Meal4", "tags": [{"name": "starter"}]},
        {"name": "Meal5", "tags": [{"name": "vegetarian"}]},
        {"name": "Meal6", "tags": [{"name": "meat"}]},
        {"name": "Meal7", "tags": [{"name": "vegetarian"}]},
    ]

    # Sample candidates
    candidates = [
        {"name": "Salad", "tags": [{"name": "Vegetarian"}]},
        {"name": "Salad2", "tags": [{"name": "vegetarian"}]},
        {"name": "Steak", "tags": [{"name": "meat"}]},
        {"name": "Soup", "tags": [{"name": "starter"}]},
    ]

    # Max 1 vegetarian per week
    rule = MaxTagPerWeek(tag="vegetarian", max_count=1)

    filtered = rule.apply(plan, candidates)

    # Check that vegetarian meals are removed because the plan already has >= 1 vegetarian
    filtered_names = [r["name"] for r in filtered]
    assert "Salad" not in filtered_names
    assert "Steak" in filtered_names
    assert "Soup" in filtered_names

    # Check that the filtered list length is correct
    assert len(filtered) == 2
