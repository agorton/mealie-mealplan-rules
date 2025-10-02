import pytest
from datetime import datetime, timedelta
from rules.no_recently_made import RecentlyMadeRule

def test_recently_made_rule_filters_recent():
    now = datetime.now()

    candidates = [
        # Made yesterday → should be excluded
        {"id": "r1", "name": "Pizza", "lastMade": (now - timedelta(days=1)).isoformat()},
        # Made 20 days ago → should be included
        {"id": "r2", "name": "Salad", "lastMade": (now - timedelta(days=20)).isoformat()},
        # Never made → should be included
        {"id": "r3", "name": "Soup"},
        # Invalid lastMade → should be included (parsing fails gracefully)
        {"id": "r4", "name": "Burger", "lastMade": "invalid-date"},
    ]

    rule = RecentlyMadeRule(days=14)

    filtered = rule.apply([], candidates)

    ids = [c["id"] for c in filtered]

    assert "r1" not in ids, "Recently made recipe (1 day ago) should be excluded"
    assert "r2" in ids, "Recipe made 20 days ago should be included"
    assert "r3" in ids, "Recipe with no lastMade should be included"
    assert "r4" in ids, "Recipe with invalid lastMade should be included"
    assert len(filtered) == 3
