import json
import re
from pathlib import Path
import streamlit as st
from agent.travel_agent import build_travel_agent, run_travel_agent

# =========================================================

# 1. PAGE CONFIGURATION

# =========================================================

st.set_page_config(
    page_title="Gantavya AI | Smart Travel Planner",
    page_icon="✈️",
    layout="wide",
    initial_sidebar_state="expanded",
)
APP_NAME = "Gantavya AI"
BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"

# =========================================================

# 2. IMAGE CONFIGURATION

# =========================================================

IMAGES = {
    "hero": "https://images.unsplash.com/photo-1512343879784-a960bf40e7f2?w=1200",
    "flight": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05?w=1000",
    "hotel": "https://images.unsplash.com/photo-1566073771259-6a8506099945?w=1000",
    "places": "https://images.unsplash.com/photo-1533929736458-ca588d08c8be?w=1000",
    "weather": "https://images.unsplash.com/photo-1504608524841-42fe6f032b4b?w=1000",
    "budget": "https://images.unsplash.com/photo-1554224155-6726b3ff858f?w=1000",
    "itinerary": "https://images.unsplash.com/photo-1464822759023-fed622ff2c3b?w=1000",
    "summary": "https://images.unsplash.com/photo-1476514525535-07fb3b4ae5f1?w=1000",
    "notes": "https://images.unsplash.com/photo-1488646953014-85cb44e25828?w=1000",
}

# =========================================================

# 3. CUSTOM CSS

# =========================================================

st.markdown(
    """

    <style>

        @import url(

            'https://fonts.googleapis.com/css2?family=DM+Sans:wght@400;500;600;700;800&display=swap'

        );



        html, body, [class*="css"] {

            font-family: 'DM Sans', sans-serif;

        }



        .stApp {

            background: #F5F7FB;

        }



        [data-testid="stSidebar"] {

            background: #102B46;

        }



        [data-testid="stSidebar"] * {

            color: #FFFFFF;

        }



        .hero-title {

            font-size: 42px;

            font-weight: 800;

            color: white;

            margin-bottom: 5px;

            text-shadow: 1px 2px 8px rgba(0,0,0,0.45);

        }



        .hero-subtitle {

            font-size: 17px;

            color: white;

            text-shadow: 1px 2px 6px rgba(0,0,0,0.5);

        }



        .section-title {

            font-size: 25px;

            font-weight: 800;

            color: #183B56;

            margin-bottom: 5px;

        }



        .section-subtitle {

            font-size: 14px;

            color: #64748B;

            margin-bottom: 15px;

        }



        .stButton > button,

        .stFormSubmitButton > button {

            border-radius: 10px;

            font-weight: 700;

            min-height: 45px;

        }



        .stForm {

            background: white;

            border: 1px solid #E5EAF1;

            border-radius: 16px;

            padding: 20px;

        }



        [data-testid="stTabs"] button {

            font-weight: 700;

        }



        .footer {

            text-align: center;

            color: #64748B;

            padding: 25px 0;

            font-size: 13px;

        }



        div[data-testid="stImage"] img {

            border-radius: 12px;

        }



        .small-note {

            color: #64748B;

            font-size: 13px;

        }

    </style>

    """,
    unsafe_allow_html=True,
)

# =========================================================

# 4. LOAD CITY OPTIONS FROM JSON DATASETS

# =========================================================

@st.cache_data

def load_cities():
    """Read city names from the local JSON datasets."""
    cities = set()
    files = [
        ("flights.json", ["from", "to"]),
        ("hotels.json", ["city"]),
        ("places.json", ["city"]),
    ]
    for filename, fields in files:
        file_path = DATA_DIR / filename
        if not file_path.exists():
            continue
        try:
            with open(file_path, "r", encoding="utf-8") as file:
                records = json.load(file)
            if not isinstance(records, list):
                continue
            for record in records:
                if not isinstance(record, dict):
                    continue
                for field in fields:
                    value = record.get(field)
                    if isinstance(value, str) and value.strip():
                        cities.add(value.strip())
        except (json.JSONDecodeError, OSError) as error:
            st.warning(f"Could not read {filename}: {error}")
    return sorted(cities)
