
import json
from langchain.tools import tool


@tool
def estimate_trip_budget(
    travelers: int,
    trip_days: int,
    flight_cost_per_person: float,
    hotel_price_per_night: float,
    food_cost_per_person_per_day: float,
    transport_cost_per_day: float,
    activities_cost_per_person_per_day: float,
    currency: str = "INR",
) -> str:
    """
    Estimate total travel expenses for a trip.

    Flight cost should be the total airfare per traveler
    for the complete journey (one-way or round-trip).
    Transport cost is the shared daily cost for all travelers.
    """

    try:
        if travelers < 1 or trip_days < 1:
            return json.dumps({
                "status": "error",
                "message": "Travelers and trip days must be at least 1."
            })

        costs = [
            flight_cost_per_person,
            hotel_price_per_night,
            food_cost_per_person_per_day,
            transport_cost_per_day,
            activities_cost_per_person_per_day,
        ]

        if any(cost < 0 for cost in costs):
            return json.dumps({
                "status": "error",
                "message": "Expenses cannot be negative."
            })

        nights = max(trip_days - 1, 0)

        flight_total = flight_cost_per_person * travelers
        hotel_total = hotel_price_per_night * nights
        food_total = food_cost_per_person_per_day * trip_days * travelers
        transport_total = transport_cost_per_day * trip_days
        activities_total = (
            activities_cost_per_person_per_day * trip_days * travelers
        )

        subtotal = (
            flight_total
            + hotel_total
            + food_total
            + transport_total
            + activities_total
        )

        contingency = subtotal * 0.10
        grand_total = subtotal + contingency

        return json.dumps({
            "status": "success",
            "currency": currency,
            "travelers": travelers,
            "trip_days": trip_days,
            "hotel_nights": nights,
            "budget_breakdown": {
                "flights": round(flight_total, 2),
                "hotels": round(hotel_total, 2),
                "food": round(food_total, 2),
                "local_transport": round(transport_total, 2),
                "activities": round(activities_total, 2),
                "subtotal": round(subtotal, 2),
                "contingency_10_percent": round(contingency, 2),
                "estimated_total": round(grand_total, 2),
            },
            "estimated_cost_per_person": round(
                grand_total / travelers, 2
            ),
            "note": (
                "This is an estimate. Actual prices may vary. "
                "Hotel cost assumes one room; adjust if multiple rooms "
                "are required."
            )
        }, indent=4)

    except (TypeError, ValueError) as error:
        return json.dumps({
            "status": "error",
            "message": str(error)
        })
