import random

from selections import SelectionStrategy

class RandomSelection(SelectionStrategy):
    def select(self, candidates, n=1):
        return random.sample(candidates, k=n) if candidates else []
