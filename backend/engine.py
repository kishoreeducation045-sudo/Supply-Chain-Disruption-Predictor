from database import get_full_graph, update_node_risks

def calculate_cascading_risk_in_memory():
    nodes, edges = get_full_graph()
    node_map = {node["id"]: node for node in nodes}
    
    # Phase 1: Local Risk Baseline (incorporating 30% geopolitical weight)
    updates = []
    for node_id, node in node_map.items():
        reliability = node.get("base_reliability", 0.85)
        geo_risk = node.get("geopolitical_risk", 0.1)
        
        # Base math
        local_risk = ((1.0 - reliability) * 0.7) + (geo_risk * 0.3)
        
        # LLM/Event Override
        if "strike" in str(node.get("latest_news", "")).lower() or "typhoon" in str(node.get("weather_condition", "")).lower() or "disruption" in str(node.get("latest_news", "")).lower():
            local_risk = max(local_risk, 0.9)
            
        node["local_risk"] = round(local_risk, 3)
        node["total_risk"] = round(local_risk, 3) 
        
    # Phase 2: Cascading (1-Level Upstream Propagation)
    decay_factor = 0.6
    for edge in edges:
        source_id = edge["source"]
        target_id = edge["target"]
        weight = edge["risk_weight"]
        if target_id in node_map and source_id in node_map:
            cascade_hit = node_map[target_id]["total_risk"] * weight * decay_factor
            new_total = min(1.0, node_map[source_id]["total_risk"] + cascade_hit)
            node_map[source_id]["total_risk"] = round(new_total, 3)

    # Database Update
    for node in node_map.values():
        updates.append({
            "id": node["id"], "local_risk": node["local_risk"], "total_risk": node["total_risk"],
            "latest_news": node.get("latest_news", "Normal operations"), "weather_condition": node.get("weather_condition", "Clear")
        })
    update_node_risks(updates)

    # Phase 3: Global Metrics Calculation for UI
    avg_risk = sum(n["total_risk"] for n in node_map.values()) / max(1, len(node_map))
    global_health = round((1.0 - avg_risk) * 100, 1)
    daily_loss = f"-${round(avg_risk * 4.2, 1)}M"
    
    stream = []
    for node in node_map.values():
        if node["total_risk"] > 0.7:
            stream.append(f"CRITICAL: {node['id']} reporting severe delays. Impact: HIGH.")
        elif node["total_risk"] > 0.4:
            stream.append(f"WARNING: {node['id']} experiencing friction. Impact: MODERATE.")
    if not stream:
        stream = ["System Normal: Global logistics nodes operating efficiently."]

    metrics = {
        "global_health": global_health, "simulated_delta_cost": daily_loss,
        "active_threats": len([n for n in node_map.values() if n["total_risk"] > 0.7]),
        "weather_risk_pct": int((avg_risk) * 100), "geo_risk_pct": int(sum(n.get("geopolitical_risk",0) for n in node_map.values())/max(1, len(node_map))*100),
        "intelligence_stream": stream[:3]
    }
    return list(node_map.values()), edges, metrics