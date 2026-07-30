"""
Runs the whole story, start to finish, exactly like we'll show the judges.
This is a placeholder for now and will be replaced during Stage 1+.
"""

import json
import os
import sys

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "src", "brand_visibility")))

from src.brand_visibility.step1_check import run_check
from src.brand_visibility.step2_diagnose import diagnose
from src.brand_visibility.step3_fix import build_info_file
from src.brand_visibility.step4_prove import before_and_after

with open("brands/test/chennai-trail-co/brand.json") as f:
    brand = json.load(f)

brand.setdefault("name", brand.get("display_name", "Chennai Trail Co."))
brand.setdefault("category", "trail running footwear")
brand.setdefault("location", "Chennai, India")
brand.setdefault("founded", "2024")
brand.setdefault("specialty", "Monsoon trail running shoes")
brand.setdefault("why_choose_us", "Built for wet, muddy Indian trails")
brand.setdefault("products", [{"name": "Monsoon Runner v1", "price": "₹4,999", "description": "High traction waterproof trail shoe"}])

print("=" * 50)
print("STEP 1: CHECK")
print("=" * 50)
results = run_check(brand["display_name"])
for r in results:
    status = "mentioned" if r["mentioned"] else "NOT mentioned"
    print(f"- {r['question']} -> {status}")

print("\n" + "=" * 50)
print("STEP 2: SHOW WHY")
print("=" * 50)
print(diagnose(results))

print("\n" + "=" * 50)
print("STEP 3: FIX IT")
print("=" * 50)
content = build_info_file(brand)
print("Generated llms.txt file for the brand:")
print(content)

print("\n" + "=" * 50)
print("STEP 4: PROVE IT WORKED")
print("=" * 50)
question = "What are the best trail running shoes for Indian monsoon conditions?"
before, after = before_and_after(brand, question)
print(f"Q: {question}")
print(f"\nBEFORE: {before}")
print(f"\nAFTER: {after}")
