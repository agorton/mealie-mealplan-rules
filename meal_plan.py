import os
import datetime
import logging
import requests
from datetime import timezone, timedelta

from dotenv import load_dotenv
from .rules import ExcludeTag, MaxTagPerWeek, NoDuplicatesWithinDays, RecentlyMadeRule, WeekdayEasyRule, IncludeTag
from .selections import RandomSelection, NeglectSelection, SelectionStrategy
from .postselections import SkipDay

# Import the MealieApiService from the main services package
from services.mealie_api_service import MealieApiService

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

logging.getLogger("rules").setLevel(os.getenv("LOG_LEVEL", "INFO"))
logging.getLogger("selections").setLevel(os.getenv("LOG_LEVEL", "INFO"))

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


def generate_meal_plan(recipes, post_selection_rules, start_date=datetime.date.today(), days=7, rules=None, meal_types=None,
                       selection_strategy:SelectionStrategy=RandomSelection,
                       ):
    if meal_types is None:
        meal_types = ["breakfast", "lunch", "dinner"]

    plan = []

    rules = rules or []

    for i in range(days):
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

def push_meal_plan(plan, mealie_service: MealieApiService):
    """Push meal plan to Mealie using the provided service.
    
    Args:
        plan: The meal plan to push
        mealie_service: MealieApiService instance for API interactions
    """
    for entry in plan:
        payload =  {
            k: entry[k]
            for k in ("date", "entryType", "recipeId", "title", "text")
            if k in entry and (k != "recipeId" or entry[k] is not None)
        }
        url = f"{mealie_service.mealie_url}/api/households/mealplans"
        headers = mealie_service._auth_headers()
        
        resp = requests.post(url, headers=headers, json=payload)
        if resp.status_code not in (200, 201):
            logger.info("Failed:", resp.text)


def next_monday():
    today = datetime.date.today()
    days_ahead = 0 - today.weekday()  # how many days until Sunday
    if days_ahead < 0:  # just in case, though weekday() never > 6
        days_ahead += 7

    return today + datetime.timedelta(days=days_ahead)

def plan_meals(mealie_service: MealieApiService = None, dry_run=os.getenv("DRY_RUN", True)):
    """
    Generate a meal plan using the provided Mealie service.
    
    Args:
        mealie_service: MealieApiService instance for API interactions
        dry_run: Whether to skip pushing the plan to Mealie
    
    Returns:
        Generated meal plan
    """
    # Use existing service or create a fallback (for backward compatibility)
    if mealie_service is None:
        # For backward compatibility, create a service from environment variables
        import os
        from dotenv import load_dotenv
        load_dotenv()
        
        mealie_url = os.getenv("MEALIE_SERVER")
        mealie_token = os.getenv("MEALIE_TOKEN")
        if mealie_url and mealie_token:
            mealie_service = MealieApiService(mealie_url, mealie_token)
        else:
            raise ValueError("Mealie service not provided and environment variables not available")
    
    recipes = mealie_service.get_all_recipes()
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
        SkipDay(day="Thursday", reason="Leftovers"),
    ]

    # Fetch data for NeglectSelection
    lookback_weeks = 1000
    logger.info("Fetching meal plans and timeline events for neglect selection...")
    meal_plans_by_recipe = mealie_service.get_meal_plans_for_recipes(recipes, lookback_weeks)
    timeline_events_by_recipe = mealie_service.get_timeline_events_for_recipes(recipes, lookback_weeks)
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
        push_meal_plan(plan, mealie_service)
    else:
        logger.info("Dry Run. Not Pushing")
    logger.info("Meal plan created.")
    return plan

if __name__ == "__main__":
    plan_meals()
