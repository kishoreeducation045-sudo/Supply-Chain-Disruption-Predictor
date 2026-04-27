import os
import requests
import json
import logging
import re
import google.generativeai as genai
from database import update_node_risks
from engine import calculate_cascading_risk_in_memory
from dotenv import load_dotenv

load_dotenv()
logger = logging.getLogger(__name__)

genai.configure(api_key=os.getenv("GEMINI_API_KEY"))
model = genai.GenerativeModel('gemini-1.5-flash')
NEWS_KEY = os.getenv("NEWS_API_KEY")
WEATHER_KEY = os.getenv("WEATHER_API_KEY")

def fetch_live_global_intelligence():
    """Live API Fetcher with Fallbacks."""
    logger.info("Fetching live logistics intelligence...")
    
    # 1. Fetch News
    try:
        url = f"https://newsapi.org/v2/everything?q=supply+chain+OR+port+strike&language=en&apiKey={NEWS_KEY}"
        news_res = requests.get(url).json()
        headlines = [a['title'] for a in news_res.get('articles', [])[:3]]
    except:
        headlines = ["Operations normal across global ports."]

    # 2. Fetch Weather (Sample Node)
    try:
        w_url = f"https://api.openweathermap.org/data/2.5/weather?q=Singapore&appid={WEATHER_KEY}"
        w_res = requests.get(w_url).json()
        weather_desc = w_res['weather'][0]['description']
    except:
        weather_desc = "Clear"

    prompt = f"""
    Analyze these headlines: {headlines} and Singapore weather: {weather_desc}.
    Identify a major disruption node_id (e.g., Singapore, Rotterdam, Shanghai).
    Assign a severity (0.0 to 1.0). Return strict JSON: {{"node_id": "Port", "severity": 0.8, "news": "Summary"}}
    If no disruption, return {{"node_id": "None", "severity": 0.0, "news": "Normal"}}
    """
    try:
        response = model.generate_content(prompt)
        clean_text = response.text.replace("```json", "").replace("```", "").strip()
        start_idx = clean_text.find("{")
        end_idx = clean_text.rfind("}") + 1
        clean_json = clean_text[start_idx:end_idx] if start_idx != -1 else clean_text
        data = json.loads(clean_json)
        
        if data.get("node_id") != "None":
            update_node_risks([{
                "id": data["node_id"], "local_risk": data["severity"], "total_risk": data["severity"],
                "latest_news": data["news"], "weather_condition": weather_desc
            }])
        calculate_cascading_risk_in_memory()
    except Exception as e:
        logger.error(f"Gemini Parse Error: {e}")

def parse_simulation_scenario(text: str) -> dict:
    """
    Extracts location, fetches LIVE API data, and asks Gemini to compare 
    the hypothetical threat against the live reality to generate a Markdown report.
    """
    try:
        # 1. Quick extraction of the target location
        loc_prompt = f"Extract the single main city name from this threat: '{text}'. Return ONLY the city name, nothing else."
        loc_response = model.generate_content(loc_prompt)
        city = loc_response.text.strip()

        # 2. Fetch Live Reality Data (with safe fallbacks so it never crashes)
        weather_data = "Clear"
        news_data = "No major news"
        
        try:
            w_url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={WEATHER_KEY}"
            w_res = requests.get(w_url).json()
            weather_data = w_res['weather'][0]['description']
        except Exception:
            pass # Fails safely if API key is missing or limit reached

        try:
            n_url = f"https://newsapi.org/v2/everything?q={city}+supply+chain&apiKey={NEWS_KEY}"
            n_res = requests.get(n_url).json()
            news_data = [a['title'] for a in n_res.get('articles', [])[:2]]
        except Exception:
            pass

        # 3. Final Analysis & Markdown Generation
        system_prompt = (
            "You are a supply chain risk analyst. "
            f"Analyze this hypothetical threat: '{text}'. "
            f"Compare it against this LIVE data for {city}: Weather='{weather_data}', News='{news_data}'. "
            "Prioritize the LIVE data for the immediate 'severity_score' (0.0 to 1.0). "
            "Write a comprehensive 2-paragraph Markdown report that analyzes the current reality and assesses the hypothetical threat as a near-future projection. "
            "Respond ONLY with a valid JSON object in this exact format, with NO markdown blocks outside the JSON: "
            '{"node_id": "<exact_city_name>", "severity_score": <float>, "markdown_report": "<string>"}'
        )

        response = model.generate_content(system_prompt)
        raw = response.text.strip()
        
        # Clean the JSON from any markdown formatting Gemini might add
        match = re.search(r'\{.*\}', raw, re.DOTALL)
        if match:
            raw = match.group(0)

        result = json.loads(raw)
        
        # Ensure severity is a float between 0 and 1
        result["severity_score"] = float(max(0.0, min(1.0, result.get("severity_score", 0.5))))

        update_node_risks([{
            "id": result.get("node_id", city), 
            "local_risk": result["severity_score"], 
            "total_risk": result["severity_score"],
            "latest_news": "Simulated Threat + Live Data", 
            "weather_condition": weather_data
        }])
        calculate_cascading_risk_in_memory()

        logger.info(f"Gemini successfully parsed scenario for {city}.")
        return result

    except Exception as exc:
        logger.warning(f"Gemini live parse failed ({exc}). Using safe fallback.")
        return {
            "node_id": "UNKNOWN",
            "severity_score": 0.5,
            "markdown_report": "### Threat Analysis Error\nFailed to process live threat intelligence. Please ensure API keys are valid and try again."
        }

def draft_mitigation_email(node_id: str):
    prompt = f"Draft an urgent 100-word procurement email to find alternate routes bypassing {node_id} due to disruption."
    return model.generate_content(prompt).text