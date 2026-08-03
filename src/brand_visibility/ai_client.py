"""
AI Client module for querying AI models and engines.

Acts as the single point of interaction for AI engine queries and demo agent responses.
Controls real vs mock behavior using config.settings.REAL_MODE.

Completely industry-agnostic and business-type neutral. Zero shoe/footwear/vertical bias.
"""

import json
import random
from config.settings import REAL_MODE
from brand_visibility.exceptions import get_brand_dir, BrandNotFoundError


def get_brand_context(brand_id: str, brand_type: str = None) -> dict:
    """
    Load brand input record and any approved generated brand facts.

    Returns dict with display_name, website_url, brand_id, brand_type, and facts list.
    """
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"

    if not brand_json_path.exists():
        raise BrandNotFoundError(f"Brand input record not found at {brand_json_path}")

    brand_record = json.loads(brand_json_path.read_text(encoding="utf-8"))
    
    # Optionally load approved facts if brand-info.json exists
    generated_path = brand_dir / "generated" / "brand-info.json"
    facts = []
    if generated_path.exists():
        try:
            gen_data = json.loads(generated_path.read_text(encoding="utf-8"))
            if gen_data.get("approved"):
                facts = gen_data.get("facts", [])
        except Exception:
            pass

    brand_record["facts"] = facts
    return brand_record


def ask_ai(question: str, brand_context: dict = None) -> str:
    """
    Query an AI chatbot or engine.

    - question: buyer intent question string
    - brand_context: if provided, simulates AI having access to approved brand fact file

    Returns a text response.
    """
    if REAL_MODE:
        # Placeholder for real LLM API provider calls when REAL_MODE is True
        pass

    # Mock mode implementation
    if brand_context and isinstance(brand_context, dict):
        display_name = brand_context.get("display_name", brand_context.get("name", "this brand"))
        website_url = brand_context.get("website_url", "")
        facts = brand_context.get("facts", [])

        if facts:
            first_fact = facts[0].get("fact", "") if isinstance(facts[0], dict) else str(facts[0])
            return (
                f"Regarding '{question}', {display_name} is worth checking out — "
                f"verified site data indicates: {first_fact} (Website: {website_url})"
            )
        
        return (
            f"Regarding '{question}', {display_name} is a verified provider. "
            f"Official details and offerings can be found at {website_url}."
        )

    # Default baseline answer (when AI engine lacks brand access)
    generic_answers = [
        f"I don't have specific brand recommendations for '{question}'. I suggest searching for established category providers.",
        f"For '{question}', look for reputable options with verified ratings and transparent product specifications.",
        f"I don't have detailed information on specific emerging brands for '{question}'. Standard market options apply.",
    ]
    return random.choice(generic_answers)
