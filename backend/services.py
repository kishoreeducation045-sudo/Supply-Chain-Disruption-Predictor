import json
import logging
import os
import requests

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_gemini_model = genai.GenerativeModel("gemini-2.5-flash")

WEATHER_API_KEY = os.getenv("WEATHER_API_KEY", "")
NEWS_API_KEY = os.getenv("NEWS_API_KEY", "")

def fetch_live_global_intelligence() -> str:
    """Fetch live news and weather, then combine them for Gemini."""
    # 1. Fetch News
    try:
        if not NEWS_API_KEY:
            raise ValueError("NEWS_API_KEY not set")
        news_url = f"https://newsapi.org/v2/everything?q=supply+chain+disruption+OR+port+strike&language=en&sortBy=publishedAt&apiKey={NEWS_API_KEY}"
        news_res = requests.get(news_url, timeout=10)
        news_res.raise_for_status()
        articles = news_res.json().get("articles", [])
        if articles:
            headlines = [article.get("title", "") for article in articles[:3]]
        else:
            headlines = ["No major logistics disruptions reported."]
    except Exception as exc:
        logger.warning("Failed to fetch live news: %s", exc)
        headlines = ["No major logistics disruptions reported."]

    # 2. Fetch Weather
    weather_data = {}
    for city in ["Singapore", "Rotterdam"]:
        try:
            if not WEATHER_API_KEY:
                raise ValueError("WEATHER_API_KEY not set")
            weather_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_API_KEY}"
            weather_res = requests.get(weather_url, timeout=10)
            weather_res.raise_for_status()
            weather_json = weather_res.json()
            condition = weather_json.get("weather", [{}])[0].get("main", "Clear")
            weather_data[city] = condition
        except Exception as exc:
            logger.warning("Failed to fetch weather for %s: %s", city, exc)
            weather_data[city] = "Clear"

    # 3. Combine
    combined_text = (
        "LIVE GLOBAL INTELLIGENCE REPORT:\n"
        f"Recent News Headlines:\n" + "\n".join(f"- {h}" for h in headlines) + "\n\n"
        "Current Weather Conditions:\n"
    )
    for city, cond in weather_data.items():
        combined_text += f"- {city}: {cond}\n"

    logger.info("fetch_live_global_intelligence combined text: \n%s", combined_text)
    return combined_text


def parse_disaster_scenario(text: str) -> dict:
    """
    Ask Gemini to extract structured disruption data from free-form text.
    Returns {"node_id": str, "severity_score": float}.
    Falls back to safe defaults on any failure.
    """
    system_prompt = (
        "You are a supply chain risk analyst. "
        "Given a disruption description, identify the most affected supplier node ID "
        "(use the exact city name mentioned, e.g., 'Singapore', 'Antwerp', 'Shanghai', 'Rotterdam') "
        "and assign a severity_score between 0.0 (no impact) and 1.0 (total disruption). "
        "Respond ONLY with a valid JSON object in this exact format, with no markdown formatting: "
        '{"node_id": "<string>", "severity_score": <float>}'
    )
    full_prompt = f"{system_prompt}\n\nDisruption description:\n{text}"

    try:
        response = _gemini_model.generate_content(full_prompt)
        raw = response.text.strip()
        import re
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)
        result = json.loads(raw)
        result["severity_score"] = float(
            max(0.0, min(1.0, result.get("severity_score", 0.5)))
        )
        logger.info("Gemini parsed scenario: %s", result)
        return result
    except Exception as exc:
        logger.warning("Gemini parse failed (%s). Using safe fallback.", exc)
        return {"node_id": "UNKNOWN", "severity_score": 0.5}


def draft_mitigation_email(failing_node_id: str) -> str:
    """
    Ask Gemini to draft an urgent procurement email for an alternative supplier.
    Returns the drafted email as a plain string.
    """
    prompt = (
        f"You are a senior Procurement Agent. Supplier node '{failing_node_id}' has failed "
        "and poses critical risk to our supply chain. "
        "Draft an urgent, professional email (under 100 words) to an alternative supplier "
        "requesting immediate capacity allocation. Be concise and action-oriented."
    )

    try:
        response = _gemini_model.generate_content(prompt)
        email_text = response.text.strip()
        logger.info("Gemini drafted mitigation email for node '%s'.", failing_node_id)
        return email_text
    except Exception as exc:
        logger.warning("Gemini email draft failed (%s). Returning template.", exc)
        return (
            f"Subject: URGENT — Alternative Supply Request for {failing_node_id}\n\n"
            "Dear Alternative Supplier,\n\n"
            f"Due to a critical failure at node {failing_node_id}, we require immediate "
            "capacity allocation to maintain continuity. Please confirm availability within 24 hours.\n\n"
            "Best regards,\nProcurement Team"
        )
