"""
AI Client module for querying AI models and engines.

Acts as the single point of interaction for AI engine queries and demo agent responses.
Controls real vs mock behavior using config.settings.REAL_MODE.

Completely industry-agnostic and business-type neutral. Zero shoe/footwear/vertical bias.
"""

import json
import random
import time
from config import settings
from brand_visibility.exceptions import get_brand_dir, BrandNotFoundError

# Module-level state for real mode
_real_call_count = 0
_circuit_state = {}  # engine_name -> consecutive failure count
_last_settings = None


def reset_client_state():
    """Reset module-level call count and circuit breaker state."""
    global _real_call_count, _circuit_state
    _real_call_count = 0
    _circuit_state = {}


def _circuit_open(engine_name: str) -> bool:
    limit = getattr(settings, "AI_CONSECUTIVE_FAILURE_LIMIT", 3)
    return _circuit_state.get(engine_name, 0) >= limit


def _trip_circuit(engine_name: str):
    _circuit_state[engine_name] = _circuit_state.get(engine_name, 0) + 1


def _reset_circuit(engine_name: str):
    _circuit_state[engine_name] = 0


def _call_gemini(question: str, key: str, brand_context: dict = None) -> str:
    """Call Google Gemini API."""
    import google.generativeai as genai

    genai.configure(api_key=key)
    model = genai.GenerativeModel("gemini-1.5-flash")

    if brand_context and isinstance(brand_context, dict):
        display_name = brand_context.get("display_name", brand_context.get("name", "this brand"))
        website_url = brand_context.get("website_url", "")
        facts = brand_context.get("facts", [])
        prompt = (
            f"Brand: {display_name}\nWebsite: {website_url}\nFacts: {json.dumps(facts)}\n"
            f"Question: {question}"
        )
    else:
        prompt = question

    response = model.generate_content(prompt)
    if hasattr(response, "text"):
        return response.text
    return str(response)


def _call_groq(question: str, key: str, brand_context: dict = None) -> str:
    """Call Groq API."""
    from groq import Groq

    client = Groq(api_key=key)

    if brand_context and isinstance(brand_context, dict):
        display_name = brand_context.get("display_name", brand_context.get("name", "this brand"))
        website_url = brand_context.get("website_url", "")
        facts = brand_context.get("facts", [])
        prompt = (
            f"Brand: {display_name}\nWebsite: {website_url}\nFacts: {json.dumps(facts)}\n"
            f"Question: {question}"
        )
    else:
        prompt = question

    chat_completion = client.chat.completions.create(
        messages=[{"role": "user", "content": prompt}],
        model="llama-3.3-70b-versatile",
    )
    return chat_completion.choices[0].message.content


ENGINE_REGISTRY = {
    "engine_a": {
        "caller": lambda question, key, brand_context=None: _call_gemini(question, key, brand_context=brand_context),
        "key_env": "GEMINI_API_KEY",
    },
    "engine_b": {
        "caller": lambda question, key, brand_context=None: _call_groq(question, key, brand_context=brand_context),
        "key_env": "GROQ_API_KEY",
    },
}


def _call_with_retry(engine_name: str, caller, question: str, key: str, brand_context: dict = None) -> str:
    timeout = getattr(settings, "AI_REQUEST_TIMEOUT", 15)
    max_retries = getattr(settings, "AI_MAX_RETRIES", 1)
    backoff = getattr(settings, "AI_RETRY_BACKOFF_SECONDS", 2)

    last_err = None
    for attempt in range(1, max_retries + 2):
        try:
            response = caller(question, key, brand_context=brand_context)
            if not response or not isinstance(response, str):
                _trip_circuit(engine_name)
                return f"[{engine_name} error: malformed response]"
            _reset_circuit(engine_name)
            return response
        except TimeoutError:
            last_err = f"[{engine_name} error: timeout after {timeout}s]"
            if attempt <= max_retries:
                time.sleep(backoff)
        except Exception as exc:
            status = getattr(exc, "status_code", None)
            if status == 429:
                last_err = f"[{engine_name} error: rate limited]"
                if attempt <= max_retries:
                    time.sleep(backoff)
                continue
            if status in (502, 503, 504):
                last_err = f"[{engine_name} error: service unavailable ({status})]"
                if attempt <= max_retries:
                    time.sleep(backoff)
                continue
            if status in (401, 403):
                _trip_circuit(engine_name)
                return f"[{engine_name} error: auth failed]"
            _trip_circuit(engine_name)
            both_signal = "[both engines unavailable for this question; manual review recommended]"
            return f"[{engine_name} error: {exc}] {both_signal}"

    _trip_circuit(engine_name)
    return last_err or f"[{engine_name} error: request failed]"


def get_brand_context(brand_id: str, brand_type: str = None) -> dict:
    """
    Load brand input record and any approved generated brand facts.

    Returns dict with display_name, website_url, brand_id, brand_type, and facts list.
    """
    brand_dir = get_brand_dir(brand_id, brand_type=brand_type)
    brand_json_path = brand_dir / "brand.json"

    if not brand_json_path.exists():
        raise BrandNotFoundError(f"Brand record not found at {brand_json_path}")

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


def ask_ai(question: str, brand_context: dict = None, engine: str = "engine_a") -> str:
    """
    Query an AI chatbot or engine.

    - question: buyer intent question string
    - brand_context: if provided, simulates AI having access to approved brand fact file
    - engine: target engine identifier ("engine_a", "engine_b", etc.)

    Returns a text response or a visible error string.
    """
    global _real_call_count, _last_settings

    current_settings = (
        getattr(settings, "REAL_MODE", False),
        getattr(settings, "AI_MAX_REAL_CALLS_PER_RUN", 10),
        getattr(settings, "AI_CONSECUTIVE_FAILURE_LIMIT", 3),
        getattr(settings, "GEMINI_API_KEY", ""),
        getattr(settings, "GROQ_API_KEY", ""),
        getattr(settings, "AI_MAX_RETRIES", 1),
    )
    if _last_settings != current_settings:
        reset_client_state()
        _last_settings = current_settings

    if getattr(settings, "REAL_MODE", False):
        entry = ENGINE_REGISTRY.get(engine)
        if not entry:
            return f"[{engine} error: unknown engine]"

        key = getattr(settings, entry["key_env"], "")
        if not key or key == "***":
            return f"[{engine} error: missing API key]"

        if _circuit_open(engine):
            return f"[{engine} error: circuit breaker tripped after {_circuit_state[engine]} consecutive failures]"

        budget = getattr(settings, "AI_MAX_REAL_CALLS_PER_RUN", 10)
        if _real_call_count >= budget:
            return f"[{engine} error: real call budget exhausted]"

        _real_call_count += 1
        return _call_with_retry(engine, entry["caller"], question, key, brand_context=brand_context)

    # Mock mode implementation (when REAL_MODE is False)
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
