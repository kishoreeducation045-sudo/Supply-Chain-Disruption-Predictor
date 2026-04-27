import logging
import os

from neo4j import GraphDatabase, Driver
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger(__name__)

_driver: Driver | None = None


def get_driver() -> Driver:
    global _driver
    if _driver is None:
        uri = os.getenv("NEO4J_URI", "neo4j+s://localhost:7687")
        user = os.getenv("NEO4J_USER", "neo4j")
        password = os.getenv("NEO4J_PASSWORD", "")
        _driver = GraphDatabase.driver(
            uri,
            auth=(user, password),
            max_connection_pool_size=10,
            connection_timeout=10,
        )
        _driver.verify_connectivity()
        logger.info("Neo4j AuraDB connection verified.")
    return _driver


def close_driver() -> None:
    global _driver
    if _driver is not None:
        _driver.close()
        _driver = None
        logger.info("Neo4j driver closed.")


def get_full_graph() -> dict:
    """Return all Supplier nodes and DEPENDS_ON edges as plain Python dicts."""
    driver = get_driver()
    nodes: list[dict] = []
    edges: list[dict] = []

    with driver.session() as session:
        node_result = session.run(
            """
            MATCH (n:Supplier)
            RETURN
                n.id              AS id,
                n.tier            AS tier,
                n.weather_condition AS weather_condition,
                n.latest_news     AS latest_news,
                n.base_reliability AS base_reliability,
                n.geopolitical_risk AS geopolitical_risk,
                n.local_risk      AS local_risk,
                n.total_risk      AS total_risk
            """
        )
        for record in node_result:
            nodes.append(dict(record))

        edge_result = session.run(
            """
            MATCH (a:Supplier)-[r:DEPENDS_ON]->(b:Supplier)
            RETURN
                a.id          AS source,
                b.id          AS target,
                r.lead_time   AS lead_time,
                r.risk_weight AS risk_weight
            """
        )
        for record in edge_result:
            edges.append(dict(record))

    return {"nodes": nodes, "edges": edges}


def update_node_risks(risk_updates: list[dict]) -> None:
    """Bulk-update local_risk and total_risk for multiple nodes via UNWIND."""
    if not risk_updates:
        return
    driver = get_driver()
    with driver.session() as session:
        session.run(
            """
            UNWIND $updates AS row
            MATCH (n:Supplier {id: row.id})
            SET n.local_risk = row.local_risk,
                n.total_risk = row.total_risk
            """,
            updates=risk_updates,
        )
    logger.info("Bulk risk update applied to %d nodes.", len(risk_updates))
