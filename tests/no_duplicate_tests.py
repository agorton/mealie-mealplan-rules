import pytest
from rules.no_duplicates import NoDuplicatesWithinDays

def test_no_duplicates_within_days():
    # Sample plan: last 7 days
    plan = [
        {"recipeId": "r1", "name": "Pizza"},
        {"recipeId": "r2", "name": "Salad"},
        {"recipeId": "r3", "name": "Soup"},
        {"recipeId": "r4", "name": "Steak"},
        {"recipeId": "r5", "name": "Pasta"},
        {"recipeId": "r6", "name": "Burger"},
        {"recipeId": "r7", "name": "Sandwich"},
    ]

    # Sample candidates
    candidates = [
        {"id": "r1", "name": "Pizza"},        # duplicate
        {"id": "r2", "name": "Salad"},        # duplicate
        {"id": "r8", "name": "Omelette"},     # new
        {"id": "r9", "name": "Curry"},        # new
    ]

    # Rule: no duplicates within last 7 entries
    rule = NoDuplicatesWithinDays(days=7)

    filtered = rule.apply(plan, candidates)

    filtered_names = [r["name"] for r in filtered]

    # Only recipes not in recent plan should remain
    assert "Omelette" in filtered_names
    assert "Curry" in filtered_names
    assert "Pizza" not in filtered_names
    assert "Salad" not in filtered_names

    # Check that the filtered list length is correct
    assert len(filtered) == 2
