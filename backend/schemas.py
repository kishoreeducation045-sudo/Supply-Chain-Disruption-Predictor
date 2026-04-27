from pydantic import BaseModel
from typing import List, Optional

class SimulationRequest(BaseModel):
    scenario_text: str

class MitigationRequest(BaseModel):
    failing_node_id: str

class GlobalMetrics(BaseModel):
    global_health: float
    simulated_delta_cost: str
    active_threats: int
    weather_risk_pct: int
    geo_risk_pct: int
    intelligence_stream: List[str]

class NodeSchema(BaseModel):
    id: str
    tier: str
    weather_condition: Optional[str] = "Clear"
    latest_news: Optional[str] = "Normal operations"
    base_reliability: float
    geopolitical_risk: float
    local_risk: float
    total_risk: float

class EdgeSchema(BaseModel):
    source: str
    target: str
    lead_time: float
    risk_weight: float

class NetworkResponse(BaseModel):
    nodes: List[NodeSchema]
    edges: List[EdgeSchema]
    metrics: GlobalMetrics