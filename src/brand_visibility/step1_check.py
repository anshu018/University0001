"""
STEP 1: CHECK
Ask a couple of AI engines a few buyer questions and see if our brand
gets mentioned in the answer.
"""

import json
from ai_client import ask_ai

QUESTIONS = [
    "What are the best trail running shoes for Indian monsoon conditions?",
    "Recommend a good running shoe brand from India.",
]


def run_check(brand_name):
    results = []
    for q in QUESTIONS:
        answer = ask_ai(q)
        mentioned = brand_name.lower() in answer.lower()
        results.append({"question": q, "answer": answer, "mentioned": mentioned})
    return results


if __name__ == "__main__":
    with open("demo_brand.json") as f:
        brand = json.load(f)

    results = run_check(brand["name"])
    for r in results:
        status = "MENTIONED" if r["mentioned"] else "NOT mentioned"
        print(f"\nQ: {r['question']}\nA: {r['answer']}\nStatus: {status}")
