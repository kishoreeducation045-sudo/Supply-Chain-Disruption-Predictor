import logging
from collections import defaultdict

from database import get_full_graph, update_node_risks

logger = logging.getLogger(__name__)

_WEATHER_SEVERITY_MAP: dict[str, float] = {
    "typhoon": 1.0,
    "hurricane": 1.0,
    "flood": 0.8,
    "storm": 0.7,
    "rain": 0.3,
    "fog": 0.2,
    "clear": 0.0,
    "normal": 0.0,
}

_DECAY = 0.5


def _weather_severity(condition: str) -> float:
    return _WEATHER_SEVERITY_MAP.get(condition.lower().strip(), 0.1)


def calculate_cascading_risk_in_memory(
    override_node_id: str | None = None,
    override_sentiment: float | None = None,
) -> None:
    """
    Pull the full graph from Neo4j, compute cascading risk scores purely in
    Python, then push all updated values back via a single UNWIND transaction.

    Math:
        local_risk  = (weather_severity * 0.5) + ((1 - sentiment_score) * 0.5)
        total_risk  = local_risk + sum(child.total_risk * edge.risk_weight * DECAY)
        All values capped at 1.0.
    """
    logger.info("Starting in-memory cascading risk calculation.")
    graph = get_full_graph()

    # Index nodes by id for O(1) lookup
    node_map: dict[str, dict] = {n["id"]: dict(n) for n in graph["nodes"]}

    # Build adjacency: parent -> list of (child_id, risk_weight)
    # Edge direction: (source)-[:DEPENDS_ON]->(target)
    # source depends ON target, so target is the upstream supplier (child).
    children: dict[str, list[tuple[str, float]]] = defaultdict(list)
    parents: dict[str, list[str]] = defaultdict(list)
    for edge in graph["edges"]:
        src, tgt = edge["source"], edge["target"]
        weight = float(edge.get("risk_weight") or 0.0)
        children[src].append((tgt, weight))
        parents[tgt].append(src)

    # Apply override from a live simulation event
    if override_node_id and override_node_id in node_map:
        node_map[override_node_id]["_sentiment_override"] = override_sentiment or 0.0

    # Compute local_risk for every node
    for node_id, node in node_map.items():
        condition = node.get("weather_condition") or "normal"
        weather_sev = _weather_severity(condition)
        # Use overridden sentiment if present; default neutral 0.5
        sentiment = node.pop("_sentiment_override", 0.5)
        geo_risk = node.get("geopolitical_risk", 0.0)
        node["local_risk"] = round(min(weather_sev * 0.3 + (1.0 - sentiment) * 0.4 + geo_risk * 0.3, 1.0), 4)
        node["total_risk"] = node["local_risk"]  # seed before cascade

    # Topological cascade: propagate from leaves (no children) upward.
    # We use iterative BFS from leaf nodes to ensure correct ordering.
    in_degree = {n: len(children[n]) for n in node_map}
    queue = [n for n, deg in in_degree.items() if deg == 0]
    processed: set[str] = set()

    while queue:
        node_id = queue.pop(0)
        if node_id in processed:
            continue
        processed.add(node_id)

        # Propagate this node's total_risk to its dependents (parents)
        for parent_id in parents[node_id]:
            edge_weight = next(
                w for (c, w) in children[parent_id] if c == node_id
            )
            contribution = node_map[node_id]["total_risk"] * edge_weight * _DECAY
            node_map[parent_id]["total_risk"] = round(
                min(node_map[parent_id]["total_risk"] + contribution, 1.0), 4
            )
            in_degree[parent_id] -= 1
            if in_degree[parent_id] == 0:
                queue.append(parent_id)

    risk_updates = [
        {"id": nid, "local_risk": n["local_risk"], "total_risk": n["total_risk"]}
        for nid, n in node_map.items()
    ]
    update_node_risks(risk_updates)
    logger.info("Cascading risk calculation complete. %d nodes updated.", len(risk_updates))


def get_global_metrics(nodes: list[dict]) -> dict:
    if not nodes:
        return {"global_health": 1.0, "threat_streams": 0, "avg_risk_percentage": 0.0}
    
    total_risk_sum = sum(n.get("total_risk", 0.0) for n in nodes)
    avg_risk = total_risk_sum / len(nodes)
    
    threat_streams = sum(1 for n in nodes if n.get("total_risk", 0.0) > 0.7)
    global_health = max(0.0, 1.0 - avg_risk)
    
    return {
        "global_health": round(global_health, 2),
        "threat_streams": threat_streams,
        "avg_risk_percentage": round(avg_risk * 100, 1)
    }
