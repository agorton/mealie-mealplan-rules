from .base import Rule

class IncludeTag(Rule):
    def __init__(self, tag, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag.casefold()

    def _apply(self, plan, candidates):
        return [
            c for c in candidates
            if any(t.get("name").casefold() == self.tag for t in c.get("tags", []))
        ]