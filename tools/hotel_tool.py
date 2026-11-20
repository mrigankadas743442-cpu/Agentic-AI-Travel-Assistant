
import json
from pathlib import Path
from typing import Optional

from langchain.tools import tool

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "hotels.json"


@tool
def search_hotels(
    city: str,
    max_price_per_night: Optional[float] = None,
    min_stars: Optional[int] = None,
    required_amenity: Optional[str] = None,
) -> str:
    """
    Find sample hotels by city, nightly budget, minimum star rating
    and optional amenity. Identify the cheapest and highest-rated hotels.
    """

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            hotels = json.load(file)

        if not isinstance(hotels, list):
            raise ValueError("Hotel dataset must contain a JSON list.")

        results = []

        for hotel in hotels:
            if hotel.get("city", "").strip().lower() != city.strip().lower():
                continue

            price = float(hotel.get("price_per_night", 0))
            stars = int(hotel.get("stars", 0))

            if max_price_per_night is not None and price > max_price_per_night:
                continue

            if min_stars is not None and stars < min_stars:
                continue

            amenities = [
                str(item).strip().lower()
                for item in hotel.get("amenities", [])
            ]

            if (
                required_amenity
                and required_amenity.strip().lower() not in amenities
            ):
                continue

            results.append(hotel)

        # Cheapest hotel first.
        results.sort(
            key=lambda hotel: float(hotel.get("price_per_night", 0))
        )

        cheapest_hotel = results[0] if results else None

        # Highest-rated hotel first.
        highest_rated_hotel = (
            max(results, key=lambda hotel: int(hotel.get("stars", 0)))
            if results
            else None
        )

        return json.dumps({
            "status": "success",
            "city": city,
            "result_count": len(results),
            "notice": (
                "Hotel information and prices are sample dataset records. "
                "They are not live availability or booking quotations."
            ),
            "cheapest_hotel": cheapest_hotel,
            "highest_rated_hotel": highest_rated_hotel,
            "hotels": results
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
