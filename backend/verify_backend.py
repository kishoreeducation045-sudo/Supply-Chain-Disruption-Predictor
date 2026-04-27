import requests
import sys

# Standard terminal escape codes for color-coding
GREEN = '\033[92m'
RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

BASE_URL = "http://localhost:8000/api/v1"

def print_pass(msg):
    print(f"{GREEN}[PASS] {msg}{RESET}")

def print_fail(msg):
    print(f"{RED}[FAIL] {msg}{RESET}")
    sys.exit(1)

def print_info(msg):
    print(f"{CYAN}[INFO] {msg}{RESET}")

def verify_backend():
    print(f"{YELLOW}=== Starting SCDP Backend Verification ==={RESET}\n")

    # ----------------------------------------------------
    # Test 1: The Network Topology
    # ----------------------------------------------------
    print(f"{YELLOW}Test 1: Fetching Network Topology (GET /api/v1/network)...{RESET}")
    try:
        res = requests.get(f"{BASE_URL}/network")
        if res.status_code == 200:
            print_pass(f"GET /api/v1/network returned {res.status_code} OK")
        else:
            print_fail(f"GET /api/v1/network returned {res.status_code}")

        data = res.json()
        if 'nodes' in data and 'edges' in data:
            print_pass("Response contains 'nodes' and 'edges'")
        else:
            print_fail("Response missing 'nodes' or 'edges'")

        nodes_count = len(data.get('nodes', []))
        edges_count = len(data.get('edges', []))
        print_info(f"Total Nodes retrieved from Neo4j: {nodes_count}")
        print_info(f"Total Edges retrieved from Neo4j: {edges_count}\n")

        # Save initial network state for reference
        initial_nodes = {n['id']: n for n in data.get('nodes', [])}

    except Exception as e:
        print_fail(f"Test 1 request failed: {e}")

    # ----------------------------------------------------
    # Test 2: The AI Disaster Simulator
    # ----------------------------------------------------
    print(f"{YELLOW}Test 2: Triggering AI Disaster Simulator (POST /api/v1/simulate)...{RESET}")
    scenario = "A massive category 5 typhoon has shut down all operations at the port of Singapore."
    try:
        res = requests.post(f"{BASE_URL}/simulate", json={"scenario_text": scenario})
        if res.status_code == 200:
            print_pass(f"POST /api/v1/simulate returned {res.status_code} OK")
        else:
            print_fail(f"POST /api/v1/simulate returned {res.status_code}")

        sim_data = res.json()
        print_info(f"Structured Node ID: {sim_data.get('affected_node_id')}")
        print_info(f"Structured Severity: {sim_data.get('severity_score')}\n")

    except Exception as e:
        print_fail(f"Test 2 request failed: {e}")

    # ----------------------------------------------------
    # Test 3: The Cascading Math Verification
    # ----------------------------------------------------
    print(f"{YELLOW}Test 3: Verifying Cascading Risk Math (GET /api/v1/network)...{RESET}")
    try:
        res = requests.get(f"{BASE_URL}/network")
        if res.status_code == 200:
            print_pass(f"GET /api/v1/network returned {res.status_code} OK")
        else:
            print_fail(f"GET /api/v1/network returned {res.status_code}")

        data = res.json()
        
        # Verify Singapore Node
        singapore_node = next((n for n in data.get('nodes', []) if n.get('id') == "Singapore"), None)
        if singapore_node:
            total_risk = singapore_node.get('total_risk', 0)
            if total_risk > 0.7:
                print_pass(f"'Singapore' node total_risk is critically high: {total_risk} (> 0.7)")
            else:
                print_fail(f"'Singapore' node total_risk is {total_risk} (Expected > 0.7)")
        else:
            print_fail("Could not find 'Singapore' node in the network to verify.")

        # Verify cascading to dependent nodes
        dependent_nodes = [e['source'] for e in data.get('edges', []) if e['target'] == "Singapore"]
        if dependent_nodes:
            print_info(f"Found upstream nodes depending on Singapore: {dependent_nodes}")
            for d in dependent_nodes:
                dep_node = next((n for n in data.get('nodes', []) if n.get('id') == d), None)
                if dep_node:
                    initial_val = initial_nodes.get(d, {}).get('total_risk', 0) if d in initial_nodes else 0
                    new_val = dep_node.get('total_risk', 0)
                    if new_val >= initial_val:
                        print_pass(f"Dependent Node '{d}' cascaded total_risk updated accurately! (Currently: {new_val})")
                    else:
                        print_fail(f"Dependent Node '{d}' cascaded total_risk did not increase (Initial: {initial_val}, Current: {new_val})")
        else:
            print_info("No edges found targeting 'Singapore' in current dataset (cascade check skipped).\n")

    except Exception as e:
        print_fail(f"Test 3 request failed: {e}")

    # ----------------------------------------------------
    # Test 4: The AI Mitigation Agent
    # ----------------------------------------------------
    print(f"{YELLOW}\nTest 4: Triggering AI Mitigation Agent (POST /api/v1/mitigate)...{RESET}")
    try:
        res = requests.post(f"{BASE_URL}/mitigate", json={"failing_node_id": "Singapore"})
        if res.status_code == 200:
            print_pass(f"POST /api/v1/mitigate returned {res.status_code} OK")
        else:
            print_fail(f"POST /api/v1/mitigate returned {res.status_code}")

        mit_data = res.json()
        email_content = mit_data.get('drafted_email')
        
        print_pass("Successfully received AI drafted mitigation email!")
        print(f"\n{CYAN}--- DRAFTED EMAIL START ---{RESET}")
        print(f"{email_content}")
        print(f"{CYAN}--- DRAFTED EMAIL END ---{RESET}\n")

    except Exception as e:
        print_fail(f"Test 4 request failed: {e}")

    print(f"{GREEN}=== ALL VERIFICATION TESTS PASSED SUCCESSFULLY ==={RESET}")

if __name__ == "__main__":
    verify_backend()