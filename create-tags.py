# Create a default set of tags that we can use with organise-tags.py
# Really the organise tags should automatically try and create the tag first and then push it in, but that sounds hard.

import os
import requests
import classifications
from dotenv import load_dotenv

load_dotenv()

# ==============================
# CONFIGURATION
# ==============================
MEALIE_URL = os.getenv("MEALIE_SERVER") + "/api"
MEALIE_TOKEN = os.getenv("MEALIE_TOKEN")  # create this in Mealie settings

headers = {"Authorization": f"Bearer {MEALIE_TOKEN}"}

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
    all_tags = (classifications.CUISINES + classifications.CARBS +
                classifications.PROTEINS + classifications.MEALTIME)

    for tag in all_tags:
        if tag != "None":
            create_tag(tag)

if __name__ == "__main__":
    main()
