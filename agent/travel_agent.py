"""Gantavya AI travel planner.

Token-efficient orchestration:
- Executes the five existing Python tools directly.
- Sends only compact tool results to Groq for the final plan.
- Avoids sending large tool schemas to Groq on every request.
- Keeps run_travel_agent() compatible with the existing Streamlit app.

This is a tool-augmented LangChain/Groq workflow rather than a
create_agent() tool-calling loop. It is designed for the 8K TPM limit.
"""

import json
import re
import time
from typing import Any

from dotenv import load_dotenv
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage

from tools.flight_tool import search_flights
from tools.hotel_tool import search_hotels
from tools.places_tool import search_places
from tools.weather_tool import get_weather_forecast
from tools.budget_tool import estimate_trip_budget
from agent.prompts import TRAVEL_AGENT_PROMPT

load_dotenv()

MODEL_NAME = "openai/gpt-oss-20b"
MAX_OUTPUT_TOKENS = 1800
TOOL_RESULT_CHAR_LIMIT = 2600

# Keep this short: the original detailed prompt is retained in prompts.py,
# but a compact system message reduces input tokens for the final Groq call.
COMPACT_SYSTEM_PROMPT = (
    "You are Gantavya AI, a concise budget-aware travel planner. "
    "Use only supplied tool results; never invent facts. The route must remain "
    "departure to destination. Hotels, attractions and weather use destination. "
    "Flights, hotels and attractions are static historical sample data, not live "
    "or bookable. Weather is live; state only returned forecast dates. Use the "
    "budget-tool result exactly if present; otherwise say it is unavailable. "
    "Create exactly the requested number of days. Keep the complete answer under "
    "900 words and avoid long explanations. Use compact Markdown tables. "
    "Include: (1) trip summary and route; (2) flight options; (3) at most 3 "
    "hotel options; (4) at most 4 attractions; (5) concise weather summary; "
    "(6) one short morning/afternoon/evening row for each itinerary day; "
    "(7) budget breakdown and per-person estimate if returned; "
    "(8) one short limitations note. Never leave a table unfinished."
)


def build_travel_agent():
    """Build a lightweight LangChain ChatGroq model (no tool schemas attached)."""
    return ChatGroq(
        model=MODEL_NAME,
        temperature=0.1,
        max_retries=0,
        timeout=60,
        reasoning_effort="low",
        model_kwargs={"include_reasoning": False},
        max_tokens=MAX_OUTPUT_TOKENS,
    )


def extract_number(patterns, text, default=None, number_type=float):
    for pattern in patterns:
        match = re.search(pattern, text or "", re.IGNORECASE)
        if match:
            try:
                return number_type(match.group(1).replace(",", ""))
            except (ValueError, TypeError):
                pass
    return default


def extract_trip_details(request):
    text = request or ""
    route_match = re.search(
        r"\bfrom\s+([A-Za-z][A-Za-z ]*?)\s+to\s+"
        r"([A-Za-z][A-Za-z ]*?)"
        r"(?=\s+(?:for|with|on|during|between)\b|[,.;\n]|$)",
        text,
        re.IGNORECASE,
    )
    departure = " ".join(route_match.group(1).split()) if route_match else None
    destination = " ".join(route_match.group(2).split()) if route_match else None

    travelers = extract_number(
        [r"\b(\d+)\s*(?:travelers?|people|persons?)\b",
         r"\bfor\s+(\d+)\s+(?:of\s+us|people)\b"],
        text, 2, int,
    )
    days = extract_number([r"\b(\d+)\s*[- ]?\s*days?\b"], text, 3, int)
    hotel_budget = extract_number(
        [r"hotels?.*?(?:under|below|less than|max(?:imum)?)\s*(?:INR|Rs\.?|₹)?\s*([\d,]+)",
         r"(?:under|below)\s*(?:INR|Rs\.?|₹)?\s*([\d,]+)\s*(?:per night|/night)"],
        text, 5000, float,
    )
    rating = extract_number(
        [r"(?:rating|rated).*?(?:at least|minimum)\s*(\d+(?:\.\d+)?)",
         r"minimum attraction rating\s*[:=]?\s*(\d+(?:\.\d+)?)"],
        text, 4.0, float,
    )
    food = extract_number(
        [r"food(?:\s+cost)?\s*[:=]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+)"],
        text, 800, float,
    )
    transport = extract_number(
        [r"transport(?:\s+cost)?\s*[:=]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+)"],
        text, 1000, float,
    )
    activities = extract_number(
        [r"activities(?:\s+cost)?\s*[:=]?\s*(?:INR|Rs\.?|₹)?\s*([\d,]+)"],
        text, 500, float,
    )
    return {
        "departure_city": departure,
        "destination_city": destination,
        "travelers": max(1, travelers),
        "trip_days": max(1, min(days, 7)),
        "hotel_budget": hotel_budget,
        "minimum_rating": rating,
        "food_cost": food,
        "transport_cost": transport,
        "activities_cost": activities,
    }


