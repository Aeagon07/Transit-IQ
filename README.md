# Transit-IQ 🚏🧠

**The Intelligent Brain for Pune's Buses**
A Live Demo of Pune Transit Intelligence powered by Machine Learning and Operations Research.

Transit-IQ is a comprehensive, open-source Intelligent Transit Management System tailored for PMPML (Pune Mahanagar Parivahan Mahamandal Ltd.). It solves the classic commuter problem—"Is my bus 5 minutes away or 45 minutes away?"—by combining predictive passenger demand, dynamic fleet optimization, and real-time mapping into a unified platform.

![License](https://img.shields.io/badge/license-MIT-blue.svg)
![React](https://img.shields.io/badge/Frontend-React%20%2B%20Vite-61dafb.svg)
![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688.svg)

---

## 📸 Platform Gallery

<details>
<summary>Click to view Transit-IQ Interface Screenshots</summary>
<br>

| Landing Page | Fleet Tracking |
| :---: | :---: |
| <img src="docs/hero.png" width="400" alt="Landing Page Hero"/> | <img src="docs/fleet.png" width="400" alt="Operator Dashboard Fleet"/> |

| Demand Forecasting | Live Optimization |
| :---: | :---: |
| <img src="docs/demand.png" width="400" alt="Operator Dashboard Demand"/> | <img src="docs/optimize.png" width="400" alt="Operator Dashboard Optimize"/> |

</details>

---

## 🌟 Key Features

### 1. Facebook Prophet Demand Forecasting
Predicts passenger demand per route, per 15-minute slot, up to 4 hours ahead.
- Seamlessly integrates Pune's specific calendar features (e.g., Ganpati festival, IPL matches) into the forecasting model.
- Includes a bespoke **Rain-to-Bus Model** shifting 2-wheeler commuters to buses automatically during rainfall simulations.

### 2. Live Fleet Optimization (OR-Tools)
Utilizes Google OR-Tools to compute the mathematically optimal bus frequency for each route based on live and predicted demand signals.
- Generates actionable deployment recommendations for dispatchers.
- Adjusts fleets dynamically to maximize efficiency and minimize overcrowding.

### 3. Dynamic RAPTOR Route Planning
Provides users with exact minute-precision journey planning.
- Calculates transit routes using a Python implementation of the RAPTOR algorithm.
- Displays realistic upcoming bus departures by automatically simulating frequency intervals and real-time fare calculations.
- Assigns specific mock license plates (`MH-12-xx-xxxx`) so passengers know exactly which physical bus to board.

### 4. Interactive Operator Dashboard
A dedicated, real-time command center for PMPML operators:
- Real-time fleet tracking via Leaflet.js interactive maps.
- Live telemetry including health metrics (CPU/RAM thresholds, active API connections).
- Review pipeline for approving or rejecting OR-Tools generated fleet recommendations.

### 5. Multi-Modal Passenger Application
A modern rider-facing interface optimized for quick look-ups.
- Features dynamic "Step Card" UI directions mimicking premium navigation apps (walking distances, transfers, fare estimates, and crowd density).
- Uses state-of-the-art UI animations driven by `framer-motion` and crisp iconography via `lucide-react`.

---

## 🛠️ Tech Stack & Architecture

### Backend Stack
* **Framework:** FastAPI (Python 3)
* **Routing Logic:** RAPTOR Algorithm & Haversine A* Fallback
* **Machine Learning:** Facebook Prophet, scikit-learn (IsolationForest for Anomaly Detection)
* **Optimization:** Google OR-Tools
* **Weather Integration:** Open-Meteo API
* **Database:** SQLite

### Frontend Stack
* **Framework:** React 18 & Vite
* **Routing:** react-router-dom
* **Styling & UI:** Modern CSS / Flexbox Grid
* **Animations:** Framer Motion
* **Mapping:** Leaflet.js & react-leaflet
* **Icons:** Lucide-React

---

## 🚀 Getting Started

### Prerequisites
* Python 3.9+
* Node.js v18+ & npm
* Git

### 1. Clone the Repository
```bash
git clone https://github.com/Ayush-Jayatkar/Transit-IQ.git
cd Transit-IQ
```

### 2. Start the Backend Server
The FastAPI server handles the ML inferences and data APIs.
```bash
cd backend
python -m venv venv

# Windows
venv\Scripts\activate
# Mac/Linux
source venv/bin/activate

pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```
*The backend API Docs (Swagger) will be available at `http://localhost:8000/docs`.*

### 3. Start the Frontend Application
In a new terminal window:
```bash
cd frontend
npm install
npm run dev
```

The application will launch at `http://localhost:5173/`.

---

## 🗺️ Project Structure

```text
Transit-IQ/
├── backend/
│   ├── main.py              # FastAPI endpoints and route logic
│   ├── models/
│   │   └── route_planner.py # Core RAPTOR algorithm & path generation
│   ├── data/                # Mock datasets & geo information
│   └── requirements.txt     # Python dependencies
├── frontend/
│   ├── index.html
│   ├── package.json
│   ├── src/
│   │   ├── api.js           # Main REST wrapper for all backend routes
│   │   ├── App.jsx          # React Router configuration
│   │   ├── index.css        # Global variables and design system
│   │   └── pages/
│   │       ├── LandingPage.jsx       # Public marketing page
│   │       ├── OperatorDashboard.jsx # Dispatcher control panel
│   │       ├── PassengerApp.jsx      # Rider journey planner
│   │       └── ApiDocs.jsx           # Internal UI API documentation
└── README.md
```

## 🏆 Conclusion
Transit-IQ successfully bridges the gap between historical static transit routing and dynamic, live-intelligence operations. By utilizing robust machine learning methodologies (Prophet, Isolation Forests) coupled with hardened operations-research constraint processing (OR-Tools), we present a next-generation platform that scales with real-world infrastructure complexity. It transforms City Transit from a reactive entity into a proactive, adaptive, and highly trustworthy network for its citizens.

## 📄 License
This open-source software is licensed under the [MIT License](LICENSE).
