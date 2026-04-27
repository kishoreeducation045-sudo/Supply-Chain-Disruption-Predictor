import os
import pandas as pd
from neo4j import GraphDatabase
from dotenv import load_dotenv

def ingest_data():
    load_dotenv()
    
    uri = os.getenv("NEO4J_URI")
    username = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    if not uri or not username or not password:
        print("Error: Neo4j credentials not found in .env.")
        return

    driver = GraphDatabase.driver(uri, auth=(username, password))
    
    base_dir = os.path.dirname(__file__)
    data_file = os.path.join(base_dir, "data", "global_supply_chain_risk_2026.csv")
    
    try:
        df = pd.read_csv(data_file)
    except FileNotFoundError as e:
        print(f"Error reading CSV file: {e}")
        return

    # Extract Nodes (Ports)
    # We need to get all unique ports from Origin_Port and Destination_Port
    df_origin = df[['Origin_Port', 'Carrier_Reliability_Score', 'Geopolitical_Risk_Score', 'Weather_Condition', 'Date']].rename(columns={'Origin_Port': 'Port'})
    df_dest = df[['Destination_Port', 'Carrier_Reliability_Score', 'Geopolitical_Risk_Score', 'Weather_Condition', 'Date']].rename(columns={'Destination_Port': 'Port'})
    
    df_ports = pd.concat([df_origin, df_dest])
    
    # Process Base Reliability and Geopolitical Risk
    node_stats = df_ports.groupby('Port').agg(
        base_reliability=('Carrier_Reliability_Score', 'mean'),
        geopolitical_risk_score=('Geopolitical_Risk_Score', 'mean')
    ).reset_index()
    
    # Geopolitical risk normalized 0-1
    node_stats['geopolitical_risk'] = node_stats['geopolitical_risk_score'] / 10.0
    
    # Most recent weather condition
    df_ports_sorted = df_ports.sort_values('Date').drop_duplicates('Port', keep='last')
    
    nodes_df = pd.merge(node_stats, df_ports_sorted[['Port', 'Weather_Condition']], on='Port')
    
    nodes_records = []
    for _, row in nodes_df.iterrows():
        nodes_records.append({
            'Node_ID': row['Port'],
            'Tier': 'Tier 1' if 'Shanghai' in row['Port'] or 'Singapore' in row['Port'] else 'Tier 2',
            'Weather_Condition': row['Weather_Condition'],
            'base_reliability': float(row['base_reliability']),
            'geopolitical_risk': float(row['geopolitical_risk'])
        })
        
    # Edge Extraction: Group by Origin and Destination
    edges_df = df.groupby(['Origin_Port', 'Destination_Port']).agg(
        Avg_Lead_Time=('Lead_Time_Days', 'mean'),
        Risk_Score=('Disruption_Occurred', 'mean')
    ).reset_index()

    edges_records = []
    for _, row in edges_df.iterrows():
        edges_records.append({
            'Source': row['Origin_Port'],
            'Target': row['Destination_Port'],
            'Avg_Lead_Time': float(row['Avg_Lead_Time']),
            'Risk_Score': float(row['Risk_Score'])
        })

    wipe_query = "MATCH (n) DETACH DELETE n"

    nodes_query = """
    UNWIND $nodes AS row
    MERGE (n:Supplier {id: row.Node_ID})
    SET n.tier = row.Tier,
        n.weather_condition = row.Weather_Condition,
        n.latest_news = "",
        n.base_reliability = row.base_reliability,
        n.geopolitical_risk = row.geopolitical_risk,
        n.local_risk = 0.0,
        n.total_risk = 0.0
    """

    edges_query = """
    UNWIND $edges AS row
    MATCH (source:Supplier {id: row.Source})
    MATCH (target:Supplier {id: row.Target})
    MERGE (source)-[r:DEPENDS_ON]->(target)
    SET r.lead_time = toFloat(row.Avg_Lead_Time),
        r.risk_weight = toFloat(row.Risk_Score)
    """

    try:
        with driver.session() as session:
             print("Wiping existing Neo4j database...")
             session.run(wipe_query)
             
             print(f"Ingesting {len(nodes_records)} Supplier nodes...")
             session.run(nodes_query, nodes=nodes_records)
             print("Successfully ingested nodes.")
             
             print(f"Creating {len(edges_records)} DEPENDS_ON edges...")
             session.run(edges_query, edges=edges_records)
             print("Successfully created edges.")
    except Exception as e:
        print(f"Error executing Cypher queries: {e}")
    finally:
        driver.close()

if __name__ == "__main__":
    print("Starting raw CSV data ingestion to Neo4j...")
    ingest_data()
    print("Data ingestion complete.")