def _tool_call(tool, args, label, show_trace):
    """Invoke an existing LangChain @tool and return a printable result."""
    try:
        result = tool.invoke(args)
        if show_trace:
            print(f"[TOOL OK] {label}")
        return result, None
    except Exception as exc:
        if show_trace:
            print(f"[TOOL ERROR] {label}: {exc}")
        return None, str(exc)


def _to_jsonable(value):
    if isinstance(value, (dict, list, str, int, float, bool)) or value is None:
        return value
    return str(value)


def _compact_result(value, limit=TOOL_RESULT_CHAR_LIMIT):
    if value is None:
        return "No result returned."
    try:
        text = json.dumps(_to_jsonable(value), ensure_ascii=False, default=str)
    except Exception:
        text = str(value)
    if len(text) > limit:
        text = text[:limit] + "... [truncated to control token usage]"
    return text


def _find_numeric_values(value, key_words):
    """Find numeric values under keys containing any supplied keyword."""
    found = []
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
            if isinstance(parsed, (dict, list)):
                return _find_numeric_values(parsed, key_words)
        except (ValueError, TypeError):
            return found
    if isinstance(value, dict):
        for key, item in value.items():
            key_lower = str(key).lower()
            if any(word in key_lower for word in key_words):
                try:
                    number = float(str(item).replace(",", "").replace("₹", "").strip())
                    if number > 0:
                        found.append(number)
                except (ValueError, TypeError):
                    pass
            found.extend(_find_numeric_values(item, key_words))
    elif isinstance(value, list):
        for item in value:
            found.extend(_find_numeric_values(item, key_words))
    return found


def _calculate_budget(flight_result, hotel_result, details, show_trace):
    """Call the project's budget tool when sample prices can be extracted."""
    flight_prices = _find_numeric_values(
        flight_result, ("price", "fare", "cost")
    )
    hotel_prices = _find_numeric_values(
        hotel_result, ("price_per_night", "nightly_rate", "per_night")
    )
    # Some tools may expose a generic 'price' field for hotel records.
    if not hotel_prices:
        hotel_prices = _find_numeric_values(hotel_result, ("price",))

    if not flight_prices or not hotel_prices:
        if show_trace:
            print("[BUDGET] Skipped: could not reliably extract flight and hotel prices.")
        return None

    args = {
        "travelers": details["travelers"],
        "trip_days": details["trip_days"],
        "flight_cost_per_person": min(flight_prices),
        "hotel_price_per_night": min(hotel_prices),
        "food_cost_per_person_per_day": details["food_cost"],
        "transport_cost_per_day": details["transport_cost"],
        "activities_cost_per_person_per_day": details["activities_cost"],
        "currency": "INR",
    }
    result, error = _tool_call(
        estimate_trip_budget, args, "estimate_trip_budget", show_trace
    )
    if error:
        return {"error": error, "arguments": args}
    return {"arguments": args, "result": result}