cities = load_cities()
if not cities:
    cities = [
        "Delhi",
        "Goa",
        "Hyderabad",
        "Kolkata",
        "Mumbai",
        "Bengaluru",
        "Chennai",
    ]

# =========================================================

# 5. CACHE LANGCHAIN + GROQ MODEL

# =========================================================

@st.cache_resource

def load_travel_agent():
    """Initialize and cache the LangChain/Groq model."""
    return build_travel_agent()

# =========================================================

# 6. SESSION STATE

# =========================================================

DEFAULT_SESSION_VALUES = {
    "travel_agent": None,
    "travel_plan": None,
    "travel_request": None,
    "last_error": None,
    "requested_route": None,
}
for key, default_value in DEFAULT_SESSION_VALUES.items():
    if key not in st.session_state:
        st.session_state[key] = default_value

# =========================================================

# 7. ERROR MESSAGE HELPER

# =========================================================

def friendly_error_message(error_text):
    """Convert common API errors into understandable messages."""
    message = str(error_text)
    lower_message = message.lower()
    if "429" in message or "rate_limit" in lower_message or "rate limit" in lower_message:
        return (
            "The Groq API rate limit has been reached. Please wait a short "
            "while and try again. If this happens repeatedly, reduce the "
            "number of requests or check your Groq account limits."
        )
    if "401" in message or "authentication" in lower_message or "invalid_api_key" in lower_message:
        return (
            "Groq authentication failed. Check that GROQ_API_KEY is correctly "
            "configured in your local .env file. Do not share your API key."
        )
    if "timeout" in lower_message or "timed out" in lower_message:
        return (
            "The request timed out. Please check your internet connection "
            "and try again."
        )
    if "503" in message or "unavailable" in lower_message:
        return (
            "The AI service is temporarily unavailable. Please wait a few "
            "minutes and try again."
        )
    return f"Travel planning failed: {message}"

# =========================================================

# 8. GENERATE TRAVEL PLAN

# =========================================================

def generate_travel_plan(user_request, departure_city, destination_city):
    """Run the travel tools and ask Groq to prepare the final plan."""
    try:
        with st.spinner(
            "🤖 Gantavya AI is checking flights, hotels, attractions, "
            "weather and your estimated budget. Please wait..."
        ):
            if st.session_state.travel_agent is None:
                st.session_state.travel_agent = load_travel_agent()
            response = run_travel_agent(
                user_request=user_request,
                agent=st.session_state.travel_agent,
                show_trace=True,
                departure_city=departure_city,
                destination_city=destination_city,
            )
        if not isinstance(response, str):
            response = str(response)
        if response.startswith("AGENT_ERROR:"):
            error_message = response.replace("AGENT_ERROR:", "", 1).strip()
            st.session_state.last_error = friendly_error_message(error_message)
            st.error(st.session_state.last_error)
            return False
        if response.startswith("TEMPORARY_API_ERROR:"):
            error_message = response.replace(
                "TEMPORARY_API_ERROR:", "", 1
            ).strip()
            st.session_state.last_error = friendly_error_message(error_message)
            st.error(st.session_state.last_error)
            return False
        if not response.strip():
            st.session_state.last_error = (
                "The AI assistant returned an empty response. Please try again."
            )
            st.error(st.session_state.last_error)
            return False
        # Validate explicit route fields only. Do not mistake Markdown table
        # headings such as "From -> To" for an actual route.
        summary_text = response.split("## Flight Options", 1)[0]
        summary_text = summary_text.split("### Flight Options", 1)[0]
        summary_lines = summary_text.splitlines()[:35]

        reported_departure = None
        reported_destination = None
        reported_route = None

        for line in summary_lines:
            clean_line = re.sub(r"[*_`#|]", "", line).strip()
            departure_match = re.search(
                r"^departure(?:\s+city)?\s*[:：-]\s*(.+?)\s*$",
                clean_line,
                flags=re.IGNORECASE,
            )
            destination_match = re.search(
                r"^destination(?:\s+city)?\s*[:：-]\s*(.+?)\s*$",
                clean_line,
                flags=re.IGNORECASE,
            )
            route_match = re.search(
                r"^(?:(?:travel\s+)?route)\s*[:：-]\s*"
                r"(.+?)\s*(?:→|->)\s*(.+?)\s*$",
                clean_line,
                flags=re.IGNORECASE,
            )

            if departure_match:
                reported_departure = departure_match.group(1).strip()
            if destination_match:
                reported_destination = destination_match.group(1).strip()
            if route_match:
                reported_route = (
                    route_match.group(1).strip(),
                    route_match.group(2).strip(),
                )

        def city_matches(reported, expected):
            if not reported:
                return True
            reported = re.sub(r"\s*\([^)]*\)", "", reported).strip()
            expected = expected.strip()
            return (
                reported.casefold() == expected.casefold()
                or reported.casefold().startswith(expected.casefold() + " ")
            )

        route_is_valid = (
            city_matches(reported_departure, departure_city)
            and city_matches(reported_destination, destination_city)
        )
        if reported_route:
            route_is_valid = (
                route_is_valid
                and city_matches(reported_route[0], departure_city)
                and city_matches(reported_route[1], destination_city)
            )

        if not route_is_valid:
            displayed_route = (
                f"{reported_departure or 'unknown'} → "
                f"{reported_destination or 'unknown'}"
            )
            st.session_state.last_error = (
                f"The AI reported {displayed_route}, but you selected "
                f"{departure_city} → {destination_city}. "
                "The incorrect plan was rejected."
            )
            st.error(st.session_state.last_error)
            return False
        st.session_state.travel_plan = response
        st.session_state.travel_request = user_request
        st.session_state.last_error = None
        st.session_state.requested_route = (
            f"{departure_city} → {destination_city}"
        )
        return True
    except Exception as error:
        st.session_state.last_error = friendly_error_message(error)
        st.error(st.session_state.last_error)
        return False

