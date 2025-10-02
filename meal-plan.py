import os
import requests
import random
import datetime

from dotenv import load_dotenv
from rules import ExcludeTag, MaxTagPerWeek, NoDuplicatesWithinDays, RecentlyMadeRule

load_dotenv()

API_URL = os.getenv("MEALIE_SERVER") + "/api"
API_TOKEN =  os.getenv("MEALIE_TOKEN")

headers = {
    "Authorization": f"Bearer {API_TOKEN}",
    "Content-Type": "application/json"
}

def apply_rules_with_backoff(rules, plan, candidates, date, meal_type):
    """Apply rules, relaxing soft ones if needed. Returns candidates and relaxed rules."""
    hard_rules = [r for r in rules if r.hard]
    soft_rules = sorted([r for r in rules if not r.hard],
                        key=lambda r: r.priority)

    # Apply all hard rules (non-negotiable)
    filtered = candidates[:]
    for rule in hard_rules:
        filtered = rule.apply(plan, filtered)
    if not filtered:
        raise ValueError(f"No candidates left after applying hard rules ({date} {meal_type})")

    # Apply soft rules with backoff
    for drop_count in range(len(soft_rules) + 1):
        filtered_soft = filtered[:]
        active_rules = soft_rules[drop_count:]  # progressively drop lower priority
        for rule in active_rules:
            filtered_soft = rule.apply(plan, filtered_soft)
            if not filtered_soft:
                break
        if filtered_soft:
            relaxed = [r.name for r in soft_rules[:drop_count]]
            return filtered_soft, relaxed

    # If everything fails, just return hard-rule set
    return filtered, [r.name for r in soft_rules]


# -------------------------------
# Core planner
# -------------------------------

def fetch_recipes():
    recipes = []
    url = f"{API_URL}/recipes"
    page = 1
    while True:
        resp = requests.get(url, headers=headers, params={"page": page, "perPage": 50})
        resp.raise_for_status()
        data = resp.json()
        recipes.extend(data["items"])
        if not data["items"]:
            break
        page += 1
    return recipes


def generate_meal_plan(recipes, days=7, rules=None, meal_types=None):
    if meal_types is None:
        meal_types = ["breakfast", "lunch", "dinner"]

    plan = []
    today = datetime.date.today()

    rules = rules or []

    for i in range(days):
        date = today + datetime.timedelta(days=i)

        for meal_type in meal_types:
            candidates, relaxed = apply_rules_with_backoff(rules, plan, recipes, date, meal_type)
            recipe = random.choice(candidates)
            plan.append({
                "date": date.isoformat(),
                "entryType": "recipe",
                "recipeId": recipe["id"],
                "tags": recipe.get("tags", []),
                "mealType": meal_type
            })

            # Logging
            recipe_name = recipe.get("name", recipe["id"])
            flat_tags = [d["name"] for d in recipe.get("tags", [])]

            if relaxed:
                print(f"{date} {meal_type}: picked '{recipe_name}' tags: {', '.join(flat_tags)} (relaxed rules: {relaxed})")
            else:
                print(f"{date} {meal_type}: picked '{recipe_name}' tags: {', '.join(flat_tags)}")

    return plan

def push_meal_plan(plan):
    for entry in plan:
        payload = {
            "date": entry["date"],
            "entryType": "recipe",
            "recipeId": entry["recipeId"]
        }
        resp = requests.post(f"{API_URL}/meal-plans/", headers=headers, json=payload)
        if resp.status_code not in (200, 201):
            print("Failed:", resp.text)


# -------------------------------
# Example usage
# -------------------------------

def main():
    recipes = fetch_recipes()
    print(f"Fetched {len(recipes)} recipes")

    rules = [
        # Hard rules
        ExcludeTag("allergen-nuts", hard=True, name="No Nuts"),
        ExcludeTag("dessert", hard=True, priority=2, name="No Dessert"),
        ExcludeTag("side", hard=True, priority=2, name="No Sides"),

        # Soft rules with priorities
        RecentlyMadeRule(),
        NoDuplicatesWithinDays(7, hard=False, priority=1, name="No Duplicates (7d)"),
        MaxTagPerWeek("chicken", max_count=2, hard=False, priority=3, name="Max 2 Chicken/Week"),
    ]

    plan = generate_meal_plan(recipes, days=7, rules=rules, meal_types=["dinner"])
    print("I would push here but i'm testing.")
    print(plan)
    # push_meal_plan(plan)
    print("Meal plan created.")

if __name__ == "__main__":
    main()
