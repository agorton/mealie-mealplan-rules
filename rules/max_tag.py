from .base import Rule

class MaxTagPerWeek(Rule):
    def __init__(self, tag, max_count=1, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag
        self.max_count = max_count

    def apply(self, plan, candidates):
        count = sum(1 for e in plan[-7:] if self.tag in e.get("tags", []))
        if count >= self.max_count:
            return [c for c in candidates if self.tag not in c.get("tags", [])]
        return candidates
