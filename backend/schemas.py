from pydantic import BaseModel, Field


class SimulationRequest(BaseModel):
    scenario_text: str = Field(
        ...,
        min_length=3,
        description="Free-text description of the disruption scenario, e.g. 'Typhoon in Singapore'.",
    )


class MitigationRequest(BaseModel):
    failing_node_id: str = Field(
        ...,
        min_length=1,
        description="The graph node ID of the supplier that is failing.",
    )


class NodeSchema(BaseModel):
    id: str
    tier: str
    weather_condition: str
    latest_news: str
    base_reliability: float
    geopolitical_risk: float
    local_risk: float
    total_risk: float


class EdgeSchema(BaseModel):
    source: str
    target: str
    lead_time: float
    risk_weight: float


class GlobalMetrics(BaseModel):
    global_health: float
    threat_streams: int
    avg_risk_percentage: float


class NetworkResponse(BaseModel):
    nodes: list[NodeSchema]
    edges: list[EdgeSchema]
    metrics: GlobalMetrics


class SimulationResponse(BaseModel):
    status: str
    affected_node_id: str
    severity_score: float
    message: str


class MitigationResponse(BaseModel):
    failing_node_id: str
    drafted_email: str
