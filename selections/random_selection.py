import random

from .selection_strategy import SelectionStrategy

class RandomSelection(SelectionStrategy):
    def select(self, candidates, n=1):
        return random.sample(candidates, k=n) if candidates else []
