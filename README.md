# FitCoach AI - Personal Fitness & Health Assistant

**FitCoach AI** is an intelligent, multi-modal personal fitness assistant built using the **Google Agent Development Kit (ADK)** and powered by **Gemini 2.5**. FitCoach AI assists users in planning workouts, calculating training metrics, generating custom workout visuals and video demonstrations, searching for nearby fitness centers, and maintaining long-term memory of health goals and dietary restrictions.

![FitCoach AI Live Demo](./demo.gif)

---

## Key Features & Wired Capabilities

FitCoach AI implements the following production features and Google Cloud integrations:

### 🧠 Cross-Session Long-Term Memory
- **Vertex AI Memory Bank**: Integrates `VertexAiMemoryBankService` to persist user health preferences, workout milestones, and dietary restrictions across sessions.
- Automatically preloads context at the start of conversations using `PreloadMemoryTool` and extracts facts via post-turn callbacks.

### 💾 Firestore Exercise & Workout Management
- **Google Cloud Firestore Database**: Stores and retrieves structured exercise definitions and workout logs (`list_exercises`, `get_exercise_details`, `add_exercise`).

### 🎨 Visual & Media Generation
- **Workout Visuals (Google Imagen)**: Generates custom exercise illustrations and posture diagrams using Google's Imagen model, saving them as ADK artifacts and publishing them to a public Google Cloud Storage bucket.
- **Exercise Demonstration Videos (Google Omni)**: Uses Google's `gemini-omni-flash-preview` model in the `global` region to generate MP4 exercise video demonstrations, saving them as ADK artifacts and uploading them to Google Cloud Storage.

### 📱 Rich Interactive UI (A2UI)
- **Agent-Driven A2UI Cards**: Generates structured A2UI v0.8 card layouts (`A2uiSchemaManager` & `BasicCatalog`) for seamless visual rendering in chat interfaces.

### 🐍 Secure Code Execution Sandbox
- **Agent Engine Sandbox**: Executes dynamic Python code (`AgentEngineSandboxCodeExecutor`) to perform precise fitness calculations including BMI, BMR, TDEE, and heart rate training zones.

### 📍 Location & Maps Integration
- **Google Maps Places API & Geocoding**: Geocodes user locations (`geocode_address`) and finds nearby gyms, parks, and fitness facilities (`find_nearby_places`).

### 🏋️ Public Fitness API
- **Wger Exercise Database**: Fetches exercise details and workout data dynamically from the public Wger REST API (`fetch_online_exercises`).

---

## Project Architecture

```
fitcoach-ai/
├── app/
│   ├── agent.py               # Root ADK Agent configuration & A2UI prompt schema
│   ├── fitness_tools.py       # Metrics calculations, Imagen visuals, and Omni video generation
│   ├── db_tools.py            # Firestore database operations for exercise logs
│   ├── maps_tools.py          # Google Maps geocoding and places lookup
│   ├── a2ui_utils.py          # A2UI callback handler for structured UI cards
│   └── fast_api_app.py        # FastAPI proxy backend
├── frontend/
│   ├── main.py                # FastAPI proxy server connecting browser to Agent Engine
│   └── static/
│       ├── index.html         # Custom glassmorphic chat interface with A2UI renderer
│       └── style.css          # Modern typography and animated UI styling
├── demo.gif                   # Recorded live application demo
└── agents-cli-manifest.yaml   # ADK manifest configuration
```

---

## Setup & Local Execution

### Prerequisites
- Python 3.11+
- [`uv`](https://docs.astral.sh/uv/) package manager
- [`google-agents-cli`](https://pypi.org/project/google-agents-cli/)
- Google Cloud SDK (`gcloud`)

### 1. Environment Configuration
Create a `.env` file in the project root:

```bash
GOOGLE_CLOUD_PROJECT=your-gcp-project-id
GOOGLE_CLOUD_LOCATION=us-central1
FIRESTORE_DATABASE=(default)
```

### 2. Install Dependencies
```bash
uv sync
```

### 3. Run the ADK Web Playground
Launch the local ADK Web playground with Agent Engine Memory Service enabled:

```bash
uv run adk web . --port 8080 --reload_agents --memory_service_uri=agentengine://<AGENT_ENGINE_ID>
```

### 4. Run the Custom Web Frontend
Start the local FastAPI proxy server from the `frontend` directory:

```bash
cd frontend
export AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUM>/locations/us-central1/reasoningEngines/<AGENT_ENGINE_ID>"
export AGENT_DIRECTORY="app"
uv run uvicorn main:app --host 0.0.0.0 --port 8080 --reload
```

---

## Deployment

### Agent Engine Deployment
Deploy the agent logic to Google Cloud Agent Runtime:

```bash
agents-cli deploy
```

### Frontend Cloud Run Deployment
Deploy the custom chat UI proxy to Google Cloud Run:

```bash
cd frontend
gcloud run deploy fitcoach-ai-frontend \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --set-env-vars AGENT_ENGINE_RESOURCE_NAME="projects/<PROJECT_NUM>/locations/us-central1/reasoningEngines/<AGENT_ENGINE_ID>",AGENT_DIRECTORY="app"
```
