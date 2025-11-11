import random
import requests
import logging

from datetime import datetime, timedelta, timezone
from .selection_strategy import SelectionStrategy

logger = logging.getLogger(__name__)

class NeglectSelection(SelectionStrategy):
    """
    Soft selection strategy: reduces the chance of picking recipes that
    have been frequently planned but not made recently.
    """

    def __init__(self, api_url, api_token, lookback_weeks=8, min_weight=0.1):
        """
        :param api_url: Base URL of your Mealie instance
        :param api_token: API token with access to recipes/timeline/events
        :param lookback_weeks: Lookback window for neglect calculation
        :param min_weight: Minimum weight for heavily neglected recipes
        """
        self.api_url = api_url.rstrip("/")
        self.headers = {"Authorization": f"Bearer {api_token}"}
        self.lookback_weeks = lookback_weeks
        self.min_weight = min_weight

    def _get_meal_plans(self, recipe_name):
        url = f"{self.api_url}/households/mealplans"
        cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=self.lookback_weeks)
        filter_str = f'recipe.name="{recipe_name}"'
        params = {
            "orderDirection": "desc",
            "queryFilter": filter_str,
            "page": 1,
            "perPage": 50,
            "start_date": cutoff_date.date(),
        }

        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        planned_events = resp.json().get("items", [])
        return planned_events

    def _get_timeline_events(self, recipe_name):
        """
        Query the Mealie API for timeline events for a recipe.
        Returns a list of dicts with keys 'planned' and 'made'.
        """

        filter_str = f'recipe.name="{recipe_name}"'  # no spaces around =
        url = f"{self.api_url}/recipes/timeline/events"
        cutoff_date = datetime.now(timezone.utc) - timedelta(weeks=self.lookback_weeks)

        params = {
            "orderDirection": "desc",
            "queryFilter": filter_str,
            "page": 1,
            "perPage": 50
        }

        resp = requests.get(url, headers=self.headers, params=params)
        resp.raise_for_status()
        events = resp.json().get("items", [])

        # Only consider events within lookback window
        recent_events = []
        for e in events:
            event_date_str = e.get("createdAt")
            if not event_date_str:
                continue
            try:
                event_date = datetime.fromisoformat(event_date_str.replace("Z", "+00:00"))
            except Exception:
                continue
            if event_date < cutoff_date:
                continue
            made = not e.get("subject").__contains__("Created".casefold())
            recent_events.append({"made": made})
        return recent_events

    def calculate_weight(self, recipe):
        """
        Compute weight based on neglect: planned-but-not-made events
        reduce weight toward min_weight.
        """
        events = self._get_timeline_events(recipe["name"])
        planned_events = self._get_meal_plans(recipe["name"])

        if not events:
            return 1.0  # never planned → full weight

        made_count = len(events)
        planned_count = len(planned_events)

        neglect_count = planned_count - made_count
        if planned_count == 0 or neglect_count <= 0:
            return 1.0  # no neglect → full weight

        # Linear scaling: heavily neglected recipes get min_weight
        neglect_fraction = neglect_count / planned_count
        weight = 1.0 - neglect_fraction * (1.0 - self.min_weight)

        logger.debug(f"Calculated weight for {recipe['name']}: planned: {planned_count}, made: {made_count}, neglect: {neglect_count} weight:{max(weight, self.min_weight)}")

        return max(weight, self.min_weight)

    def select(self, candidates, n=1):
        """
        Select `n` candidates using weighted random choice based on neglect.
        """
        if not candidates:
            return None if n == 1 else []

        weights = [self.calculate_weight(r) for r in candidates]

        if n == 1:
            return random.choices(candidates, weights=weights, k=1)[0]
        return random.choices(candidates, weights=weights, k=n)
