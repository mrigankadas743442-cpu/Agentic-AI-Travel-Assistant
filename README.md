# ✈️ Gantavya AI – Agentic AI Travel Planning Assistant

![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)
![LangChain](https://img.shields.io/badge/LangChain-Framework-green.svg)
![Groq](https://img.shields.io/badge/Groq-LLM-orange.svg)
![Streamlit](https://img.shields.io/badge/Streamlit-Web%20App-red.svg)
![Status](https://img.shields.io/badge/Status-Deployed-success.svg)

## 🌐 Live Demo

👉 [Gantavya AI – Live Application](https://agentic-ai-travel-assistant-743442.streamlit.app/)

## 📌 Project Overview

**Gantavya AI** is an Agentic AI-based Travel Planning Assistant developed using Python, LangChain, Groq, and Streamlit.

The application helps users plan trips by gathering flight, hotel, tourist attraction, and weather information, estimating travel expenses, and generating a personalized day-wise travel itinerary.

It combines Python-based tool orchestration with an LLM-powered response-generation workflow to simplify travel planning.

## 🎯 Problem Statement

Planning a trip often requires searching across multiple platforms for flights, accommodation, tourist attractions, weather conditions, and estimated expenses.

This process can be time-consuming and difficult to organize.

Gantavya AI addresses this challenge by bringing essential travel-planning features together in one application. It processes user requirements, executes relevant tools, and generates a structured travel plan.

## ✨ Key Features

- ✈️ **Flight Search:** Search for available sample flight information based on departure city, destination, and budget.
- 🏨 **Hotel Search:** Find sample hotel information using city, price, star rating, and amenity preferences.
- 📍 **Tourist Attraction Search:** Discover tourist attractions based on destination, place type, and minimum rating.
- 🌤️ **Weather Forecast:** Retrieve weather forecast information using the Open-Meteo API.
- 💰 **Trip Budget Estimation:** Calculate estimated travel expenses based on the number of travelers, trip duration, accommodation, food, transportation, and activities.
- 🗓️ **Day-wise Itinerary:** Generate an organized travel itinerary based on the collected information.
- 🤖 **AI-Powered Travel Assistance:** Use Groq LLM to synthesize tool results into a structured travel-planning response.
- 📊 **Interactive Web Interface:** Access travel-planning functionality through a Streamlit application.

## 🛠️ Technologies Used

| Technology | Purpose |
|---|---|
| Python | Core programming language |
| LangChain | Tool integration and orchestration |
| Groq | LLM-powered response generation |
| OpenAI GPT-OSS 20B (via Groq) | Language model |
| Streamlit | Web application interface |
| JSON | Local sample datasets |
| Open-Meteo API | Weather forecast information |
| Requests | External API communication |

## ⚙️ Application Architecture

The application follows a Python-based tool orchestration workflow.

1. **User Input:** The user provides travel requirements, including departure city, destination, number of travelers, trip duration, and budget preferences.
2. **Tool Execution:** Python executes the relevant travel tools to retrieve flight, hotel, tourist attraction, weather, and budget information.
3. **Data Collection:** Flight, hotel, and attraction information is retrieved from local JSON datasets, while weather information is obtained from the Open-Meteo API.
4. **AI Processing:** LangChain connects the application workflow with the Groq language model to synthesize the collected information.
5. **Travel Plan Generation:** The model generates a structured travel-planning response, including a day-wise itinerary.
6. **Result Display:** Streamlit displays the generated travel plan to the user.

## 🔧 Project Tools

The application includes five Python-based tools:

### 1. ✈️ Flight Search Tool
- Searches sample flight information.
- Uses departure and destination cities.
- Supports maximum-price filtering.

### 2. 🏨 Hotel Search Tool
- Searches sample hotel information.
- Supports city-based searching.
- Filters hotels by maximum price, minimum star rating, and required amenities.

### 3. 📍 Tourist Attraction Search Tool
- Retrieves tourist attraction information.
- Supports filtering by place type and minimum rating.

### 4. 🌤️ Weather Forecast Tool
- Retrieves weather forecast information using the Open-Meteo API.
- Supports configurable forecast duration.

### 5. 💰 Trip Budget Estimation Tool
- Estimates total trip expenses.
- Considers flight, hotel, food, transportation, and activity costs.
- Includes a 10% contingency allowance.

## 💵 Budget Estimation

The budget estimation tool calculates approximate travel expenses using the following components:

- Flight cost per person
- Hotel price per night
- Food cost per person per day
- Transportation cost per day
- Activity cost per person per day
- Number of travelers
- Total trip duration

The calculation assumes one hotel room, with accommodation nights calculated as trip days minus one. A 10% contingency allowance is added to the estimated expenses.

## 📂 Project Structure

```text
Agentic_AI_Travel_Assistant/
│
├── agent/
│   ├── __init__.py
│   ├── prompts.py
│   └── travel_agent.py
│
├── tools/
│   ├── __init__.py
│   ├── flight_tool.py
│   ├── hotel_tool.py
│   ├── places_tool.py
│   ├── weather_tool.py
│   └── budget_tool.py
│
├── data/
│   ├── flights.json
│   ├── hotels.json
│   └── places.json
│
├── app.py
├── requirements.txt
└── .gitignore
```

## ☁️ Deployment

The application is deployed using **Streamlit Community Cloud**.
![Gantavya AI – Live Deployment](<img width="1244" height="1089" alt="Gantavya AI Travel Planner Dashboard" src="https://github.com/user-attachments/assets/7e1a1a9a-eecd-47e3-9c02-71dacb8f361f" />
)

Live application:

👉 [https://agentic-ai-travel-assistant-743442.streamlit.app/](https://agentic-ai-travel-assistant-743442.streamlit.app/)

For deployment, configure the GitHub repository and main file (`app.py`) in Streamlit Community Cloud.



## ⚠️ Limitations

- Flight, hotel, and tourist attraction information comes from local JSON sample datasets.
- Sample flights and hotels do not represent live availability or confirmed bookings.
- Flight dates and fares may be historical and should not be treated as current prices.
- Weather forecasts depend on the availability and coverage of the external Open-Meteo service.
- Budget estimates depend on sample prices and user-provided daily expense assumptions.
- The application provides travel-planning assistance; it does not book flights, hotels, or activities.

## 🔮 Future Improvements

- Integration with live flight and hotel APIs
- Real-time booking and availability support
- Interactive maps and route visualization
- More detailed destination recommendations
- Currency conversion and multi-currency budgets
- User accounts and saved travel plans
- Improved itinerary personalization

## 👨‍💻 Author

**Mriganka Das**

MCA Graduate | AI/ML & Data Science Enthusiast

- **GitHub:** [mrigankadas743442-cpu](https://github.com/mrigankadas743442-cpu)
- **Project Repository:** [Agentic-AI-Travel-Assistant](https://github.com/mrigankadas743442-cpu/Agentic-AI-Travel-Assistant)
