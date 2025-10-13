from setuptools import setup, find_packages

setup(
    name="mealie_meal_planner",     # package name
    version="0.1.0",
    packages=find_packages(),       # automatically find __init__.py packages
    install_requires=[],            # list dependencies here if any
    entry_points={
        "console_scripts": [
            # optional: make it runnable from command line
            # "mealplan=mealie_meal_planner.meal_plan:plan_meals"
        ],
    },
)
