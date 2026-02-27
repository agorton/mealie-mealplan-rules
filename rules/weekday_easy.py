from .base import Rule
from pytimeparse.timeparse import timeparse

def time_to_minutes(text:str) -> float:
    if text is int:
        return 0
    seconds = timeparse(text)
    if seconds is None:
        return 0
    return seconds / 60

def compute_effort(recipe):
    # Basic example
    total_time = time_to_minutes(recipe.get("totalTime", 0))
    steps = len(recipe.get("recipeInstructions", []))

    # Reduce effort if slow cooker or instant pot
    tool_bonus = 0
    if "slow_cooker" in recipe.get("tools", []):
        tool_bonus -= 2

    score = (total_time / 60) + steps + tool_bonus
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
