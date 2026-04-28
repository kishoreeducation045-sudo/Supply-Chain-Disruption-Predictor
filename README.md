# Supply Chain Disruption Predictor (SCDP) 

A comprehensive AI-powered risk management platform that maps multi-tier supplier relationships and integrates live global intelligence (News, Weather, Geopolitics) to predict and mitigate supply chain disruptions.

## Features

- **Real-time Risk Monitoring**: Aggregates data from global news APIs and weather services to detect emerging threats.
- **AI-Powered Simulation**: Uses Gemini to analyze geopolitical events, natural disasters, and port strikes, calculating cascading risk propagation through the supply chain graph.
- **Predictive Analytics**: Identifies high-risk suppliers and calculates "Time to Impact" to enable proactive decision-making.
- **Mitigation Automation**: Generates optimized alternative routing suggestions and drafts executive summary reports and mitigation emails instantly.
- **Interactive Visualization**: Visualizes the global supply chain network with live risk scoring and node-level health monitoring.

## Tech Stack

### Backend
- **Framework**: [FastAPI](https://fastapi.tiangolo.com/)
- **Database**: [Neo4j](https://neo4j.com/) (Graph Database)
- **AI / ML**:
  - [Google GenAI (Gemini 2.5 Flash)](https://ai.google.dev/gemini-api)
  - Graph Algorithms (Cascading Risk Propagation)
- **Data Processing**: [Pandas](https://pandas.pydata.org/)

### Frontend
- **Framework**: [React](https://react.dev/)
- **Build Tool**: [Vite](https://vitejs.dev/)
- **Visualization**: [React Flow](https://reactflow.dev/) (Custom Graph Rendering)
- **Styling**: [Tailwind CSS](https://tailwindcss.com/)
- **Charts**: [Recharts](https://recharts.org/)

## Project Structure

```
supply-chain-disruption-predictor/
├── backend/                # FastAPI Application & Core Logic
│   ├── main.py             # API Entry Point
│   ├── engine.py           # Risk Calculation & threat Mitigation
│   ├── services.py         # External API Integrations (News, Weather)
│   ├── database.py         # Neo4j Connection & Queries
│   └── schemas.py          # Pydantic Data Models
├── frontend/               # React Application
│   ├── src/                # Source Code
│   │   ├── components/     # UI Components (Graph, Sidebar, etc.)
│   │   ├── services/       # API Client
│   │   ├── App.jsx         # Main App Container
│   │   └── main.jsx        # Entry Point
│   ├── package.json        # Dependencies
│   └── vite.config.js      # Vite Configuration
├── data/                   # Dataset
│   └── global_supply_chain_risk_2026.csv
└── .env                    # Environment variables (API Keys, DB Config)
```

## Setup & Installation

### Prerequisites
- [Python 3.8+](https://www.python.org/downloads/)
- [Node.js 16+](https://nodejs.org/)
- [Neo4j Database](https://neo4j.com/download/)

### 1. Backend Setup

1. Navigate to the backend directory:
   ```bash
   cd backend
   ```

2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

3. Configure environment variables:
   Create a `.env` file in the `backend/` directory with the following:
   ```env
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USERNAME=neo4j
   NEO4J_PASSWORD=your_neo4j_password
   GEMINI_API_KEY=your_gemini_api_key
   NEWS_API_KEY=your_news_api_key
   WEATHER_API_KEY=your_weather_api_key
   ```

4. (Optional) Ingest the dataset into Neo4j:
   ```bash
   python ingest.py
   ```
   *Note: Ensure your Neo4j database is running before running this command.*

5. Run the server:
   ```bash
   python -m uvicorn main:app --reload
   ```

### 2. Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Start the development server:
   ```bash
   npm run dev
   ```

## Usage

1. Open your browser and navigate to `http://localhost:5173`.
2. **Interact with the Graph**: Click on any node (supplier) to view detailed metrics and news.
3. **Run Simulation**: Use the "Risk Dashboard" sidebar to input a disruption scenario (e.g., "Port closure in Miami"). The system will calculate the impact and suggest alternative routes.
4. **Monitor Status**: Check the "Live Metrics" panel for the global health score and active threats.

## Project Documentation

For detailed information about the project architecture, setup, and development guidelines, please refer to the [Project Documentation](LINK_TO_YOUR_DETAILED_DOCS).

---
*Built with ❤️ for Supply Chain Resilience.*