# =========================================================

# 9. SPLIT AI RESPONSE INTO DASHBOARD SECTIONS

# =========================================================

SECTION_ALIASES = {
    "trip summary": [
        "trip summary",
        "trip summary & route",
        "trip summary and route",
    ],
    "flight options": [
        "flight options",
        "flight information",
    ],
    "hotel recommendations": [
        "hotel recommendations",
        "hotel options",
    ],
    "tourist attractions": [
        "tourist attractions",
        "attractions",
        "places to visit",
    ],
    "weather forecast": [
        "weather forecast",
        "weather",
    ],
    "day-wise itinerary": [
        "day-wise itinerary",
        "day wise itinerary",
        "day–wise itinerary",
        "day‑wise itinerary",
        "itinerary",
    ],
    "estimated budget": [
        "estimated budget",
        "budget breakdown",
        "budget",
    ],
    "important notes": [
        "important notes",
        "important assumptions & limitations",
        "assumptions & limitations",
        "assumptions and limitations",
        "notes",
    ],
}

def split_plan_into_sections(plan):
    """Identify dashboard sections despite Markdown and heading variations."""
    alias_to_section = {
        alias.lower(): section
        for section, aliases in SECTION_ALIASES.items()
        for alias in aliases
    }
    sections = {}
    current_section = None
    current_lines = []
    def save_current():
        if current_section and current_lines:
            content = "\n".join(current_lines).strip()
            if content:
                sections[current_section] = content
    for line in plan.splitlines():
        cleaned = line.strip()
        # Remove Markdown heading markers.
        cleaned = re.sub(r"^#{1,6}\s*", "", cleaned)
        # Remove numbered heading prefixes.
        cleaned = re.sub(r"^\d+\s*[.)]\s*", "", cleaned)
        # Remove Markdown emphasis.
        cleaned = cleaned.strip().strip("*_` ").strip()
        # Normalize different Unicode dash characters.
        cleaned = cleaned.replace("‑", "-")
        cleaned = cleaned.replace("–", "-")
        cleaned = cleaned.replace("—", "-")
        # Remove descriptive text in parentheses.
        cleaned = cleaned.strip()
        # Remove trailing punctuation.
        cleaned = cleaned.rstrip(":").strip()
        normalized = re.sub(r"\s+", " ", cleaned.lower()).strip()
        matched_section = alias_to_section.get(normalized)
        # Also accept headings with additional descriptive words.
        if not matched_section:
            for alias, section in alias_to_section.items():
                if normalized.startswith(alias + " "):
                    matched_section = section
                    break
        if matched_section:
            save_current()
            current_section = matched_section
            current_lines = []
        elif current_section:
            current_lines.append(line)
    save_current()
    return sections

