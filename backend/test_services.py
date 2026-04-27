import os
import requests
from dotenv import load_dotenv
from services import fetch_live_global_intelligence, parse_simulation_scenario, draft_mitigation_email

load_dotenv()

def diagnostic():
    print("--- SCDP External Service Diagnostic ---")
    
    # 1. Live Intelligence / Gemini Test
    print("[AI] Fetching live risk synthesis (this hits Gemini)...")
    try:
        fetch_live_global_intelligence()
        print("[SUCCESS] Live intelligence pipeline executed without crashing.")
    except Exception as e:
        print(f"[!] Warning: Risk synthesis failed: {e}")

    # 2. Simulation Test
    print("\n[AI] Testing Simulation Parsing...")
    try:
        sim_result = parse_simulation_scenario("A major category 5 hurricane is approaching the Port of Miami, causing severe disruptions.")
        print(f"[SUCCESS] Simulation Result: {sim_result}")
    except Exception as e:
        print(f"[!] Warning: Simulation parsing failed: {e}")

    # 3. Mitigation Draft Test
    print("\n[AI] Testing Mitigation Drafting...")
    try:
        draft = draft_mitigation_email("Miami")
        print(f"[SUCCESS] Draft Output: {draft[:100]}...")
    except Exception as e:
        print(f"[!] Warning: Mitigation drafting failed: {e}")

if __name__ == "__main__":
    diagnostic()
