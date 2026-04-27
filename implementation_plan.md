# Goal Description

Build the high-fidelity FastAPI backend prototype for the Supply Chain Disruption Predictor (SCDP) according to the 28-hour Hackathon Sprint constraints. This includes setting up the API skeleton, defining the Neo4j AuraDB integration for the final consolidated schema, implementing in-memory cascaded risk heuristic paths in Python, setting up mocked API fetchers for Weather and News to save rate limits, and preparing the endpoints for interaction with Gemini 1.5 and the React UI.

## User Review Required

> [!IMPORTANT]  
> Please review the `calculate_cascading_risk` implementation approach detailed below. We will pull components to Python, use standard dictionaries/lists for the topology traversal calculation (instead of heavy external graph libraries to maintain simplicity), and finally perform bulk `UNWIND` Cypher updates back to the DB to ensure speed. Is this acceptable?

> [!NOTE]  
> We have hard-coded the `neo4j+s://` scheme as the default. Neo4j AuraDB requires the driver to connect. Ensure your `.env` contains the active AuraDB credentials before running the mock ingestion endpoints.

## Proposed Changes

### Configuration & Base Environment
Initialize the central `.env` strategy to house credentials for AuraDB and Gemini safely without exposing them in the repo.

#### [NEW] .env
Create an empty template indicating where `NEO4J_URI`, `NEO4J_USER`, `NEO4J_PASSWORD`, and `GEMINI_API_KEY` should be placed. Note that actual keys will never be committed.

---
### Backend Application Core
Modify the `main.py` file to replace the structural boilerplate with the functional, fully-typed mock backend as per the architectural decisions.

#### [MODIFY] main.py
*   **Pydantic Models**: Update models to reflect the required `SimulationRequest` and `MitigationRequest`.
*   **Neo4j Connection**: Configure Driver for AuraDB with standard fast connection settings.
*   **API Fakes / Mocks**: Function `mock_fetch_news_and_weather()` to return hardcoded JSON (e.g., massive strike at Singapore).
*   **Gemini Extraction Logic (Stubbed for now)**: Send the mocked text to Gemini to extract JSON structure (Node ID, Sentiment) using the specified System Prompt 1.
*   **Heuristic Math Engine**: Implement `calculate_cascading_risk_in_memory()`. Pulls all nodes and edges via a Cypher fetch. Loops over dependencies, runs the math: `Local_Risk = (Weather ... )` and `Upstream_Total_Risk = Local_Risk + ...`. Issues `UNWIND` transaction to Neo4j to update `total_risk`.
*   **Endpoints**: Setup complete routes for `GET /api/v1/network`, `POST /api/v1/simulate`, and `POST /api/v1/mitigate`.
*   **APScheduler**: Ensure interval ticking hits the mock functions perfectly every 5 minutes.

## Open Questions

None currently. The exact constraints and choices have been fully outlined perfectly by the user.

## Verification Plan

### Automated Tests
*   Run the FastAPI server locally (`uvicorn main:app --reload`).
*   Confirm APScheduler is logging its tick every 5 mins without crashing.

### Manual Verification
*   We will invoke the `GET /api/v1/network` via browser to ensure Neo4j connection is verified and returning a standard output.
*   We will send a manual cURL / Swagger POST to `POST /api/v1/simulate` with fake payload to observe the logger calculate the Cascading risk purely in memory using the local logic.
