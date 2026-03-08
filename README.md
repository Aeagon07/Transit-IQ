# 🚀 Transit-IQ: Predictive Urban Mobility & Fleet Optimizer

**Transit-IQ** is a comprehensive, closed-loop public transport intelligence system. It transitions municipal transit from being a *reactionary* service to a *predictive* one. By modeling a city's transport network using real GTFS data, applying time-series Machine Learning to forecast crowd sizes, and utilizing Operations Research (Constraint Programming), Transit-IQ dynamically rebalances bus fleets to minimize passenger wait times and optimize fuel efficiency.

Built for **Problem Statement 4 [PS4] - Public Transport Demand & Fleet Optimizer**.

---

## 🔥 Key Features

- **Predictive Demand Heatmap:** Anticipates crowd surges at specific bus stops hours before they happen using daily/weekly seasonality.
- **Multi-Objective Fleet Optimization:** Calculates Pareto-optimal fleet distribution strategies (Time-Optimal vs. Fuel-Optimal) dynamically.
- **RAPTOR Journey Planner:** A passenger-facing routing engine that finds the mathematically fastest, fewest-transfer path through the transit graph.
- **Live Anomaly Detection:** An unsupervised real-time ML guardrail that alerts operators to statistically abnormal crowd surges (e.g., flash protests or local events).
- **Time-of-Day Comparisons:** Dynamically compares predicted demand curves for Morning Peaks, Evening Peaks, and Weekends routes.

---

## 🏗️ System Architecture

```mermaid
graph TD
    subgraph Data Layer
        GTFS[(Pune GTFS Data)] --> Loader[GTFS Loader & Graph Builder]
        Synth[(Historical Ticket Data)] --> DataLoader[Time-Series Data Loader]
    end

    subgraph Intelligence Core 🧠
        DataLoader --> HybridForecaster((Prophet + XGBoost Hybrid Forecaster))
        Loader --> RaptorEngine([RAPTOR Routing Engine])
        HybridForecaster --> Optimizer{Google OR-Tools Optimizer}
        LiveSim[Live Event Loop Simulation] --> IsolationForest((IsolationForest Anomaly Detector))
        HybridForecaster -.-> IsolationForest
    end

    subgraph Backend API (FastAPI)
        HybridForecaster --> DemandAPI[/api/demand/]
        Optimizer --> TradeoffAPI[/api/optimize/]
        RaptorEngine --> RouteAPI[/api/route/]
        IsolationForest --> AlertAPI[/api/alerts]
    end

    subgraph Frontend (React + Vite)
        DemandAPI --> Dashboard[Operator Dashboard UI]
        TradeoffAPI --> Dashboard
        AlertAPI --> Dashboard
        RouteAPI --> Passenger[Passenger Mobile App UI]
    end
```

---

## 🧠 Core Machine Learning & Algorithms

We utilized 4 distinct algorithmic engines to solve the core objective of the hackathon:

### 1. Hybrid Demand Forecaster (Facebook Prophet + XGBoost)
To predict how many people will be waiting at a bus stop, we didn't just use historical averages.
*   **Prophet:** Captures cyclical time-series data (e.g., the massive Monday morning surge to the IT Park, the weekend drop-off).
*   **XGBoost:** Prophet fails when external anomalies occur. We layered XGBoost to correct Prophet's residuals in real-time by analyzing external variables like sudden heavy rainfall or local events, drastically improving overall prediction accuracy.

### 2. Fleet Rebalancing (Google OR-Tools)
Predicting crowds is only half the battle. We used **Google OR-Tools** (Constraint Programming) to solve the complex fleet allocation problem.
*   The optimizer takes the forecasted passenger count and physical bus capacity constraints.
*   It outputs a **Pareto Frontier** offering three strict deployment strategies:
    *   *Time-Optimal:* Dispatch maximum buses to crush passenger wait times.
    *   *Fuel-Optimal:* Dispatch minimum buses to save municipal diesel.
    *   *Balanced:* The mathematical sweet spot (recommended).

### 3. Passenger Routing (RAPTOR Algorithm)
When a passenger wants to go from Point A to Point B, we actively **rejected Dijkstra/A***.
*   Dijkstra is designed for cars navigating static physical roads—it is blind to bus timetables.
*   We implemented **RAPTOR (Round-Based Public Transit Optimized Router)**. Invented by Microsoft Research specifically for GTFS data, RAPTOR operates in "rounds" (transfers) to guarantee the optimal path that minimizes *both* physical travel time AND the number of frustrating bus transfers.

