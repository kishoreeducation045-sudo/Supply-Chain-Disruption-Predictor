import json
import logging
import os

import google.generativeai as genai
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY", ""))
_gemini_model = genai.GenerativeModel("gemini-1.5-flash")

_MOCK_NEWS_PAYLOAD = json.dumps(
    {
        "location": "Singapore",
        "event": "Massive port strike",
        "detail": (
            "Longshoremen at the Port of Singapore have begun an indefinite strike, "
            "halting all cargo operations. Approximately 40% of global container traffic "
            "that transits Singapore is now suspended. Logistics analysts warn of severe "
            "multi-week delays for electronics, semiconductor, and raw-material supply chains."
        ),
        "weather": {
            "condition": "Typhoon",
            "wind_speed_kmh": 185,
            "rainfall_mm": 320,
        },
        "severity_estimate": 0.92,
    }
)


def mock_fetch_news_and_weather() -> str:
    """Return a hardcoded disruption payload — preserves external API rate limits."""
    logger.info("mock_fetch_news_and_weather: returning hardcoded Singapore disruption payload.")
    return _MOCK_NEWS_PAYLOAD


def parse_disaster_scenario(text: str) -> dict:
    """
    Ask Gemini to extract structured disruption data from free-form text.
    Returns {"node_id": str, "severity_score": float}.
    Falls back to safe defaults on any failure.
    """
    system_prompt = (
        "You are a supply chain risk analyst. "
        "Given a disruption description, identify the most affected supplier node ID "
        "(use short identifiers like 'SGP-PORT', 'APAC-HUB', or a city/port code) "
        "and assign a severity_score between 0.0 (no impact) and 1.0 (total disruption). "
        "Respond ONLY with a valid JSON object in this exact format: "
        '{"node_id": "<string>", "severity_score": <float>}'
    )
    full_prompt = f"{system_prompt}\n\nDisruption description:\n{text}"

    try:
        response = _gemini_model.generate_content(full_prompt)
        raw = response.text.strip()
        # Strip markdown code fences if present
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        result = json.loads(raw.strip())
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
