import pytest
from selections.neglect_selection import NeglectSelection

def test_calculate_weight():
    # Fake recipe candidates
    pizza = {"name": "Pizza"}
    salad = {"name": "Salad"}
    soup = {"name": "Soup"}

    # Prepare pre-fetched data
    meal_plans_by_recipe = {
        "Pizza": [{"id": 1}, {"id": 2}, {"id": 3}],  # Planned 3 times
        "Salad": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],  # Planned 5 times
        "Soup": []  # Never planned
    }
    
    timeline_events_by_recipe = {
        "Pizza": [],  # made 0 → heavily neglected
        "Salad": [{"id": 1}, {"id": 2}, {"id": 3}, {"id": 4}, {"id": 5}],  # Planned 5 times, made 5 → fully liked
        "Soup": []
    }

    # Instantiate strategy with pre-fetched data
    strategy = NeglectSelection(
        meal_plans_by_recipe=meal_plans_by_recipe,
        timeline_events_by_recipe=timeline_events_by_recipe,
        lookback_weeks=4,
        min_weight=0.1
    )

    # Test weight calculations
    pizza_weight = strategy.calculate_weight(pizza)
    salad_weight = strategy.calculate_weight(salad)
    soup_weight = strategy.calculate_weight(soup)

    assert pizza_weight == strategy.min_weight, "Heavily neglected recipe should get min_weight"
    assert salad_weight == 1.0, "Recipe always made should get full weight"
    assert soup_weight == 1.0, "Recipe never planned should get full weight"


def test_select(monkeypatch):
    candidates = [
        {"name": "Pizza"},
        {"name": "Salad"},
    ]
    
    # Instantiate with empty data since we're mocking calculate_weight
    strategy = NeglectSelection(
        meal_plans_by_recipe={},
        timeline_events_by_recipe={},
        min_weight=0.1
    )

    # Mock calculate_weight to fixed values
    weights = {"Pizza": 0.1, "Salad": 1.0}
    monkeypatch.setattr(strategy, "calculate_weight", lambda r: weights[r["name"]])

    # Mock random.choices to return the first candidate to simplify test
    import random
    def fake_choices(population, weights, k):
        assert population == candidates
        assert weights == [0.1, 1.0]
        return [population[1]] * k  # always pick Salad
    monkeypatch.setattr(random, "choices", fake_choices)

    selected = strategy.select(candidates, n=1)
    assert selected == candidates[1], "Should pick candidate with higher weight"

    selected_two = strategy.select(candidates, n=2)
    assert selected_two == [candidates[1], candidates[1]], "Should return list with correct length"
