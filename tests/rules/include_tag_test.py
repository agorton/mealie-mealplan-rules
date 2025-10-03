import pytest
from rules.include_tag import IncludeTag

def test_include_tag_rule():
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
    rule = IncludeTag(tag="vegetarian")

    filtered = rule.apply(plan, candidates)

    # Check that only recipes without 'vegetarian' tag remain
    filtered_names = [r["name"] for r in filtered]
    assert "Pizza" not in filtered_names
    assert "Steak" not in filtered_names
    assert "Salad" in filtered_names
    assert "Soup" in filtered_names

    # Check that the filtered list length is correct
    assert len(filtered) == 2
