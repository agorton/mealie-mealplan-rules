from .base import Rule

class MaxTagPerWeek(Rule):
    def __init__(self, tag, max_count=1, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag
        self.max_count = max_count

    def _apply(self, plan, candidates):
        """
        Filters out candidates with the tag if the tag has already appeared
        max_count times in the last 7 plan entries.
        """
        # Count occurrences of the tag in last 7 plan entries
        count = sum(
            1 for e in plan[-7:]
            if any(t.get("name") == self.tag for t in e.get("tags", []))
        )

        if count >= self.max_count:
            # Remove candidates containing this tag
            return [
                c for c in candidates
                if all(t.get("name") != self.tag for t in c.get("tags", []))
            ]
        return candidates