import pytest
from rules.exclude_tag import ExcludeTag

def test_exclude_tag_rule():
    # Sample recipes
    candidates = [
        {"name": "Pizza", "tags": [{"name": "italian"}, {"name": "dinner"}]},
        {"name": "Salad", "tags": [{"name": "vegetarian"}, {"name": "starter"}]},
        {"name": "Soup", "tags": [{"name": "starter"}, {"name": "vegetarian"}]},
        {"name": "Steak", "tags": [{"name": "dinner"}, {"name": "meat"}]}
    ]

    # Plan can be empty for this test
    plan = []

    # Exclude recipes tagged 'vegetarian'
    rule = ExcludeTag(tag="vegetarian")

    filtered = rule.apply(plan, candidates)

    # Check that only recipes without 'vegetarian' tag remain
    filtered_names = [r["name"] for r in filtered]
    assert "Pizza" in filtered_names
    assert "Steak" in filtered_names
    assert "Salad" not in filtered_names
    assert "Soup" not in filtered_names

    # Check that the filtered list length is correct
    assert len(filtered) == 2
