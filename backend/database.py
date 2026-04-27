import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
AUTH = (os.getenv("NEO4J_USERNAME", "neo4j"), os.getenv("NEO4J_PASSWORD", "password"))

driver = GraphDatabase.driver(URI, auth=AUTH, max_connection_lifetime=200)

def get_full_graph():
    query = """
    MATCH (n:Supplier)
    OPTIONAL MATCH (n)-[r:DEPENDS_ON]->(m:Supplier)
    RETURN n, r, m
    """
    nodes_dict = {}
    edges_list = []
    with driver.session() as session:
        result = session.run(query)
        for record in result:
            n = record["n"]
            if n["id"] not in nodes_dict:
                nodes_dict[n["id"]] = dict(n)
            r = record["r"]
            m = record["m"]
            if r and m:
                edges_list.append({
                    "source": n["id"], "target": m["id"],
                    "lead_time": r.get("lead_time", 0.0), "risk_weight": r.get("risk_weight", 0.1)
                })
    return list(nodes_dict.values()), edges_list

def update_node_risks(updates: list):
    query = """
    UNWIND $updates AS update
    MATCH (n:Supplier {id: update.id})
    SET n.local_risk = update.local_risk, 
        n.total_risk = update.total_risk,
        n.latest_news = update.latest_news,
        n.weather_condition = update.weather_condition
    """
    with driver.session() as session:
        session.run(query, updates=updates)