import logging
import os
from datetime import datetime

import requests
from openai import OpenAI
from dotenv import load_dotenv
from .classifications import Classifications

# ==============================
# CONFIGURATION
# ==============================

load_dotenv()

logger = logging.getLogger(__name__)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

MEALIE_URL = os.getenv("MEALIE_SERVER") + "/api"
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Which model to use
OPENAI_MODEL = "gpt-4o-mini"

# ==============================
# INITIALIZE CLIENTS
# ==============================

client = OpenAI(api_key=OPENAI_API_KEY)
headers = {"Authorization": f"Bearer {MEALIE_TOKEN}"}


PROMPT_SYSTEM = f"""
You are a recipe classifier. 
Given a recipe's name, ingredients, and instructions, classify it into:
- Cuisine: one of {Classifications.CUISINES}
- Main carb: one of {Classifications.CARBS}
- Main protein: one or many of {Classifications.PROTEINS}
- Meal time: one of {Classifications.MEALTIME}

Always return JSON in this format:
{{
  "cuisine": "...",
  "main_carb": "...",
  "main_protein": ["..."]
  "meal_time": "..."
}}
"""

# ==============================
# FUNCTIONS
# ==============================

def fetch_tags():
    """Fetch all tags from Mealie and return a lookup by lowercase name."""
    url = f"{MEALIE_URL}/organizers/tags"
    tags = {}
    page = 1
    while True:
        r = requests.get(f"{url}?page={page}&perPage=100", headers=headers)
        r.raise_for_status()
        data = r.json()
        items = data.get("items", [])
        if not items:
            break
        for t in items:
            tags[t["name"].lower()] = t
        page += 1
    return tags

def fetch_recipes_since_first_of_month():
    url = f"{MEALIE_URL}/recipes?queryFilter=createdAt>=\"{datetime.today().replace(day=1)}\""
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.json()["items"]  # Mealie paginates results

def classify_recipe(recipe):
    recipe_text = f"""
    Name: {recipe.get('name')}
    Ingredients: {', '.join(recipe.get('ingredients', []))}
    Instructions: {recipe.get('instructions')}
    """

    response = client.chat.completions.create(
        model=OPENAI_MODEL,
        messages=[
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": recipe_text},
        ],
        temperature=0
    )

    try:
        content = response.choices[0].message.content.strip()
        return eval(content)  # AI returns JSON string, convert to dict
    except Exception as e:
        logger.info(f"Failed to parse AI output for {recipe['name']}: {e}")
        logger.info("Raw output:", response.choices[0].message.content)
        return None

def bulk_update_recipe_tags(recipe_slug, new_tag_names, tag_lookup):
    """Use /api/recipes/bulk-actions/tag to attach tags to a recipe."""
    tag_objects = []
    for name in new_tag_names:
        if not name or name == "None":
            continue
        tag = tag_lookup.get(name.lower())
        if tag:
            tag_objects.append(tag)
        else:
            logger.info(f"⚠️ Tag '{name}' not found in Mealie — skipping")

    if not tag_objects:
        logger.info("⚠️ No valid tags to apply")
        return

    url = f"{MEALIE_URL}/recipes/bulk-actions/tag"
    payload = {
        "recipes": [recipe_slug],
        "tags": tag_objects
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 200:
        logger.info(f"✅ Updated recipe '{recipe_slug}' with tags {[t['name'] for t in tag_objects]}")
    else:
        logger.info(f"❌ Failed to update recipe '{recipe_slug}': {r.text}")

def flatten(lst):
    for item in lst:
        if isinstance(item, list):
            yield from flatten(item)
        else:
            yield item
# ==============================
# MAIN WORKFLOW
# ==============================
def tag_recipes(dry_run=os.getenv("DRY_RUN", True)):
    logger.info("🔍 Fetching tag list from Mealie...")
    tag_lookup = fetch_tags()

    recipes = fetch_recipes_since_first_of_month()
    for recipe in recipes:
        if not recipe:
            logger.info("No recipes found in Mealie.")
            return

        logger.info(f"Classifying recipe: {recipe['name']} (slug {recipe['slug']})")
        classification = classify_recipe(recipe)
        if classification:
            tags = [classification["cuisine"], classification["main_carb"],
                    *flatten(classification["main_protein"]), classification["meal_time"]]
            logger.info(f"AI suggests tags: {tags}")
            if not dry_run == "True":
                bulk_update_recipe_tags(recipe["slug"], tags, tag_lookup)
            else:
                logger.info("Dry Run. Not Pushing Tags")
        else:
            logger.info("Classification failed.")

def main():
    tag_recipes()

if __name__ == "__main__":
    main()
