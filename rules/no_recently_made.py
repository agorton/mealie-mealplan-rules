from datetime import datetime, timedelta
from .base import Rule

class RecentlyMadeRule(Rule):
    """
    Excludes recipes that have been made within the last X days.
    """

    def __init__(self, days=14, hard=False, priority=1, name="No Recently Made Meals in the last 2 weeks"):
        name = name or f"No repeats within {days} days"
        super().__init__(hard=hard, priority=priority, name=name)
        self.days = days

    def _apply(self, plan, candidates):
        cutoff = datetime.now() - timedelta(days=self.days)
        filtered = []

        for recipe in candidates:
            last_made = recipe.get("lastMade")
            if last_made:
                try:
                    # Mealie lastMade is an ISO date string like "2025-09-01T00:00:00Z"
                    last_made_dt = datetime.fromisoformat(last_made.replace("Z", "+00:00"))
                    if last_made_dt >= cutoff:
                        continue  # exclude if too recent
                except Exception:
                    # if parsing fails, don't exclude
                    pass
            filtered.append(recipe)

        return filtered
