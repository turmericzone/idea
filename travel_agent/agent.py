from strands import Agent

from .models import ItineraryResponse, PreferenceRequest
from .tools import build_itinerary, generate_destinations, score_and_filter, summarise_preferences


def run_agent(request: PreferenceRequest) -> ItineraryResponse:
    agent = Agent(tools=[generate_destinations, score_and_filter, build_itinerary, summarise_preferences])

    vector = request.vector.model_dump()
    context = request.context.model_dump()
    weights = request.weights.model_dump() if request.weights else {}
    filters = request.filters.model_dump() if request.filters else {}

    # Step 1 — summarise preferences
    preference_summary: str = agent.tool.summarise_preferences(vector=vector)

    # Step 2 — generate destination candidates
    raw_destinations: list[dict] = agent.tool.generate_destinations(
        vector=vector,
        context=context,
        filters=filters,
    )

    # Step 3 — score and filter to top 3
    scored: list[dict] = agent.tool.score_and_filter(
        destinations=raw_destinations,
        vector=vector,
        weights=weights,
        filters=filters,
    )

    if not scored:
        raise ValueError("No suitable destinations found after filtering.")

    top = scored[0]

    # Step 4 — build full itinerary for top destination
    itinerary_data: dict = agent.tool.build_itinerary(
        destination=top,
        vector=vector,
        context=context,
    )

    itinerary_data["preference_summary"] = preference_summary

    return ItineraryResponse(**itinerary_data)
