"""
Step 4: PROVE IT
Minimal Stage 1 proof script per plan boundary.

- Without approved brand facts: baseline mock answer
- With approved brand facts: richer answer showing brand access

In Stage 1 this is intentionally minimal. Full before/after demo agent
with MCP tools belongs to Stage 3.
"""

import os
import sys
from pathlib import Path

# Ensure project root and src directory are in sys.path for direct execution
root_dir = Path(__file__).resolve().parent.parent.parent
if str(root_dir) not in sys.path:
    sys.path.insert(0, str(root_dir))
src_dir = Path(__file__).resolve().parent.parent
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))

from brand_visibility.ai_client import ask_ai, get_brand_context


def run_prove(brand_id: str, brand_type: str = None, question: str | None = None) -> dict:
    brand_context = get_brand_context(brand_id, brand_type=brand_type)
    display_name = brand_context.get("display_name", brand_id)
    website_url = brand_context.get("website_url", "")

    if question is None:
        question = f"What are the key facts about {display_name} from its official website?"

    before = ask_ai(question)
    after = ask_ai(question, brand_context=brand_context)

    print(f"Question: {question}\n", file=sys.stderr)
    print("WITHOUT brand access (before):", file=sys.stderr)
    print(before, file=sys.stderr)
    print("\nWITH brand access (after):", file=sys.stderr)
    print(after, file=sys.stderr)

    return {
        "brand_id": brand_id,
        "question": question,
        "before": before,
        "after": after,
    }


if __name__ == "__main__":
    import os as _os
    brand_id = _os.environ.get("BRAND_ID")
    brand_type = _os.environ.get("BRAND_TYPE")
    if not brand_id:
        print("Set BRAND_ID to run directly.", file=sys.stderr)
        raise SystemExit(2)
    run_prove(brand_id, brand_type=brand_type)