def run_travel_agent(
    user_request: str,
    agent=None,
    show_trace: bool = True,
    departure_city: str | None = None,
    destination_city: str | None = None,
):
    """Run existing project tools, then make one compact Groq generation call."""
    if not user_request or not user_request.strip():
        return "Please enter a valid travel request."

    started = time.perf_counter()
    details = extract_trip_details(user_request)
    departure = departure_city or details["departure_city"]
    destination = destination_city or details["destination_city"]

    if not departure or not destination:
        return (
            "Please specify both departure and destination cities. "
            "Example: Plan a 3-day trip from Hyderabad to Delhi for 2 travelers."
        )
    if departure.casefold() == destination.casefold():
        return "AGENT_ERROR: Departure and destination cities must differ."

    details["departure_city"] = departure
    details["destination_city"] = destination

    if show_trace:
        print("\n========== GANTAVYA TOKEN-EFFICIENT WORKFLOW ==========")
        print(f"Route: {departure} -> {destination}")
        print(f"Travelers: {details['travelers']} | Days: {details['trip_days']}")
        print("Running Python tools before the single Groq generation call...")

    # These searches run locally in Python; no tool schemas are sent to Groq.
    flight_result, flight_error = _tool_call(
        search_flights,
        {"departure_city": departure, "destination_city": destination, "max_price": None},
        "search_flights", show_trace,
    )
    hotel_result, hotel_error = _tool_call(
        search_hotels,
        {"city": destination, "max_price_per_night": details["hotel_budget"],
         "min_stars": None, "required_amenity": None},
        "search_hotels", show_trace,
    )
    places_result, places_error = _tool_call(
        search_places,
        {"city": destination, "place_type": None,
         "min_rating": details["minimum_rating"]},
        "search_places", show_trace,
    )
    weather_result, weather_error = _tool_call(
        get_weather_forecast,
        {"city": destination, "forecast_days": min(7, details["trip_days"] + 2)},
        "get_weather_forecast", show_trace,
    )

    budget_result = _calculate_budget(
        flight_result, hotel_result, details, show_trace
    )

    tool_data = {
        "trip_requirements": {
            "departure_city": departure,
            "destination_city": destination,
            "travelers": details["travelers"],
            "trip_days": details["trip_days"],
            "hotel_max_price_per_night_inr": details["hotel_budget"],
            "minimum_attraction_rating": details["minimum_rating"],
            "food_cost_per_person_per_day_inr": details["food_cost"],
            "transport_cost_per_day_inr": details["transport_cost"],
            "activities_cost_per_person_per_day_inr": details["activities_cost"],
        },
        "tool_results": {
            "flights": _compact_result(flight_result),
            "hotels": _compact_result(hotel_result),
            "attractions": _compact_result(places_result),
            "weather": _compact_result(weather_result),
            "budget": _compact_result(budget_result),
        },
        "tool_errors": {
            key: value for key, value in {
                "flights": flight_error,
                "hotels": hotel_error,
                "attractions": places_error,
                "weather": weather_error,
            }.items() if value
        },
    }

    # The cached Streamlit object may be an older agent; rebuild if it is not
    # a ChatGroq model. No tool definitions are attached to this model.
    model = agent if isinstance(agent, ChatGroq) else build_travel_agent()

    human_prompt = (
        "Create the travel plan using only this compact JSON data. "
        "The route must remain exactly "
        f"{departure} -> {destination}. "
        "Do not claim that sample flights or hotels are live/bookable. "
        "If any tool result is missing, state that clearly. Data: "
        + json.dumps(tool_data, ensure_ascii=False, separators=(",", ":"), default=str)
    )

    try:
        if show_trace:
            print("[GROQ] Sending one compact request without tool schemas...")
            print(f"[GROQ] Input payload size: {len(human_prompt)} characters.")

        response = model.invoke([
            SystemMessage(content=COMPACT_SYSTEM_PROMPT),
            HumanMessage(content=human_prompt),
        ])
        content = response.content
        if isinstance(content, list):
            content = "\n".join(
                str(part.get("text", "")) if isinstance(part, dict) else str(part)
                for part in content
            )
        content = str(content or "").strip()

        if not content:
            if show_trace:
                print("[GROQ] Empty visible content.")
                print("[GROQ] Additional kwargs:", getattr(response, "additional_kwargs", {}))
                print("[GROQ] Response metadata:", getattr(response, "response_metadata", {}))
            return (
                "AGENT_ERROR: Groq returned no visible answer text. "
                "Check the terminal diagnostics for model response metadata."
            )

        if show_trace:
            print("\n========== FINAL GANTAVYA RESPONSE ==========")
            print(content)
            print("[GROQ] Response metadata:", getattr(response, "response_metadata", {}))
            print(f"\nTotal execution time: {time.perf_counter() - started:.2f}s")
        return content

    except Exception as error:
        message = str(error)
        if show_trace:
            print("\n========== GROQ GENERATION ERROR ==========")
            print(type(error).__name__, message)
        lowered = message.lower()
        if "429" in message or "rate_limit" in lowered or "rate limit" in lowered:
            return (
                "TEMPORARY_API_ERROR: Groq TPM limit is currently occupied. "
                "Wait for the rolling rate-limit window to clear and try once."
            )
        if "timeout" in lowered:
            return "TEMPORARY_API_ERROR: The AI request timed out."
        return "AGENT_ERROR: " + message


if __name__ == "__main__":
    sample = (
        "Plan a 3-day trip from Hyderabad to Delhi for 2 travelers. "
        "Find hotels under INR 5000 per night and attractions rated at least 4.0. "
        "Use INR 800 per person per day for food, INR 1000 per day for transport "
        "and INR 500 per person per day for activities."
    )
    print(run_travel_agent(sample, show_trace=True))