# =========================================================

# 10. SIDEBAR NAVIGATION

# =========================================================

with st.sidebar:
    st.markdown(f"## ✈️ {APP_NAME}")
    st.caption("INTELLIGENT TRAVEL ASSISTANT")
    st.markdown("---")
    st.markdown("### Navigation")
    page = st.radio(
        "Navigate",
        ["Plan Your Trip", "My Travel Plan", "About Project"],
        label_visibility="collapsed",
    )
    st.markdown("---")
    st.markdown("### AI Capabilities")
    features = [
        "✈️ Flight Search",
        "🏨 Hotel Recommendations",
        "📍 Tourist Attractions",
        "🌤️ Weather Forecast",
        "💰 Budget Estimation",
        "🗓️ Day-wise Itinerary",
    ]
    for feature in features:
        st.markdown(f"- {feature}")
    st.markdown("---")
    st.caption("Powered by Python • LangChain • Groq")

# =========================================================

# 11. PLAN YOUR TRIP PAGE

# =========================================================

if page == "Plan Your Trip":
    st.image(IMAGES["hero"], width="stretch")
    st.html(
        """
<div style="background:linear-gradient(110deg,#102B46,#176B87);padding:28px;border-radius:15px;margin-top:8px;margin-bottom:25px;">
  <div class="hero-title">Your Journey, Intelligently Planned.</div>
  <div class="hero-subtitle">Tell us your destination. Let AI organize the details.</div>
</div>
        """
    )
    st.markdown(
        '<div class="section-title">Plan Your Journey</div>',
        unsafe_allow_html=True,
    )
    st.markdown(
        '<div class="section-subtitle">'
        "Enter your travel details to generate a personalized travel plan."
        "</div>",
        unsafe_allow_html=True,
    )
    with st.form("travel_form"):
        st.markdown("### ✈️ Flight Information")
        col1, col2 = st.columns(2)
        with col1:
              departure_city = st.selectbox(
              "Departure City",
              cities,
              index=0,
              key="departure_city",
            )
        with col2:
             destination_city = st.selectbox(
             "Destination City",
              cities,
             index=1,
             key="destination_city",
            )
        st.markdown("---")
        st.markdown("### 🏨 Accommodation & Travelers")
        col3, col4, col5 = st.columns(3)
        with col3:
            travelers = st.number_input(
                "Number of Travelers",
                min_value=1,
                max_value=20,
                value=2,
                step=1,
            )
        with col4:
            trip_days = st.number_input(
                "Trip Duration (days)",
                min_value=3,
                max_value=7,
                value=3,
                step=1,
                help="The itinerary generator is configured for trips of 3–7 days.",
            )
        with col5:
            hotel_budget = st.number_input(
                "Maximum Hotel Budget / Night (₹)",
                min_value=500,
                max_value=100000,
                value=5000,
                step=500,
            )
        st.markdown("---")
        st.markdown("### 📍 Explore & Discover")
        col6, col7 = st.columns(2)
        with col6:
            min_rating = st.selectbox(
                "Minimum Attraction Rating",
                [3.0, 3.5, 4.0, 4.5],
                index=2,
            )
        with col7:
            travel_style = st.selectbox(
                "Travel Style",
                [
                    "Balanced",
                    "Budget Friendly",
                    "Adventure",
                    "Historical & Cultural",
                    "Relaxation",
                    "Family Trip",
                ],
            )
        preferences = st.text_area(
            "Additional Preferences",
            placeholder=(
                "Example: historical places, beaches, local food, "
                "shopping, nature..."
            ),
        )
        st.markdown("---")
        st.markdown("### 💰 Daily Budget Assumptions")
        st.caption(
            "These values are estimates used by the budget calculator. "
            "Transport is treated as a shared daily cost."
        )
        col8, col9, col10 = st.columns(3)
        with col8:
            food_cost = st.number_input(
                "Food / Person / Day (₹)",
                min_value=0,
                max_value=20000,
                value=800,
                step=100,
            )
        with col9:
            transport_cost = st.number_input(
                "Transport / Day for Group (₹)",
                min_value=0,
                max_value=50000,
                value=1000,
                step=100,
            )
        with col10:
            activities_cost = st.number_input(
                "Activities / Person / Day (₹)",
                min_value=0,
                max_value=20000,
                value=500,
                step=100,
            )
        submitted = st.form_submit_button(
            "✨ GENERATE MY AI TRAVEL PLAN",
            width="stretch",
            type="primary",
        )
    if submitted:
        if departure_city == destination_city:
            st.error("Please choose two different cities.")
        else:
            # Clear the previous plan before processing a new destination.
            st.session_state.travel_plan = None
            st.session_state.travel_request = None
            st.session_state.last_error = None
            st.session_state.requested_route = (
                f"{departure_city} → {destination_city}"
            )
            user_request = f"""
Plan a {trip_days}-day trip from {departure_city} to {destination_city}
for {travelers} travelers.
Please find hotels under INR {hotel_budget} per night and attractions
with a minimum rating of {min_rating}.
Travel style: {travel_style}.
Additional preferences: {preferences or "None"}.
BUDGET ASSUMPTIONS:
FOOD COST: INR {food_cost} per person per day
TRANSPORT COST: INR {transport_cost} per day for the whole group
ACTIVITIES COST: INR {activities_cost} per person per day
CURRENCY: INR
REQUIREMENTS:
1. Search sample flights between the selected cities.
2. Recommend hotels within the nightly budget.
3. Find suitable tourist attractions.
4. Apply the minimum attraction rating.
5. Retrieve the destination weather forecast.
6. Calculate the estimated total budget for all travelers using the
   budget assumptions above.
7. Create an itinerary for exactly {trip_days} days.
8. Explain all expense assumptions.
FINAL RESPONSE SECTIONS:
1. Trip Summary
2. Flight Options
3. Hotel Recommendations
4. Tourist Attractions
5. Weather Forecast
6. Day-wise Itinerary
7. Estimated Budget
8. Important Notes
IMPORTANT:
- Use actual results returned by the tools.
- Do not invent flights, hotels or attractions.
- Clearly identify flight, hotel and attraction records as sample data.
- Historical sample flight fares are not live or bookable.
- Do not claim that a booking has been made.
- Do not assume a sample flight fare is round-trip. State its direction
  or one-way limitation if the data does not confirm a return fare.
- Do not present current weather as a forecast for an arbitrary future
  travel date.
- If a tool returns no results, explain that honestly.
- Preserve the original names, ratings and categories in the datasets.
"""
            success = generate_travel_plan(
                user_request=user_request,
                departure_city=departure_city,
                destination_city=destination_city,
            )
            if success:
                st.success("Your travel plan has been generated!")
                st.info(
                    "Open 'My Travel Plan' from the sidebar to explore "
                    "your results."
                )

