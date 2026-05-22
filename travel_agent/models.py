from enum import Enum
from typing import Optional
from pydantic import BaseModel, model_validator


class PreferenceVector(BaseModel):
    social_intensity: float
    physical_intensity: float
    cultural_appetite: float
    culinary_focus: float
    tempo: float
    structure: float
    nature_vs_urban: float
    budget: float
    novelty_seeking: float


class DimensionWeights(BaseModel):
    social_intensity: float = 1.0
    physical_intensity: float = 1.0
    cultural_appetite: float = 1.0
    culinary_focus: float = 1.0
    tempo: float = 1.0
    structure: float = 1.0
    nature_vs_urban: float = 1.0
    budget: float = 1.0
    novelty_seeking: float = 1.0


class ArchetypeEnum(str, Enum):
    SOCIAL_BUTTERFLY = "SOCIAL_BUTTERFLY"
    SUMMIT_CHASER = "SUMMIT_CHASER"
    CULTURE_SPONGE = "CULTURE_SPONGE"
    RECHARGER = "RECHARGER"
    THRILL_SEEKER = "THRILL_SEEKER"
    FOODIE_EXPLORER = "FOODIE_EXPLORER"
    FESTIVAL_PILGRIM = "FESTIVAL_PILGRIM"
    ROAD_WARRIOR = "ROAD_WARRIOR"


class ArchetypeAssignment(BaseModel):
    primary: ArchetypeEnum
    secondary: Optional[ArchetypeEnum] = None
    primary_weight: float
    secondary_weight: float

    @model_validator(mode="after")
    def weights_sum_to_one(self) -> "ArchetypeAssignment":
        total = self.primary_weight + self.secondary_weight
        if abs(total - 1.0) > 1e-6:
            raise ValueError(f"primary_weight + secondary_weight must equal 1.0, got {total}")
        return self


class NegativeFilters(BaseModel):
    hard_exclusions: list[str] = []
    soft_exclusions: list[str] = []
    fatigue_exclusions: list[str] = []


class TripContext(BaseModel):
    duration_days: int
    travel_party: str  # "solo" | "couple" | "group"
    origin_city: str
    max_flight_hours: Optional[float] = None


class PreferenceRequest(BaseModel):
    vector: PreferenceVector
    weights: Optional[DimensionWeights] = None
    archetype: Optional[ArchetypeAssignment] = None
    filters: Optional[NegativeFilters] = None
    context: TripContext


class Destination(BaseModel):
    name: str
    region: str
    vector: PreferenceVector
    similarity_score: float
    reasoning: str


class ItineraryDay(BaseModel):
    day: int
    location: str
    theme: str
    activities: list[str]
    meals: list[str]
    notes: str


class ItineraryResponse(BaseModel):
    destination: str
    destination_reasoning: str
    archetype_match: str
    preference_summary: str
    days: list[ItineraryDay]
    confidence_score: float
