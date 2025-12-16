import random
import logging

from .selection_strategy import SelectionStrategy

logger = logging.getLogger(__name__)

class NeglectSelection(SelectionStrategy):
    """
    Soft selection strategy: reduces the chance of picking recipes that
    have been frequently planned but not made recently.
    """

    def __init__(self, meal_plans_by_recipe, timeline_events_by_recipe, lookback_weeks=8, min_weight=0.1):
        """
        :param meal_plans_by_recipe: Dict mapping recipe names to lists of meal plan events
        :param timeline_events_by_recipe: Dict mapping recipe names to lists of timeline events with "made" field
        :param lookback_weeks: Lookback window for neglect calculation (for reference, data should already be filtered)
        :param min_weight: Minimum weight for heavily neglected recipes
        """
        self.meal_plans_by_recipe = meal_plans_by_recipe
        self.timeline_events_by_recipe = timeline_events_by_recipe
        self.lookback_weeks = lookback_weeks
        self.min_weight = min_weight

    def calculate_weight(self, recipe):
        """
        Compute weight based on neglect: planned-but-not-made events
        reduce weight toward min_weight.
        """
        recipe_name = recipe["name"]
        times_made = self.timeline_events_by_recipe.get(recipe_name, [])
        planned_events = self.meal_plans_by_recipe.get(recipe_name, [])

        if not planned_events:
            return 1.0  # never planned → full weight

        made_count = len(times_made)
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
