"""
STEP 2: SHOW WHY
Look at the check results and explain, in plain words, why the brand
is missing from AI answers.
"""

import json
from .step1_check import run_check


def diagnose(check_results):
    missed = [r for r in check_results if not r["mentioned"]]
    if not missed:
        return "Brand is showing up fine - no issues found."

    return (
        f"The brand was missed in {len(missed)} out of {len(check_results)} questions.\n"
        "Likely reason: there is no clean, structured information about this brand "
        "anywhere an AI can easily read. AI engines tend to recommend brands they "
        "have clear, trustworthy facts about - right now, this brand has none online."
    )


if __name__ == "__main__":
    with open("demo_brand.json") as f:
        brand = json.load(f)

    results = run_check(brand["name"])
    print(diagnose(results))
