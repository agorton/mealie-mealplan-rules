import os
import requests
from openai import OpenAI
from dotenv import load_dotenv
import classifications

# ==============================
# CONFIGURATION
# ==============================

load_dotenv()

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
- Cuisine: one of {classifications.CUISINES}
- Main carb: one of {classifications.CARBS}
- Main protein: one of {classifications.PROTEINS}
- Meal time: one of {classifications.MEALTIME}

Always return JSON in this format:
{{
  "cuisine": "...",
  "main_carb": "...",
  "main_protein": "..."
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

def fetch_recipes():
    url = f"{MEALIE_URL}/recipes"
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
        print(f"Failed to parse AI output for {recipe['name']}: {e}")
        print("Raw output:", response.choices[0].message.content)
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
            print(f"⚠️ Tag '{name}' not found in Mealie — skipping")

    if not tag_objects:
        print("⚠️ No valid tags to apply")
        return

    url = f"{MEALIE_URL}/recipes/bulk-actions/tag"
    payload = {
        "recipes": [recipe_slug],
        "tags": tag_objects
    }
    r = requests.post(url, headers=headers, json=payload)
    if r.status_code == 200:
        print(f"✅ Updated recipe '{recipe_slug}' with tags {[t['name'] for t in tag_objects]}")
    else:
        print(f"❌ Failed to update recipe '{recipe_slug}': {r.text}")

# ==============================
# MAIN WORKFLOW
# ==============================

def main():
    print("🔍 Fetching tag list from Mealie...")
    tag_lookup = fetch_tags()

    recipes = fetch_recipes()
    for recipe in recipes:
        if not recipe:
            print("No recipes found in Mealie.")
            return

        print(f"Classifying recipe: {recipe['name']} (slug {recipe['slug']})")
        classification = classify_recipe(recipe)
        if classification:
            tags = [classification["cuisine"], classification["main_carb"],
                    classification["main_protein"], classification["meal_time"]]
            print(f"AI suggests tags: {tags}")
            bulk_update_recipe_tags(recipe["slug"], tags, tag_lookup)
        else:
            print("Classification failed.")

if __name__ == "__main__":
    main()
