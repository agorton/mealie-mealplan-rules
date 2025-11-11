
from .post_selection_rule import PostSelectionRule

DAY_NAME_TO_INDEX = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}

def day_name_to_index(name: str) -> int:
    """Convert a day name (case-insensitive) into a 0-based weekday index."""
    try:
        return DAY_NAME_TO_INDEX[name.strip().lower()]
    except KeyError:
        raise ValueError(f"Invalid day name: {name}")

class SkipDay(PostSelectionRule):
    def __init__(self, day, reason, **kwargs):
        super().__init__(**kwargs)
        self.day = day
        self.reason = reason

    def _apply(self, plan):
        day_index = day_name_to_index(self.day)
        plan[day_index] = {
                "date": plan[day_index]["date"],
                "entryType": plan[day_index]["entryType"],
                "title": self.reason,
                "text": "",
            }
        return plan

    def get_day_index(self):
        return DAY_NAME_TO_INDEX[self.day.strip().lower()]