# =========================================================

# 12. MY TRAVEL PLAN PAGE

# =========================================================

elif page == "My Travel Plan":
    st.markdown("## 🌍 Your Travel Dashboard")
    st.caption("Explore your AI-generated travel recommendations.")
    if st.session_state.requested_route:
        st.info(
            f"Latest requested route: {st.session_state.requested_route}"
        )
    if not st.session_state.travel_plan:
        st.info(
            "You haven't generated a travel plan yet. "
            "Go to 'Plan Your Trip' to get started."
        )
        if st.session_state.last_error:
            st.warning(st.session_state.last_error)
    else:
        plan = st.session_state.travel_plan
        section_content = split_plan_into_sections(plan)
        sections = [
            ("Trip Summary", "trip summary", "summary"),
            ("Flight Options", "flight options", "flight"),
            ("Hotel Recommendations", "hotel recommendations", "hotel"),
            ("Tourist Attractions", "tourist attractions", "places"),
            ("Weather Forecast", "weather forecast", "weather"),
            ("Day-wise Itinerary", "day-wise itinerary", "itinerary"),
            ("Estimated Budget", "estimated budget", "budget"),
            ("Important Notes", "important notes", "notes"),
        ]
        tabs = st.tabs([section[0] for section in sections])
        for tab, (title, section_key, image_key) in zip(tabs, sections):
            with tab:
                st.image(IMAGES[image_key], width="stretch")
                st.markdown(f"### {title}")
                content = section_content.get(section_key)
                if content:
                    st.markdown(content)
                else:
                    st.info(
                        "This section was not separately identified in "
                        "the AI response. Open 'View Complete Travel Plan' "
                        "below to see the full response."
                    )
        st.markdown("---")
        with st.expander("📄 View Complete Travel Plan", expanded=False):
            st.markdown(plan)
        st.download_button(
            label="⬇️ Download Complete Travel Plan",
            data=plan,
            file_name="Gantavya_AI_Travel_Plan.txt",
            mime="text/plain",
            width="stretch",
        )
        if st.button("➕ Plan Another Trip", width="stretch"):
            st.session_state.travel_plan = None
            st.session_state.travel_request = None
            st.session_state.last_error = None
            st.session_state.requested_route = None
            st.rerun()

