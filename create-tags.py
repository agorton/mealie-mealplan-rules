# Create a default set of tags that we can use with organise-tags.py
# Really the organise tags should automatically try and create the tag first and then push it in, but that sounds hard.

import os
import requests
from dotenv import load_dotenv

load_dotenv()

# ==============================
# CONFIGURATION
# ==============================
MEALIE_URL = os.getenv("MEALIE_SERVER") + "/api"
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")  # create this in Mealie settings

headers = {"Authorization": f"Bearer {MEALIE_TOKEN}"}

# All possible categories
CUISINES = [
    "Indian", "Italian", "Chinese", "Mexican", "French",
    "Japanese", "Greek", "American", "Middle Eastern", "Filipino"
]
CARBS = ["Rice", "Pasta", "Bread", "Potatoes", "Couscous", "Quinoa"]
PROTEINS = ["Chicken", "Beef", "Pork", "Lamb", "Fish", "Tofu", "Lentils", "Beans"]
MEALTIME = ["Breakfast", "Lunch", "Dinner", "Side", "Dessert", "Snack"]

def create_tag(name: str):
    url = f"{MEALIE_URL}/organizers/tags"
    payload = {"name": name}
    response = requests.post(url, headers=headers, json=payload)
    if response.status_code == 201:
        print(f"✅ Created tag: {name}")
    elif response.status_code == 409:
        print(f"ℹ️ Tag already exists: {name}")
    else:
        print(f"❌ Failed to create tag {name}: {response.text}")

def main():
    all_tags = CUISINES + CARBS + PROTEINS + MEALTIME
    for tag in all_tags:
        create_tag(tag)

if __name__ == "__main__":
    main()
