
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from langchain_core.tools import tool

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "flights.json"


def calculate_flight_duration(flight: dict) -> Optional[float]:
    """Calculate flight duration in minutes from departure and arrival times."""

    departure = flight.get("departure_time")
    arrival = flight.get("arrival_time")

    if not departure or not arrival:
        return None

    date_formats = [
        "%Y-%m-%d %H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%dT%H:%M",
        "%b %d %Y %H:%M",
        "%b %d, %Y %H:%M",
        "%b %d %Y %I:%M %p",
        "%b %d, %Y %I:%M %p",
        "%H:%M",
    ]

    def parse_datetime(value):
        for date_format in date_formats:
            try:
                return datetime.strptime(value.strip(), date_format)
            except ValueError:
                continue
        return None

    departure_dt = parse_datetime(departure)
    arrival_dt = parse_datetime(arrival)

    if departure_dt is None or arrival_dt is None:
        return None

    duration = arrival_dt - departure_dt

    # Handle overnight flights when the dataset contains times only.
    if duration.total_seconds() < 0:
        if departure_dt.date() == arrival_dt.date():
            duration += timedelta(days=1)
        else:
            return None

    return duration.total_seconds() / 60


@tool
def search_flights(
    departure_city: str,
    destination_city: str,
    max_price: Optional[float] = None,
) -> str:
    """
    Search sample flights by departure city, destination city
    and optional maximum price. Identify the cheapest and fastest flights.
    """

    try:
        with open(DATA_FILE, "r", encoding="utf-8") as file:
            flights = json.load(file)

        if not isinstance(flights, list):
            raise ValueError("Flight dataset must contain a JSON list.")

        results = [
            flight for flight in flights
            if flight.get("from", "").strip().lower()
            == departure_city.strip().lower()
            and flight.get("to", "").strip().lower()
            == destination_city.strip().lower()
            and (
                max_price is None
                or float(flight.get("price", 0)) <= max_price
            )
        ]

        # Sort by ticket price to identify the cheapest flight.
        results.sort(key=lambda flight: float(flight.get("price", 0)))

        cheapest_flight = results[0] if results else None

        # Calculate duration for each matching flight.
        flights_with_duration = []

        for flight in results:
            duration = calculate_flight_duration(flight)

            if duration is not None:
                flight_with_duration = flight.copy()
                flight_with_duration["duration_minutes"] = duration
                flights_with_duration.append(flight_with_duration)

        # Identify the fastest flight.
        fastest_flight = (
            min(
                flights_with_duration,
                key=lambda flight: flight["duration_minutes"]
            )
            if flights_with_duration
            else None
        )

        return json.dumps({
            "status": "success",
            "result_count": len(results),
            "departure_city": departure_city,
            "destination_city": destination_city,
            "notice": (
                "These are sample dataset records, not live or "
                "bookable flights. Flight prices and dates are "
                "for demonstration purposes only."
            ),
            "cheapest_flight": cheapest_flight,
            "fastest_flight": fastest_flight,
            "flights": results
        }, indent=2)

    except (FileNotFoundError, json.JSONDecodeError, ValueError,
            TypeError) as error:
        return json.dumps({
            "status": "error",
            "message": str(error)
        }, indent=2)
