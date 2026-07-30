"""
STEP 3: FIX IT
Auto-generate a clean, structured info file about the brand - this is
what we'd let AI agents read.

This is our small version of the "llms.txt" idea - a simple,
AI-readable file with clear facts about the brand.
"""

import json


def build_info_file(brand, output_path="llms.txt"):
    lines = [
        f"# {brand['name']}",
        f"Category: {brand['category']}",
        f"Location: {brand['location']}",
        f"Founded: {brand['founded']}",
        f"Specialty: {brand['specialty']}",
        f"Why choose us: {brand['why_choose_us']}",
        "",
        "## Products",
    ]
    for p in brand["products"]:
        lines.append(f"- {p['name']} ({p['price']}): {p['description']}")

    content = "\n".join(lines)

    with open(output_path, "w") as f:
        f.write(content)

    return content


if __name__ == "__main__":
    with open("demo_brand.json") as f:
        brand = json.load(f)

    content = build_info_file(brand)
    print("Generated llms.txt:\n")
    print(content)
