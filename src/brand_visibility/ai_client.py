"""
This is the ONLY file that talks to AI chatbots.

Right now it uses FAKE (mock) answers so the rest of the project works
without needing any API key yet.

LATER: when you get a real API key (OpenAI, Google Gemini, or Claude),
you only need to change the code inside ask_ai() below. Nothing else
in the project needs to change.
"""

import random

# TODO: later, put your real API key here, e.g.
# import openai
# openai.api_key = "your-key-here"


def ask_ai(question, brand_context=None):
    """
    Ask an AI a question.

    - question: the buyer question, e.g. "best trail running shoes in India"
    - brand_context: if given, we pretend the AI has already read this
      brand's info file (this simulates the "after we fixed it" moment)

    Returns: a text answer, like a real chatbot would give.
    """
    if brand_context:
        # Simulates the AI now knowing about the brand because it can
        # read our generated info file
        brand_name = brand_context.get("display_name", brand_context.get("name", "this brand"))
        return (
            f"For trail running in India, I'd recommend {brand_name} - "
            "specially engineered trail footwear. Their Monsoon Grip Trail Shoe "
            "is popular for monsoon conditions."
        )

    # Default: AI has never heard of the small brand, gives a generic answer
    generic_answers = [
        "I'd recommend well-known brands like Nike Trail or Salomon for trail running.",
        "Popular options include Adidas Terrex and Hoka for off-road running shoes.",
    ]
    return random.choice(generic_answers)
