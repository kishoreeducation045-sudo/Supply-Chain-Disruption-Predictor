from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from apscheduler.schedulers.background import BackgroundScheduler
import schemas
from engine import calculate_cascading_risk_in_memory
from services import fetch_live_global_intelligence, parse_simulation_scenario, draft_mitigation_email

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

scheduler = BackgroundScheduler()
scheduler.add_job(fetch_live_global_intelligence, 'interval', minutes=15)
scheduler.start()

@app.on_event("startup")
def startup():
    calculate_cascading_risk_in_memory()

@app.get("/")
def read_root():
    return {"status": "online", "message": "SCDP Backend API is running. Visit /docs for API documentation."}

@app.get("/api/v1/network", response_model=schemas.NetworkResponse)
def get_network():
    nodes, edges, metrics = calculate_cascading_risk_in_memory()
    return {"nodes": nodes, "edges": edges, "metrics": metrics}

@app.post("/api/v1/simulate")
def simulate(req: schemas.SimulationRequest):
    return {"status": "Success", "data": parse_simulation_scenario(req.scenario_text)}

@app.post("/api/v1/mitigate")
def mitigate(req: schemas.MitigationRequest):
    return {"drafted_action_plan": draft_mitigation_email(req.failing_node_id)}