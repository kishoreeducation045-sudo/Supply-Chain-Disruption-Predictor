import logging

from apscheduler.schedulers.background import BackgroundScheduler
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from database import close_driver, get_full_graph
from engine import calculate_cascading_risk_in_memory, get_global_metrics
from schemas import (
    MitigationRequest,
    MitigationResponse,
    NetworkResponse,
    SimulationRequest,
    SimulationResponse,
)
from services import draft_mitigation_email, mock_fetch_news_and_weather, parse_disaster_scenario

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s — %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Supply Chain Disruption Predictor",
    version="1.0.0",
    description="SCDP hackathon prototype — Neo4j + Gemini 1.5 + FastAPI",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

_scheduler = BackgroundScheduler()


def _scheduled_risk_refresh() -> None:
    """Fetch mock data, parse it with Gemini, then cascade risk scores."""
    logger.info("Scheduled tick: starting risk refresh pipeline.")
    try:
        raw_feed = mock_fetch_news_and_weather()
        parsed = parse_disaster_scenario(raw_feed)
        calculate_cascading_risk_in_memory(
            override_node_id=parsed.get("node_id"),
            override_sentiment=1.0 - parsed.get("severity_score", 0.5),
        )
        logger.info("Scheduled tick complete.")
    except Exception as exc:
        logger.error("Scheduled tick failed: %s", exc)


@app.on_event("startup")
def startup_event() -> None:
    _scheduler.add_job(
        _scheduled_risk_refresh,
        trigger="interval",
        minutes=5,
        id="risk_refresh",
        replace_existing=True,
    )
    _scheduler.start()
    logger.info("APScheduler started — risk refresh every 5 minutes.")


@app.on_event("shutdown")
def shutdown_event() -> None:
    _scheduler.shutdown(wait=False)
    close_driver()
    logger.info("Scheduler and Neo4j driver shut down.")


@app.get("/", tags=["Health"])
def health_check():
    """Health check endpoint to verify the backend is running."""
    return {"status": "SCDP Backend is live. Access /docs for API visualization."}


@app.get("/api/v1/network", response_model=NetworkResponse, tags=["Graph"])
def get_network() -> NetworkResponse:
    """Return the current state of the supply chain graph from Neo4j."""
    try:
        graph = get_full_graph()
    except Exception as exc:
        logger.error("Failed to fetch graph: %s", exc)
        raise HTTPException(status_code=503, detail=f"Neo4j unavailable: {exc}")
    
    metrics = get_global_metrics(graph["nodes"])
    return NetworkResponse(nodes=graph["nodes"], edges=graph["edges"], metrics=metrics)


@app.post("/api/v1/simulate", response_model=SimulationResponse, tags=["Simulation"])
def simulate(request: SimulationRequest) -> SimulationResponse:
    """
    Parse a free-text disruption scenario with Gemini, apply it to the graph,
    then run the cascading risk engine.
    """
    try:
        parsed = parse_disaster_scenario(request.scenario_text)
        node_id = parsed.get("node_id", "UNKNOWN")
        severity = float(parsed.get("severity_score", 0.5))
        calculate_cascading_risk_in_memory(
            override_node_id=node_id,
            override_sentiment=1.0 - severity,
        )
    except Exception as exc:
        logger.error("Simulation failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Simulation error: {exc}")

    return SimulationResponse(
        status="success",
        affected_node_id=node_id,
        severity_score=severity,
        message=f"Cascading risk recalculated. Node '{node_id}' flagged at severity {severity:.2f}.",
    )


@app.post("/api/v1/mitigate", response_model=MitigationResponse, tags=["Mitigation"])
def mitigate(request: MitigationRequest) -> MitigationResponse:
    """Draft an urgent procurement email for the specified failing supplier node."""
    try:
        email = draft_mitigation_email(request.failing_node_id)
    except Exception as exc:
        logger.error("Mitigation drafting failed: %s", exc)
        raise HTTPException(status_code=500, detail=f"Mitigation error: {exc}")

    return MitigationResponse(
        failing_node_id=request.failing_node_id,
        drafted_email=email,
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)
