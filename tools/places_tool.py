
import json
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "places.json"


@tool
def search_places(
    city: str,
    place_type: Optional[str] = None,
    min_rating: Optional[float] = None,
) -> str:
    """
    Find tourist attractions by city, optional category and minimum rating.
    Return attractions sorted by rating and identify the highest-rated place.
    """

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            places = json.load(file)

        if not isinstance(places, list):
            raise ValueError("Places dataset must contain a JSON list.")

        results = [
            place for place in places
            if place.get("city", "").strip().lower() == city.strip().lower()
            and (
                place_type is None
                or place.get("type", "").strip().lower()
                == place_type.strip().lower()
            )
            and (
                min_rating is None
                or float(place.get("rating", 0)) >= min_rating
            )
        ]

        # Sort attractions from highest to lowest rating.
        results.sort(
            key=lambda place: float(place.get("rating", 0)),
            reverse=True
        )

        highest_rated_place = results[0] if results else None

        return json.dumps({
            "status": "success",
            "city": city,
            "result_count": len(results),
            "notice": (
                "Attraction names, categories and ratings are "
                "sample dataset records, not live visitor information."
            ),
            "highest_rated_place": highest_rated_place,
            "places": results
        }, indent=2)

    except (
        FileNotFoundError,
        json.JSONDecodeError,
        ValueError,
        TypeError
    ) as error:
        return json.dumps({
            "status": "error",
            "message": str(error)
        }, indent=2)
