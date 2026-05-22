from travel_agent.models import (
    NegativeFilters,
    PreferenceRequest,
    PreferenceVector,
    TripContext,
)

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
