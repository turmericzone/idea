from fastapi import FastAPI, HTTPException

from .agent import run_agent
from .models import Destination, ItineraryResponse, PreferenceRequest
from .tools import generate_destinations, score_and_filter

app = FastAPI(title="Travel Preference → Itinerary")


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}


@app.post("/itinerary", response_model=ItineraryResponse)
def create_itinerary(request: PreferenceRequest) -> ItineraryResponse:
    try:
        return run_agent(request)
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc


@app.post("/match-only", response_model=list[Destination])
def match_only(request: PreferenceRequest) -> list[Destination]:
    """Score and filter destinations without building an itinerary."""
    try:
        vector = request.vector.model_dump()
        context = request.context.model_dump()
        filters = request.filters.model_dump() if request.filters else {}
        weights = request.weights.model_dump() if request.weights else {}

        raw = generate_destinations(vector=vector, context=context, filters=filters)
        scored = score_and_filter(destinations=raw, vector=vector, weights=weights, filters=filters)
        return [Destination(**d) for d in scored]
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc)) from exc
