from .base import Rule


def compute_effort(recipe):
    # Basic example
    prep_time = recipe.get("prep_time_minutes", 0)
    cook_time = recipe.get("cook_time_minutes", 0)
    steps = len(recipe.get("steps", []))

    # Reduce effort if slow cooker or instant pot
    tool_bonus = 0
    if "slow_cooker" in recipe.get("tools", []):
        tool_bonus -= 2
    if "instant_pot" in recipe.get("tools", []):
        tool_bonus -= 1

    score = (prep_time / 10) + (cook_time / 60) + steps + tool_bonus
    return max(score, 0)  # Ensure non-negative


class WeekdayEasyRule(Rule):
    def __init__(self, max_effort=5, hard=False, priority=5, name="No Difficult Meals on weekdays"):
        super().__init__(hard=hard, priority=priority, name=name)
        self.max_effort = max_effort

    def _apply(self, plan, candidates):
        # Only restrict on weekdays
        if len(plan) < 5:  # 0=Monday, 4=Friday
            filtered = [r for r in candidates if compute_effort(r) <= self.max_effort]
            return filtered
        return candidates
