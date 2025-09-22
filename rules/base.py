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
        """Return a filtered list of candidates"""
        return candidates
