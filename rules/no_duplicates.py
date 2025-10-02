from .base import Rule

class NoDuplicatesWithinDays(Rule):
    def __init__(self, days=7, **kwargs):
        super().__init__(**kwargs)
        self.days = days

    def _apply(self, plan, candidates):
        recent_ids = {e["recipeId"] for e in plan[-self.days:]}
        return [c for c in candidates if c["id"] not in recent_ids]
