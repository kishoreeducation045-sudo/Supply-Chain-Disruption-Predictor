import os
import requests
import json
import logging
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
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        data = json.loads(clean_json)
        
        if data.get("node_id") != "None":
            update_node_risks([{
                "id": data["node_id"], "local_risk": data["severity"], "total_risk": data["severity"],
                "latest_news": data["news"], "weather_condition": weather_desc
            }])
        calculate_cascading_risk_in_memory()
    except Exception as e:
        logger.error(f"Gemini Parse Error: {e}")

def parse_simulation_scenario(text: str):
    """User-driven manual simulation via Gemini."""
    prompt = f"""Analyze disaster: '{text}'. Identify node_id and severity (0.0-1.0). Return JSON: {{"node_id": "Node", "severity": 0.9, "news": "Simulated disruption", "weather": "Simulated"}}"""
    response = model.generate_content(prompt)
    try:
        data = json.loads(response.text.replace("```json", "").replace("```", "").strip())
        update_node_risks([{
            "id": data["node_id"], "local_risk": data["severity"], "total_risk": data["severity"],
            "latest_news": data.get("news", "Disrupted"), "weather_condition": data.get("weather", "Bad")
        }])
        calculate_cascading_risk_in_memory()
        return data
    except:
        return {"error": "Failed parse"}

def draft_mitigation_email(node_id: str):
    prompt = f"Draft an urgent 100-word procurement email to find alternate routes bypassing {node_id} due to disruption."
    return model.generate_content(prompt).text