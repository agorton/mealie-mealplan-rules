import logging

logger = logging.getLogger(__name__)

class Rule:

    def __init__(self, hard=False, priority=5, name=None):
        """
        :param hard: True if this rule can never be broken
        :param priority: Lower = more important (only applies to soft rules)
        :param name: Friendly name for logging
        """
        self.hard = hard
        self.priority = priority
        self.name = name or self.__class__.__name__

    def apply(self, plan, candidates):
        """Wrap the subclass _apply with before/after logging."""
        before = [r.get("name") for r in candidates]

        after = self._apply(plan, candidates)  # subclass implements _apply

        after_names = [r.get("name") for r in after]
        removed = set(before) - set(after_names)
        if removed:
            logger.debug(f"[{self.name}] removed recipes: {removed}")
        else:
            logger.debug(f"[{self.name}] no recipes removed")

        return after

    def _apply(self, plan, candidates):
        """
        Subclasses should override this method instead of apply().
        """
        raise NotImplementedError
