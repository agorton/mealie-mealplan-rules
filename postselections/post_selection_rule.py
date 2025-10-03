import logging

logger = logging.getLogger(__name__)

class PostSelectionRule:
    def __init__(self, name=None):
        self.name = name

    def apply(self, plan):
        """Wrap the subclass _apply with before/after logging."""
        after = self._apply(plan)  # subclass implements _apply

        logger.debug(f"After apply: {after}")

        return after

    def _apply(self, plan):
        """Apply the rule to the plan."""
        return NotImplemented