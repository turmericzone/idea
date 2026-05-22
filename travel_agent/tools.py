import json
import litellm
from strands import tool

from .config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, MODEL_NAME, MAX_TOKENS
from .matching import apply_filters, cosine_similarity
from .models import (
    Destination,
    DimensionWeights,
    ItineraryResponse,
    NegativeFilters,
    PreferenceVector,
    TripContext,
)
from .prompts import (
    DESTINATION_GENERATION_PROMPT,
    ITINERARY_GENERATION_PROMPT,
    PREFERENCE_SUMMARY_PROMPT,
)


_VECTOR_KEYS = [
    "social_intensity", "physical_intensity", "cultural_appetite", "culinary_focus",
    "tempo", "structure", "nature_vs_urban", "budget", "novelty_seeking",
]


def _normalise_vector(v: dict | list) -> dict:
    """Convert a list of values to a named vector dict if the model returned a list."""
    if isinstance(v, list):
        return dict(zip(_VECTOR_KEYS, v))
    return v


def _llm(system: str, user: str) -> str:
    response = litellm.completion(
        model=MODEL_NAME,
        api_base=OPENROUTER_BASE_URL,
        api_key=OPENROUTER_API_KEY,
        max_tokens=MAX_TOKENS,
        ssl_verify=False,
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
    )
    return response.choices[0].message.content.strip()


@tool
def generate_destinations(
    vector: dict,
    context: dict,
    filters: dict,
) -> list[dict]:
    """Generate 5 destination candidates using the LLM based on the preference vector."""
    user_msg = json.dumps(
        {
            "preference_vector": vector,
            "trip_context": context,
            "hard_exclusions": filters.get("hard_exclusions", []),
        },
        indent=2,
    )
    raw = _llm(DESTINATION_GENERATION_PROMPT, user_msg)
    data = json.loads(raw)
    for dest in data:
        dest["vector"] = _normalise_vector(dest["vector"])
    return data


@tool
def score_and_filter(
    destinations: list[dict],
    vector: dict,
    weights: dict,
    filters: dict,
) -> list[dict]:
    """Score destinations with weighted cosine similarity and apply negative filters."""
    user_vec = PreferenceVector(**vector)
    dim_weights = DimensionWeights(**weights) if weights else DimensionWeights()
    neg_filters = NegativeFilters(**filters) if filters else NegativeFilters()

    dest_objects: list[Destination] = []
    for d in destinations:
        dest_vec = PreferenceVector(**d["vector"])
        score = cosine_similarity(user_vec, dest_vec, dim_weights)
        dest_objects.append(
            Destination(
                name=d["name"],
                region=d["region"],
                vector=dest_vec,
                similarity_score=score,
                reasoning=d["reasoning"],
            )
        )

    filtered = apply_filters(dest_objects, neg_filters)
    return [d.model_dump() for d in filtered[:3]]


@tool
def build_itinerary(
    destination: dict,
    vector: dict,
    context: dict,
) -> dict:
    """Build a full day-by-day itinerary for the chosen destination."""
    user_msg = json.dumps(
        {
            "destination": destination,
            "preference_vector": vector,
            "trip_context": context,
        },
        indent=2,
    )
    raw = _llm(ITINERARY_GENERATION_PROMPT, user_msg)
    return json.loads(raw)


@tool
def summarise_preferences(vector: dict) -> str:
    """Summarise a preference vector in plain English (2 sentences, no numbers)."""
    user_msg = json.dumps(vector, indent=2)
    return _llm(PREFERENCE_SUMMARY_PROMPT, user_msg)
