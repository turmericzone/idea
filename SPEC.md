# Travel Preference → Itinerary System
## Spec for Aider Scaffolding

---

## Goal
Build a FastAPI service that accepts a hardcoded user preference vector and returns a structured travel itinerary. No UI. No auth. No database. Pure logic + LLM.

---

## Tech Stack
- **Python 3.11+**
- **FastAPI** — API layer
- **Pydantic v2** — data models
- **Strands SDK** — agent orchestration
- **LiteLLM** — model routing
- **OpenRouter** — LLM provider (OpenAI-compatible)
- **httpx** — async HTTP

---

## Project Structure
```
travel_agent/
  main.py               # FastAPI app, route definitions
  agent.py              # Strands agent — orchestrates the pipeline
  models.py             # All Pydantic models
  matching.py           # Cosine similarity + negative filter logic
  prompts.py            # All LLM prompt templates
  config.py             # Settings (model name, API keys via env)
  tools.py              # Strands tool definitions
  requirements.txt
  .env.example
```

---

## Data Models (models.py)

### PreferenceVector
All fields float, range 0.0–1.0.
```
social_intensity      # 0.0 = solo/avoids crowds, 1.0 = thrives meeting strangers
physical_intensity    # 0.0 = comfort first, 1.0 = peak physical challenge
cultural_appetite     # 0.0 = not interested, 1.0 = deep cultural immersion
culinary_focus        # 0.0 = eating is fuel, 1.0 = food is the point
tempo                 # 0.0 = slow one thing/day, 1.0 = packed maximum activities
structure             # 0.0 = total spontaneity, 1.0 = every hour planned
nature_vs_urban       # 0.0 = pure urban, 1.0 = deep wilderness
budget                # 0.0 = shoestring, 1.0 = unlimited
novelty_seeking       # 0.0 = familiar comfort, 1.0 = never-done-before
```

### DimensionWeights
Same keys as PreferenceVector. Each float is a multiplier applied before cosine similarity. Default 1.0 for all. User can signal "social life matters most" → set social_intensity weight to 2.0.

### ArchetypeEnum
```
SOCIAL_BUTTERFLY, SUMMIT_CHASER, CULTURE_SPONGE, RECHARGER,
THRILL_SEEKER, FOODIE_EXPLORER, FESTIVAL_PILGRIM, ROAD_WARRIOR
```

### ArchetypeAssignment
```
primary: ArchetypeEnum
secondary: ArchetypeEnum | None
primary_weight: float       # e.g. 0.6
secondary_weight: float     # e.g. 0.4, must sum to 1.0 with primary
```

### NegativeFilters
```
hard_exclusions: list[str]      # knockout — "no beaches", "not the South"
soft_exclusions: list[str]      # penalise but don't eliminate — "prefer no chains"
fatigue_exclusions: list[str]   # recency-based — "just did NYC, nothing like that"
```

### TripContext
```
duration_days: int              # e.g. 5
travel_party: str               # "solo" | "couple" | "group"
origin_city: str                # e.g. "Dallas, TX"
max_flight_hours: float | None  # e.g. 3.0, None = no limit
```

### PreferenceRequest (API input)
```
vector: PreferenceVector
weights: DimensionWeights | None        # optional, defaults to all 1.0
archetype: ArchetypeAssignment | None   # optional context
filters: NegativeFilters | None         # optional
context: TripContext
```

### Destination (intermediate)
```
name: str
region: str                     # e.g. "Southwest", "Pacific Coast"
vector: PreferenceVector        # destination's own scored profile
similarity_score: float         # computed by matching engine
reasoning: str                  # LLM-generated explanation
```

### ItineraryDay
```
day: int
location: str
theme: str                      # e.g. "Arrival + neighbourhood exploration"
activities: list[str]           # 3–5 activities
meals: list[str]                # breakfast / lunch / dinner suggestions
notes: str                      # practical tips, logistics
```

### ItineraryResponse (API output)
```
destination: str
destination_reasoning: str
archetype_match: str            # plain language archetype label
preference_summary: str         # plain language summary of the vector
days: list[ItineraryDay]
confidence_score: float         # 0.0–1.0
```

---

## Matching Logic (matching.py)

### Weighted Cosine Similarity
```python
def cosine_similarity(user_vec, dest_vec, weights) -> float:
    # multiply each dimension by its weight before computing similarity
    # return float 0.0–1.0
```

