import pandas as pd
import os
from neo4j import GraphDatabase
from dotenv import load_dotenv

load_dotenv()
driver = GraphDatabase.driver(os.getenv("NEO4J_URI"), auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD")))

def ingest_data():
    print("Reading Data...")
    try:
        # Load CSV
        df = pd.read_csv("data/global_supply_chain_risk_2026.csv")
        
        # Synthesize Nodes (use copy to avoid view issues)
        origins = df[['Origin_Port', 'Carrier_Reliability_Score', 'Geopolitical_Risk_Score', 'Weather_Condition']].rename(columns={'Origin_Port': 'Node'}).copy()
        dests = df[['Destination_Port', 'Carrier_Reliability_Score', 'Geopolitical_Risk_Score', 'Weather_Condition']].rename(columns={'Destination_Port': 'Node'}).copy()
        
        all_nodes_df = pd.concat([origins, dests]).groupby('Node').agg({
            'Carrier_Reliability_Score': 'mean', 
            'Geopolitical_Risk_Score': 'mean', 
            'Weather_Condition': 'last'
        }).reset_index()

        # Prepare node data for batching
        nodes_data = []
        for _, row in all_nodes_df.iterrows():
            geo_risk = min(row['Geopolitical_Risk_Score'] / 10.0, 1.0)
            nodes_data.append({
                "id": str(row['Node']),
                "weather": str(row['Weather_Condition']),
                "rel": float(row['Carrier_Reliability_Score']),
                "geo": float(geo_risk)
            })

        # Prepare edge data for batching
        edges_data = []
        for _, row in df.iterrows():
            risk_wt = float(row['Disruption_Occurred']) if 'Disruption_Occurred' in df.columns else 0.5
            edges_data.append({
                "src": str(row['Origin_Port']),
                "tgt": str(row['Destination_Port']),
                "lt": float(row['Lead_Time_Days']),
                "rw": float(risk_wt)
            })

        with driver.session() as session:
            print("Wiping existing data...")
            session.run("MATCH (n) DETACH DELETE n")
            
            print(f"Creating {len(nodes_data)} nodes...")
            session.run("""
                UNWIND $nodes AS node
                CREATE (n:Supplier {
                    id: node.id, 
                    tier: 'Tier 1', 
                    weather_condition: node.weather, 
                    latest_news: 'Normal',
                    base_reliability: node.rel, 
                    geopolitical_risk: node.geo, 
                    local_risk: 0.0, 
                    total_risk: 0.0
                })
            """, nodes=nodes_data)
            
            print(f"Creating {len(edges_data)} relationships...")
            session.run("""
                UNWIND $edges AS edge
                MATCH (s:Supplier {id: edge.src}), (t:Supplier {id: edge.tgt})
                MERGE (s)-[:DEPENDS_ON {lead_time: edge.lt, risk_weight: edge.rw}]->(t)
            """, edges=edges_data)

        print("Ingestion Complete!")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    ingest_data()