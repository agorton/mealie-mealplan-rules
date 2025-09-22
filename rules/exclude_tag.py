from .base import Rule

class ExcludeTag(Rule):
    def __init__(self, tag, **kwargs):
        super().__init__(**kwargs)
        self.tag = tag

    def apply(self, plan, candidates):
        return [c for c in candidates if self.tag not in c.get("tags", [])]
