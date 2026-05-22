import math
from .models import PreferenceVector, DimensionWeights, Destination, NegativeFilters

_DIMS = list(PreferenceVector.model_fields.keys())


def cosine_similarity(
    user_vec: PreferenceVector,
    dest_vec: PreferenceVector,
    weights: DimensionWeights,
) -> float:
    dot = sum(
        getattr(user_vec, d) * getattr(dest_vec, d) * getattr(weights, d)
        for d in _DIMS
    )
    user_mag = math.sqrt(sum((getattr(user_vec, d) * getattr(weights, d)) ** 2 for d in _DIMS))
    dest_mag = math.sqrt(sum(getattr(dest_vec, d) ** 2 for d in _DIMS))
    if user_mag == 0.0 or dest_mag == 0.0:
        return 0.0
    return dot / (user_mag * dest_mag)


def apply_filters(
    destinations: list[Destination],
    filters: NegativeFilters,
) -> list[Destination]:
    result: list[Destination] = []
    for dest in destinations:
        text = f"{dest.name} {dest.region}".lower()

        if any(exc.lower() in text for exc in filters.hard_exclusions):
            continue

        score = dest.similarity_score
        for exc in filters.soft_exclusions:
            if exc.lower() in text:
                score -= 0.2
        for exc in filters.fatigue_exclusions:
            if exc.lower() in text:
                score -= 0.15

        dest = dest.model_copy(update={"similarity_score": max(0.0, score)})
        result.append(dest)

    result.sort(key=lambda d: d.similarity_score, reverse=True)
    return result