### Negative Filter Application
Apply in this order:
1. Hard exclusions — eliminate destinations entirely if any hard exclusion matches
2. Soft exclusions — reduce similarity score by 0.2 per soft exclusion match
3. Fatigue exclusions — reduce similarity score by 0.15 per fatigue match

### apply_filters(destinations, filters) -> list[Destination]
- Remove hard-excluded destinations
- Apply score penalties for soft and fatigue exclusions
- Re-sort by adjusted score

---

## LLM Prompts (prompts.py)

### DESTINATION_GENERATION_PROMPT
System: You are a US domestic travel expert. Generate destination candidates based on a traveler preference vector.
Input: PreferenceVector as JSON + TripContext + any hard exclusions
Output: JSON array of 5 destinations, each with:
  - name, region
  - a scored preference vector (your estimate of how this destination scores)
  - one sentence reasoning
Return ONLY valid JSON. No preamble. No markdown.

### ITINERARY_GENERATION_PROMPT
System: You are an expert travel itinerary planner.
Input: Chosen destination + PreferenceVector + TripContext
Output: JSON matching ItineraryResponse schema — day by day plan
Return ONLY valid JSON. No preamble. No markdown.

### PREFERENCE_SUMMARY_PROMPT
System: Summarise a traveler's preference vector in plain English in 2 sentences. Never mention numbers or scores.
Input: PreferenceVector as JSON
Output: Plain text string only.

---

## Strands Agent (agent.py)

### Tools (tools.py)
Define these as Strands tools:

**generate_destinations(vector, context, filters) -> list[Destination]**
- Calls LLM with DESTINATION_GENERATION_PROMPT
- Parses JSON response
- Returns list of Destination objects

**score_and_filter(destinations, vector, weights, filters) -> list[Destination]**
- Runs cosine similarity from matching.py
- Applies negative filters
- Returns top 3 sorted by score

**build_itinerary(destination, vector, context) -> ItineraryResponse**
- Calls LLM with ITINERARY_GENERATION_PROMPT
- Parses JSON response
- Returns ItineraryResponse

**summarise_preferences(vector) -> str**
- Calls LLM with PREFERENCE_SUMMARY_PROMPT
- Returns plain text summary

### Agent Loop (agent.py)
```
1. summarise_preferences(vector)
2. generate_destinations(vector, context, filters)
3. score_and_filter(destinations, vector, weights, filters)
4. build_itinerary(top_destination, vector, context)
5. return ItineraryResponse
```

---

## API Endpoints (main.py)

### POST /itinerary
Request body: PreferenceRequest
Response: ItineraryResponse

### GET /health
Response: {"status": "ok"}

### POST /match-only
Request body: PreferenceRequest
Response: list of top 3 Destination with scores (no itinerary built)
Useful for testing the matching engine in isolation.

---

## Config (config.py)
Load from environment variables:
```
OPENROUTER_API_KEY
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
MODEL_NAME = "anthropic/claude-sonnet-4-5"
MAX_TOKENS = 2000
```

---

## Hardcoded Test Fixture
Include a test_fixtures.py with one hardcoded PreferenceRequest representing:
"26-year-old, social, mid budget, wants to meet people, some outdoor activity, 5 days, flying from Dallas"

```python
TEST_PREFERENCE = PreferenceRequest(
    vector=PreferenceVector(
        social_intensity=0.85,
        physical_intensity=0.35,
        cultural_appetite=0.45,
        culinary_focus=0.50,
        tempo=0.70,
        structure=0.40,
        nature_vs_urban=0.25,
        budget=0.45,
        novelty_seeking=0.60,
    ),
    context=TripContext(
        duration_days=5,
        travel_party="solo",
        origin_city="Dallas, TX",
        max_flight_hours=3.0,
    ),
    filters=NegativeFilters(
        hard_exclusions=["no beaches"],
        soft_exclusions=[],
        fatigue_exclusions=[],
    ),
)
```

---

## requirements.txt
```
fastapi
uvicorn
pydantic>=2.0
strands-agents
litellm
httpx
python-dotenv
```

---

## What NOT to build
- No database
- No user auth
- No conversation history
- No frontend
- No deployment config
- No tests (yet)

Keep it simple. The goal is one working POST /itinerary call that returns a real itinerary.
