"""
STEP 4: PROVE IT WORKED
Run the same AI question twice:
  - once WITHOUT our generated info file (the "before")
  - once WITH it (the "after")

This is the live demo moment - the judges see the AI's answer
actually change in front of them.
"""

import json
from ai_client import ask_ai


def before_and_after(brand, question):
    before = ask_ai(question)
    after = ask_ai(question, brand_context=brand)
    return before, after


if __name__ == "__main__":
    with open("demo_brand.json") as f:
        brand = json.load(f)

    question = "What are the best trail running shoes for Indian monsoon conditions?"
    before, after = before_and_after(brand, question)

    print("BEFORE (AI has no info about the brand):")
    print(before)
    print("\nAFTER (AI can read our generated info file):")
    print(after)