### 4. Live Safety Net (Scikit-Learn IsolationForest)
What if an unannounced protest happens that the ML couldn't predict?
*   We run an **Isolation Forest** (Unsupervised ML algorithm) constantly in our heavily-multithreaded backend event loop.
*   It compares the live ticket-sales tally against Prophet's predicted baseline. If a coordinate deviates wildly into the outer branches of the mathematical "forest" (e.g., a 280% undocumented passenger surge), it instantly throws a Critical Red Alert to the Operator Dashboard to bypass the AI and dispatch emergency fleets manually.

---

## 🗄️ Datasets Used

*   **Pune PMPML GTFS Dataset:** We utilized real-world public General Transit Feed Specification (GTFS) data from the Pune Municipal Corporation.
    *   `routes.txt`: Modeled distinct physical bus routes (up/down paths).
    *   `stops.txt`: Extracted and mapped exact GPS coordinates for hundreds of real bus stops across the city (e.g., Shivaji Nagar, Wakad, Hinjewadi).
*   **Synthetic Historical Demand:** Since real-time ticket sales data is proprietary, we built a Python generation engine mapping standard deviation curves onto the GTFS stops to train the Prophet and Isolation Forest models over a dense simulated timeline.

---

## 📂 Project Structure

```text
📦 Transit-IQ
 ┣ 📂 backend/                 # Python FastAPI Server
 ┃ ┣ 📂 data/
 ┃ ┃ ┣ 📂 gtfs/                # Real Pune PMPML GTFS text files
 ┃ ┃ ┣ 📜 gtfs_loader.py       # Parses GTFS into memory graphs
 ┃ ┃ ┗ 📜 synthetic_gtfs.py    # Simulates historical ticket dataset
 ┃ ┣ 📂 models/                # The Algorithm Core
 ┃ ┃ ┣ 📜 anomaly_detector.py  # Scikit-Learn Isolation Forest
 ┃ ┃ ┣ 📜 demand_forecaster.py # Prophet + XGBoost Hybrid Model
 ┃ ┃ ┣ 📜 fleet_optimizer.py   # Google OR-Tools Pareto engine
 ┃ ┃ ┗ 📜 route_planner.py     # RAPTOR Routing implementation
 ┃ ┗ 📜 main.py                # Async FastAPI Endpoints & Loop
 ┃
 ┣ 📂 frontend/                # React.js + Vite Application
 ┃ ┣ 📂 src/
 ┃ ┃ ┣ 📂 pages/
 ┃ ┃ ┃ ┣ 📜 LandingPage.jsx       # 3D animated entry screen
 ┃ ┃ ┃ ┣ 📜 OperatorDashboard.jsx # The Heavy-Duty control room UI
 ┃ ┃ ┃ ┗ 📜 PassengerApp.jsx      # Mobile-first RAPTOR journey planner
 ┃ ┃ ┣ 📜 api.js                  # Axios hooks
 ┃ ┃ ┗ 📜 App.jsx                 # React Router implementation
 ┃ ┗ 📜 package.json              # Vite, Framer-Motion, Recharts, Leaflet
 ┃
 ┗ 📜 README.md
```

---

## 💻 Tech Stack

### Frontend
*   **React 19** + **Vite** (Lightning fast compilation)
*   **Framer Motion** (For gorgeous, fluid dashboard animations)
*   **Recharts** (For rendering Demand AreaCharts and Pareto Tradeoff RadarCharts)
*   **React-Leaflet** (For mapping geospatial GTFS route data and plotting the Demand Heatmap overlay)

### Backend
*   **Python 3.10** + **FastAPI** (High-performance Async API server)
*   **Pandas & NumPy** (Heavy-duty data cleaning and matrix operations)
*   **Scikit-Learn** (IsolationForest for anomaly detection)
*   **Prophet** (Time-series forecasting seasonality)
*   **XGBoost** (Gradient-boosted decision trees for residuals)
*   **Google OR-Tools** (Constraint programming for multi-objective optimization)

---

## ⚙️ How to Run Locally

### 1. Start the Backend (Python)
```bash
cd backend
pip install -r requirements.txt
python main.py
```
*The backend will boot on `localhost:8000`. Please allow ~15 seconds on the first run for the ML models to initialize, train, and the RAPTOR indexing graph to compile.*

### 2. Start the Frontend (Node.js)
```bash
cd frontend
npm install
npm run dev
```
*The frontend will be available at `http://localhost:5173`. We highly recommend viewing the Operator Dashboard on a desktop browser for full data visibility.*
