Act as a Principal Software Architect and Technical Writer. Generate a comprehensive, professional, production-grade `README.md` file in a single Markdown document for the open-source repository described below.

---

### 🚀 PROJECT SUMMARY:
- **Project Name**: NCRB Tactical Criminal Relationship Intelligence Platform
- **Sub-system**: Anti-Fraud Entity & Device Trail Intelligence (Smart India Hackathon - SIH Project)
- **Domain**: Automated law enforcement Link Analysis, Cybercrime Syndicate Unmasking, Telephony/Device Linkage, BSA Section 63 Digital Evidence Certification, and BNSS/CrPC Statutory Judicial Relief (Bail/Remand) Prediction.

---

### 📂 EXACT FILE STRUCTURE & ARCHITECTURE:

```files
sih-criminal-analysis/
├── backend/                                  # FastAPI Backend & ML Analytics Engine
│   ├── core/                                 # Core Analytical Modules
│   │   ├── __init__.py                       # Package initializer
│   │   ├── graph_engine.py                   # NetworkX connective graph topology builder
│   │   ├── judicial_predictor.py             # Model 2: RandomForest BNSS/CrPC bail predictor
│   │   ├── nlp_extractor.py                  # Legal RegEx & flat 4-entity topology extractor
│   │   └── suspicion_engine.py               # Model 1: HistGradientBoosting suspicion engine
│   ├── data/                                 # Dataset & Sample Case Records
│   │   ├── mock_graph.json                   # Mock graph fallback data
│   │   ├── sample_firs                       # Training snippet generator
│   │   ├── sample_firs.txt                   # Sample FIR case documents (.txt)
│   │   └── synthetic_crime_15k.csv           # Master synthetic criminal dataset (15,000 records)
│   ├── models/                               # Serialized ML Artifacts (.pkl)
│   │   ├── connective_graph.pkl              # NetworkX topological graph artifact
│   │   ├── judicial_predictor.pkl            # Trained bail prediction model
│   │   ├── suspicion_engine.pkl              # Trained syndicate role scoring model
│   │   ├── bail_features.pkl                 # Feature list for judicial predictor
│   │   └── role_features.pkl                 # Feature list for suspicion engine
│   ├── app.py                                # Main FastAPI server application & REST endpoints
│   ├── requirements.txt                      # Python backend dependencies
│   ├── train_graph_model.py                  # Graph model training & Louvain clustering script
│   └── train_models.py                       # Supervised ML model training pipeline script
│
├── frontend/                                 # React + Vite + Tailwind CSS Dashboard
│   ├── src/                                  # Source Frontend Application
│   │   ├── components/                       # UI Components & Renderers
│   │   │   ├── FileIngestionSidebar.jsx      # PDF/TXT FIR document uploader sidebar
│   │   │   ├── GraphCanvas.jsx               # HTML5 Canvas ForceGraph renderer with Mini-Tags,
│   │   │   │                                 # Directional Arrows & Interactive Legend
│   │   │   └── NodeInspector.jsx             # Floating/Slide-out entity inspector card
│   │   ├── data/                             # Frontend mock datasets
│   │   │   └── mock_graph.json
│   │   ├── services/                         # API Client Layer
│   │   │   └── api.js                        # REST API client for backend communication
│   │   ├── App.jsx                           # Main application layout & state orchestration
│   │   ├── index.css                         # Tailwind CSS global styles & custom utilities
│   │   └── main.jsx                          # React application entry point
│   ├── index.html                            # Main HTML template
│   ├── package.json                          # Node.js dependencies & scripts
│   ├── package-lock.json                     # Locked dependency tree
│   ├── postcss.config.js                     # PostCSS configuration for Tailwind
│   ├── tailwind.config.js                    # Tailwind CSS configuration
│   └── vite.config.js                        # Vite bundler configuration
│
├── package.json                              # Root workspace package configuration
└── package-lock.json                         # Root package lockfile

### 1. Clone the Repository

```bash
git clone [https://github.com/ankitadasdk/sih.git](https://github.com/ankitadasdk/sih.git)
cd sih
```
## 🚀 Step-by-Step Installation & Run Guide
### 2. Backend Setup (FastAPI)

Navigate to the backend directory:

```bash
cd backend
```

Create and activate a virtual environment:

- **Linux / macOS:**
  ```bash
  python3 -m venv venv
  source venv/bin/activate
  ```

- **Windows:**
  ```bash
  python -m venv venv
  venv\Scripts\activate
  ```

Install dependencies:

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

Set up environment variables:

```bash
cp .env.example .env
```
*(Edit `.env` with your preferred database URI and secret keys)*

Run the API server:

```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

- **Interactive API Docs (Swagger UI):** `http://localhost:8000/docs`
- **Alternative Docs (ReDoc):** `http://localhost:8000/redoc`

---

### 3. Frontend Setup (React + Vite)

Open a new terminal and navigate to the frontend directory:

```bash
cd frontend
```

Install Node modules:

```bash
npm install
```

Set up environment variables:

```bash
cp .env.example .env
```

Start the Vite development server:

```bash
npm run dev
```

- **Local Web App:** `http://localhost:5173`
