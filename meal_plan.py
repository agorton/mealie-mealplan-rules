import os
import requests
import datetime
import logging
from datetime import timezone, timedelta

from dotenv import load_dotenv
from .rules import ExcludeTag, MaxTagPerWeek, NoDuplicatesWithinDays, RecentlyMadeRule, WeekdayEasyRule, IncludeTag
from .selections import RandomSelection, NeglectSelection, SelectionStrategy
from .postselections import SkipDay

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("rules").setLevel(os.getenv("LOG_LEVEL", "INFO"))
logging.getLogger("selections").setLevel(os.getenv("LOG_LEVEL", "INFO"))

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

def fetch_meal_plans_for_recipes(recipes, lookback_weeks=8):
    """
    Fetch meal plans for all recipes.
    Returns a dict mapping recipe names to lists of meal plan events.
    """
    meal_plans_by_recipe = {}
    cutoff_date = datetime.datetime.now(timezone.utc) - timedelta(weeks=lookback_weeks)
    url = f"{API_URL}/households/mealplans"
    
    for recipe in recipes:
        recipe_name = recipe["name"]
        filter_str = f'recipe.name="{recipe_name}"'
        params = {
            "orderDirection": "desc",
            "queryFilter": filter_str,
            "page": 1,
            "perPage": 50,
            "start_date": cutoff_date.date(),
        }
        
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        planned_events = resp.json().get("items", [])
        meal_plans_by_recipe[recipe_name] = planned_events
    
    return meal_plans_by_recipe

def fetch_timeline_events_for_recipes(recipes, lookback_weeks=8):
    """
    Fetch timeline events for all recipes.
    Returns a dict mapping recipe names to lists of timeline events with "made" field.
    """
    timeline_events_by_recipe = {}
    cutoff_date = datetime.datetime.now(timezone.utc) - timedelta(weeks=lookback_weeks)
    url = f"{API_URL}/recipes/timeline/events"
    
    for recipe in recipes:
        recipe_name = recipe["name"]
        filter_str = f'recipe.name="{recipe_name}" AND eventType = "comment" AND createdAt > "{cutoff_date.isoformat()}"'
        params = {
            "orderDirection": "desc",
            "queryFilter": filter_str,
            "page": 1,
            "perPage": 50
        }
        
        resp = requests.get(url, headers=headers, params=params)
        resp.raise_for_status()
        events = resp.json().get("items", [])

        timeline_events_by_recipe[recipe_name] = events
    
    return timeline_events_by_recipe

def generate_meal_plan(recipes, post_selection_rules, start_date=datetime.date.today(), days=7, rules=None, meal_types=None,
                       selection_strategy:SelectionStrategy=RandomSelection,
                       ):
    if meal_types is None:
        meal_types = ["breakfast", "lunch", "dinner"]

    plan = []

    rules = rules or []

    skip_day_rules = [rule.get_day_index() for rule in post_selection_rules if rule.__class__ == SkipDay]

    for i in range(days):
        if skip_day_rules.__contains__(i):
            logger.info(f"Skipping day because of PostSelection SkipDay rule")
            continue

        date = start_date + datetime.timedelta(days=i)

        for meal_type in meal_types:
            candidates, relaxed = apply_rules_with_backoff(rules, plan, recipes, date, meal_type)
            recipe = selection_strategy.select(candidates)
            plan.append({
                "date": date.isoformat(),
                "entryType": meal_type,
                "recipeId": recipe["id"],
                "tags": recipe.get("tags", []),
                "name": recipe["name"],
            })

            log_chosen_recipe(recipe, relaxed, date, meal_type)

    for post_selection_rule in post_selection_rules:
        plan = post_selection_rule.apply(plan)

    return plan

def log_chosen_recipe(recipe, relaxed=None, date=None, meal_type=None):
    recipe_name = recipe.get("name", recipe["id"])
    flat_tags = [d["name"] for d in recipe.get("tags", [])]
    flat_tools = [d["name"] for d in recipe.get("tools", [])]

    log = f"{date} {meal_type}: picked '{recipe_name}' tags: [{', '.join(flat_tags)}] tools: [{', '.join(flat_tools)}]"

    if relaxed:
        logger.info(log + f" (relaxed rules: {relaxed})")
    else:
        logger.info(log)

def push_meal_plan(plan):
    for entry in plan:
        payload =  {
            k: entry[k]
            for k in ("date", "entryType", "recipeId", "title", "text")
            if k in entry and (k != "recipeId" or entry[k] is not None)
        }
        resp = requests.post(f"{API_URL}/households/mealplans", headers=headers, json=payload)
        if resp.status_code not in (200, 201):
            logger.info("Failed:", resp.text)


def next_monday():
    today = datetime.date.today()
    days_ahead = 0 - today.weekday()  # how many days until Sunday
    if days_ahead < 0:  # just in case, though weekday() never > 6
        days_ahead += 7

    return today + datetime.timedelta(days=days_ahead)

def plan_meals(dry_run=os.getenv("DRY_RUN", True)):
    recipes = fetch_recipes()
    logger.info(f"Fetched {len(recipes)} recipes")

    rules = [
        # Hard rules
        ExcludeTag("allergen-nuts", hard=True, name="No Nuts"),
        IncludeTag("dinner", hard=True, priority=2, name="Only Pick Dinners"),

        # Soft rules with priorities
        WeekdayEasyRule(),
        RecentlyMadeRule(),
        NoDuplicatesWithinDays(7, hard=False, priority=1, name="No Duplicates (7d)"),
        MaxTagPerWeek("chicken", max_count=2, hard=False, priority=3, name="Max 2 Chicken/Week"),
        MaxTagPerWeek("indian", max_count=1, hard=False, priority=3, name="Max 1 Indian/Week")
    ]

    post_selection_rules = [
        SkipDay(day="Wednesday", reason="Eating at Perez's"),
    ]

    # Fetch data for NeglectSelection
    lookback_weeks = 1000
    logger.info("Fetching meal plans and timeline events for neglect selection...")
    meal_plans_by_recipe = fetch_meal_plans_for_recipes(recipes, lookback_weeks)
    timeline_events_by_recipe = fetch_timeline_events_for_recipes(recipes, lookback_weeks)
    logger.info("Finished fetching meal plans and timeline events")

    plan = generate_meal_plan(recipes, start_date=next_monday(), days=7, rules=rules, meal_types=["dinner"],
                              selection_strategy=NeglectSelection(
                                  meal_plans_by_recipe=meal_plans_by_recipe,
                                  timeline_events_by_recipe=timeline_events_by_recipe,
                                  lookback_weeks=lookback_weeks
                              ),
                              post_selection_rules = post_selection_rules)
    logger.info(plan)
    if not dry_run == "True":
        push_meal_plan(plan)
    else:
        logger.info("Dry Run. Not Pushing")
    logger.info("Meal plan created.")
    return plan

if __name__ == "__main__":
    plan_meals()
