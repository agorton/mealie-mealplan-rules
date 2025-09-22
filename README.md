# Mealie Meal Plan Rules

A Python script to generate meal plans using the Mealie API, applying custom rules and push the plan so it appears in Mealie.

---

## Features

* Fetches available recipes from Mealie.
* Allows defining **rules** to filter which recipes are used.

  * **Hard rules**: never broken (e.g. exclude allergens).
  * **Soft rules**: can be relaxed if no candidates remain.
* Priority-based backoff: the least-important soft rules are dropped first if needed.
* Logging / tracing: for each meal, indicates if any rules had to be relaxed and why.
* Pushes the generated plan to Mealie so it's visible in the app.

---

## Project Structure

```
mealie-mealplan-rules/
├── main.py              # Entry point: orchestrates fetch → plan generation → push
├── planner.py           # Core logic: applying rules, backoff, plan generation
├── rules/               # Package containing rule definitions
│   ├── __init__.py
│   ├── base.py          # Base Rule class
│   ├── no_duplicates.py  
│   ├── exclude_tag.py
│   └── max_tag_per_week.py
└── README.md            # This file
```

---

## Setup & Requirements

1. Python 3.7+

2. Install dependencies, e.g.:

   ```bash
   pip install
   ```

3. Configure environment or constants in `main.py`:

   * `MEALIE_SERVER` — your Mealie instance’s API base URL.
   * `MEALIE_TOKEN` — your Mealie API token with sufficient permission.

---

## Usage

```bash
cd path/to/mealie-mealplan-rules
python main.py
```

This will:

* Fetch all recipes.
* Create a 7-day plan (by default, breakfast/lunch/dinner each day).
* Print log messages showing which recipe was chosen each meal, and which rules (if any) were relaxed.
* Push the plan to Mealie via its API.

---

## Defining Rules

Rules are split into two categories:

* **Hard rules**: marked with `hard=True` in their constructor. They are applied first and never relaxed.
* **Soft rules**: `hard=False`. They have a priority integer (lower = more important). They may be relaxed if necessary (i.e. if no recipes pass all soft rules).

Example:

```python
from rules.exclude_tag import ExcludeTag
from rules.no_duplicates import NoDuplicatesWithinDays
from rules.max_tag_per_week import MaxTagPerWeek

rules = [
    ExcludeTag("allergen-nuts", hard=True, name="No Nuts"),
    NoDuplicatesWithinDays(7, hard=False, priority=1, name="No Duplicates (7d)"),
    ExcludeTag("dessert", hard=False, priority=2, name="No Desserts"),
    MaxTagPerWeek("chicken", max_count=2, hard=False, priority=3, name="Max 2 Chicken/Week"),
]
```

---

## Customization

You can extend or modify:

* Add new rules by creating new files under the `rules/` package (inherit from the base `Rule`).
* Adjust how many meals per day, how many days to plan.
* Change the backoff logic or priorities to suit your preferences.

---

## Troubleshooting

* **Import errors**: make sure Python is run from the root of the project so that the `rules/` package can be found.
* **No candidates left**: if even hard rules eliminate all recipes, the script will error. Add more recipes or relax hard rules.
* **Authentication / API failures**: ensure your Mealie API token is valid and has correct permissions.

---