# =========================================================

# 13. ABOUT PROJECT PAGE

# =========================================================

elif page == "About Project":
    st.image(IMAGES["hero"], width="stretch")
    st.markdown("## About Gantavya AI")
    st.write(
        """

        **Gantavya AI** is an Agentic AI-Based Travel Planning Assistant

        developed using Python, LangChain, Groq and Streamlit.



        The application coordinates multiple travel tools to search local

        sample datasets, retrieve weather information from an external API,

        estimate trip expenses and prepare a day-wise travel itinerary.

        """
    )
    st.markdown("### How the Application Works")
    st.markdown(
        """

        1. The user enters travel requirements through the Streamlit interface.

        2. Python orchestrates the flight, hotel, attraction, weather and

           budget tools.

        3. The tools retrieve information from JSON datasets and the

           Open-Meteo weather service.

        4. LangChain connects the application to the Groq-hosted language

           model, which synthesizes the collected results into a readable

           travel plan.

        5. Streamlit displays the generated recommendations and provides

           an option to download the plan.

        """
    )
    st.markdown("### Technology Stack")
    tech1, tech2, tech3 = st.columns(3)
    with tech1:
        st.markdown("**Python**")
        st.caption("Core programming language")
    with tech2:
        st.markdown("**LangChain**")
        st.caption("LLM integration and tool workflow")
    with tech3:
        st.markdown("**Groq**")
        st.caption("LLM inference provider")
    tech4, tech5, tech6 = st.columns(3)
    with tech4:
        st.markdown("**Streamlit**")
        st.caption("Interactive web interface")
    with tech5:
        st.markdown("**JSON**")
        st.caption("Sample flight, hotel and attraction data")
    with tech6:
        st.markdown("**Open-Meteo API**")
        st.caption("Weather information")
    st.markdown("---")
    st.markdown("### Project Tools")
    st.markdown(
        """

        - Flight search using a JSON dataset

        - Hotel recommendations using a JSON dataset

        - Tourist attraction search using a JSON dataset

        - Weather forecast using the Open-Meteo API

        - Travel budget calculation

        - AI-generated day-wise travel itinerary

        """
    )
    st.markdown("### Project Objectives")
    st.markdown(
        """

        - Develop an AI-assisted travel planning application.

        - Integrate multiple Python tools into a LangChain workflow.

        - Retrieve weather information from an external API.

        - Estimate travel expenses using user-provided assumptions.

        - Generate structured, day-wise travel recommendations.

        - Build an interactive web application using Streamlit.

        """
    )
    st.markdown("---")
    st.info(
        "Data note: Flight, hotel and attraction records are sample dataset "
        "information, not live inventory. Weather information is retrieved "
        "from an external service. The application does not make bookings."
    )

# =========================================================

# 14. FOOTER

# =========================================================

st.markdown("---")
st.markdown(
    f"""
    <div class="footer">
        <b>{APP_NAME}</b><br>
        Agentic AI-Based Travel Planning Assistant<br>
        Built with Python • LangChain • Groq • Streamlit
    </div>
    """,
    unsafe_allow_html=True,
)
