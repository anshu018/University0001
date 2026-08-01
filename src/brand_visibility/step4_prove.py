"""
STEP 4: PROVE IT WORKED
Run the same AI question twice:
  - once WITHOUT our generated info file (the "before")
  - once WITH it (the "after")

This is the live demo moment - the judges see the AI's answer
actually change in front of them.
"""

import json
import os
try:
    from .ai_client import ask_ai
except ImportError:
    from ai_client import ask_ai


def before_and_after(brand, question):
    before = ask_ai(question)
    after = ask_ai(question, brand_context=brand)
    return before, after


if __name__ == "__main__":
    brand_path = os.path.join(os.path.dirname(__file__), "..", "..", "brands", "test", "chennai-trail-co", "brand.json")
    with open(os.path.abspath(brand_path)) as f:
        brand = json.load(f)

    if "name" not in brand and "display_name" in brand:
        brand["name"] = brand["display_name"]
    brand.setdefault("why_choose_us", "specially engineered trail footwear")
    brand.setdefault("products", [{"name": "Monsoon Grip Trail Shoe"}])

    question = "What are the best trail running shoes for Indian monsoon conditions?"
    before, after = before_and_after(brand, question)

    print("BEFORE (AI has no info about the brand):")
    print(before)
    print("\nAFTER (AI can read our generated info file):")
    print(after)
