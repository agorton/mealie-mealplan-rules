import pytest
from selections.neglect_selection import NeglectSelection

#  TODO: make this simpler. Load the full timeline to a date, Load the mealplans to a date and pass them in, instead of calling the API in the rule.
@pytest.mark.skip(reason="trying to make an actual call.")
def test_calculate_weight(monkeypatch):
    # Fake recipe candidates
    pizza = {"name": "Pizza"}
    salad = {"name": "Salad"}
    soup = {"name": "Soup"}

    # Instantiate strategy (API details are irrelevant, we'll monkeypatch)
    strategy = NeglectSelection(api_url="http://fake", api_token="fake", lookback_weeks=4, min_weight=0.1)

    # Mock _get_timeline_events to simulate planned vs made
    def fake_get_events(recipe):
        if recipe == "Pizza":
            # Planned 3 times, made 0 → heavily neglected
            return [{"made": False}, {"made": False}, {"made": False}]
        if recipe == "Salad":
            # Planned 5 times, made 5 → fully liked
            return [{"made": True}] * 5
        if recipe == "Soup":
            # Never planned
            return []
    monkeypatch.setattr(strategy, "_get_timeline_events", lambda r: fake_get_events(r))

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
    strategy = NeglectSelection(api_url="http://fake", api_token="fake", min_weight=0.1)

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
