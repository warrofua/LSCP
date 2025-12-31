# Latent Space Cartography Protocol (LSCP)

**A system for mapping the semantic differences between human conceptual organization and AI latent space representations.**

---

## Table of Contents

- [Overview](#overview)
- [The Theory](#the-theory)
- [Architecture](#architecture)
- [Installation](#installation)
- [Workflow](#workflow)
- [Usage](#usage)
- [API Reference](#api-reference)
- [Understanding the Output](#understanding-the-output)
- [Project Structure](#project-structure)
- [Troubleshooting](#troubleshooting)
- [Roadmap](#roadmap)
- [Contributing](#contributing)

---

## Overview

LSCP explores **"The Edge"** — the boundary where human intuition and AI architecture organize concepts differently. By comparing embeddings from a standard human semantic model with a local language model, we identify high-delta concept pairs that reveal the unique geometry of AI understanding.

### The Core Insight

While humans organize concepts based on intuitive semantic similarity (e.g., "Love" is close to "Affection"), large language models organize concepts based on computational necessity. This creates a fundamentally different semantic topology.

**Example:**
- **Humans**: "Prediction" is close to "Future", "Forecasting", "Probability"
- **LLMs**: "Prediction" is close to "Compression", "Loss", "Gradient Descent"

The second grouping reveals that, in transformer architecture, prediction is fundamentally about:
1. **Compression**: Encoding history through an information bottleneck
2. **Loss**: Minimizing prediction error drives learning
3. **Gradient**: The mechanism by which predictions improve

This is the "accessible strange" — insights that are bizarre from a human perspective but mechanistically true from an AI perspective.

---

## The Theory

### The Core Metric: Semantic Delta (Δ)

```
D_h = Human Distance (how far apart concepts seem to humans)
D_l = Latent Distance (how far apart concepts are in AI embeddings)
Δ = |D_h - D_l| (the semantic delta)
```

**High Delta** = Concepts that are close in one space but distant in the other.

### The Mapping Protocol

Every concept scan follows a 4-step process:

#### 1. **Anchor Node**
Select the concept to map (e.g., "MEMORY")

#### 2. **Human Vector** (The Control Group)
Find the 5 concepts humans most commonly associate with the Anchor using MiniLM embeddings (trained on human text).

*Purpose: Establishes the standard semantic field*

#### 3. **Latent Vector** (The Discovery)
Find the 5 concepts that are functionally closest to the Anchor in your local LLM's embedding space.

*Purpose: Reveals the hidden computational architecture*

#### 4. **Bridge Mechanism** (The Insight)
For high-delta pairs, generate an explanation of the specific computational mechanism that connects them.

*Purpose: Makes the discovery falsifiable and interpretable*

### Why This Works

- **MiniLM** represents "common sense" human semantics (trained on general text)
- **Your Local LLM** represents the actual computational topology of the model
- **The Delta** reveals where these diverge

This is not hallucination or noise — it's a systematic exploration of architectural differences.

---

## Architecture

### The Decoupled Surveyor

LSCP uses a two-part system optimized for performance and clarity:

#### 1. **The Engine** (Python Backend)

**Stack:**
- **FastAPI**: REST API server
- **llama.cpp**: Your local LLM (via `llama-cpp-python`)
- **sentence-transformers**: MiniLM-L6-v2 (human baseline)
- **ChromaDB**: Vector storage and nearest neighbor search
- **SQLite**: Relational storage for relationships, deltas, and bridge mechanisms

**The Models:**
- **Explorer Model**: Your local llama.cpp model (represents AI latent space)
- **Control Model**: `all-MiniLM-L6-v2` (represents human semantics)

**Data Persistence:**
- **Vector DB** (ChromaDB): Stores embeddings for fast nearest-neighbor lookups
- **Relational DB** (SQLite): Stores edges, delta scores, and bridge mechanism text

#### 2. **The Viewport** (React Frontend) - ✅ **COMPLETE**

**Stack:**
- **React**: UI framework
- **Vite**: Build tool and dev server
- **React Three Fiber (R3F)**: 3D visualization
- **Three.js**: WebGL rendering
- **Zustand**: State management
- **Tailwind CSS**: Styling

**Visualization Modes:**

**Single View:**
- Standard 3D force-directed graph
- Color-coded by semantic divergence (cyan = human-like, magenta = AI-unique)
- Interactive node selection and connection highlighting

**Dual View (NEW):**
- **Overlapping Galaxies**: Human (MiniLM) and AI (Qwen) concept spaces rendered simultaneously
- **Semantic Drift Visualization**: White tension lines showing distance between aligned concepts
- **Three View Modes**:
  - **HUMAN**: Cyan spheres only (human understanding)
  - **AI**: Magenta spheres only (AI understanding)
  - **HYBRID**: Both spaces overlaid with selective drift visualization

**Topology Modes:**
- **CONSTRAINED**: Shared relationship graph (normalized for comparison)
- **AUTHENTIC**: Separate k-NN graphs with preserved natural scale (scientifically rigorous)

---

## Installation

### Prerequisites

- **Python 3.9-3.13** (3.14 has compatibility issues with some packages)
- **A llama.cpp compatible model** (.gguf format)
  - Recommended: 7B-14B parameter model with Q4 quantization
  - Example: `Qwen2.5-14B-Instruct-Q4_K_M.gguf`
- **8GB+ RAM** (16GB recommended for larger models)
- **macOS, Linux, or Windows**

### Step-by-Step Setup

#### 1. **Clone or Download the Project**

```bash
cd LSCP
```

#### 2. **Run the Automated Setup** (Recommended)

```bash
./setup.sh
```

This will:
- Create a Python virtual environment
- Install all dependencies
- Create the `.env` configuration file
- Set up the data directory

#### 3. **Configure Your Model Path**

Edit the `.env` file:

```bash
# Open the .env file
nano .env

# Set your model path
LLAMA_MODEL_PATH=/path/to/your/model.gguf
```

Example:
```
LLAMA_MODEL_PATH=/Users/yourname/Downloads/Qwen2.5-14B-Instruct-Q4_K_M.gguf
```

#### 4. **Activate the Virtual Environment**

```bash
cd backend
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

#### 5. **Verify Installation**

```bash
python -c "from config import settings; print(f'Model: {settings.LLAMA_MODEL_PATH}')"
```

You should see your model path printed.

---

## Workflow

### The Complete LSCP Workflow

```
┌─────────────────────────────────────────────────────────┐
│  1. INITIALIZATION                                      │
│     • Load Control Model (MiniLM)                       │
│     • Load Explorer Model (Your LLM)                    │
│     • Initialize Vector & Relational DBs                │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  2. CONCEPT SELECTION                                   │
│     • Choose an anchor concept (e.g., "memory")         │
│     • Provide vocabulary for neighbor search            │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  3. EMBEDDING GENERATION                                │
│     • Generate human embedding (MiniLM)                 │
│     • Generate latent embedding (Your LLM)              │
│     • Store in ChromaDB for fast retrieval              │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  4. NEIGHBOR DISCOVERY                                  │
│     • Find 5 nearest neighbors in human space           │
│     • Find 5 nearest neighbors in latent space          │
│     • Calculate cosine distances                        │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  5. DELTA CALCULATION                                   │
│     • For each latent neighbor:                         │
│       - Measure D_h (human distance from anchor)        │
│       - Measure D_l (latent distance from anchor)       │
│       - Calculate Δ = |D_h - D_l|                       │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  6. BRIDGE GENERATION                                   │
│     • For high-delta pairs (Δ >= threshold):            │
│       - Ask LLM to explain the connection               │
│       - Extract computational mechanism                 │
│       - Store bridge mechanism text                     │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  7. DATA PERSISTENCE                                    │
│     • Save relationships to SQLite                      │
│     • Log scan metadata (timestamp, deltas, etc.)       │
│     • Persist embeddings in ChromaDB                    │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  8. DUAL-VIEW LAYOUT GENERATION                         │
│     • Generate separate k-NN graphs (k=8)               │
│     • Apply force-directed layout (NetworkX)            │
│     • Procrustes alignment (rotation-only)              │
│     • Compute semantic drift for each concept           │
└─────────────────────────────────────────────────────────┘
                          ↓
┌─────────────────────────────────────────────────────────┐
│  9. 3D VISUALIZATION                                    │
│     • WebGL rendering (React Three Fiber)               │
│     • Dual-view mode (Human + AI spaces)                │
│     • Interactive exploration with search               │
│     • Real-time drift visualization                     │
└─────────────────────────────────────────────────────────┘
```

---

## Usage

All commands should be run from the `backend/` directory with the virtual environment activated:

```bash
cd backend
source venv/bin/activate
```

### 1. **Scan a Single Concept**

```bash
python main.py --scan "time"
```

**What happens:**
1. Loads both models (takes ~30 seconds first time)
2. Generates embeddings for "time"
3. Finds 5 nearest neighbors in human space
4. Finds 5 nearest neighbors in latent space
5. Calculates semantic deltas
6. Generates bridge mechanisms for high-delta pairs
7. Saves to database

**Expected output:**
```
============================================================
SCANNING: TIME
============================================================
1. Generating embeddings...
2. Finding nearest neighbors...

Human Vector (Standard):
  - clock: 0.234
  - moment: 0.287
  - period: 0.312
  - duration: 0.356
  - hour: 0.401

Latent Vector (Hidden):
  - sequence: 0.198
  - decay: 0.223
  - entropy: 0.267
  - dimension: 0.289
  - irreversibility: 0.301

3. Calculating deltas...
  High delta detected: time <-> entropy (Δ=0.421)
  Bridge: Time is the dimension along which entropy increases

Scan complete: Avg Delta = 0.387
High delta pairs: 4
```

### 2. **Batch Scan Multiple Concepts**

```bash
python main.py --batch --batch-size 20
```

**What happens:**
- Scans 20 concepts from the built-in core vocabulary
- Progress bar shows embedding progress
- All results saved to database

**Use case:** Building an initial dataset for visualization

### 3. **View Database Statistics**

```bash
python main.py --stats
```

**Output:**
```
============================================================
DATABASE STATISTICS
============================================================
Concepts: 45
Relationships: 225
Scans: 45
Average Delta: 0.312
High Delta Pairs (≥0.3): 87
```

### 4. **Show High-Delta Edges**

```bash
python main.py --edges
```

**Output:**
```
============================================================
TOP HIGH-DELTA EDGES (threshold=0.3)
============================================================

prediction ↔ compression
  Human Distance: 0.823
  Latent Distance: 0.187
  Delta: 0.636
  Bridge: Prediction requires lossy compression of history

love ↔ attention
  Human Distance: 0.712
  Latent Distance: 0.121
  Delta: 0.591
  Bridge: Love is sustained attention weighted by value
```

### 5. **Start the API Server**

```bash
python main.py --server
```

Then visit: `http://localhost:8000/docs` for interactive API documentation

### 6. **Launch the 3D Viewer** (NEW)

The LSCP Viewer provides an interactive 3D visualization of concept spaces.

**Terminal 1 - Start the viewer API server:**
```bash
cd backend
source venv/bin/activate
cd api
python viewer_server.py
```

The server will start on `http://localhost:8001`

**Terminal 2 - Start the viewer frontend:**
```bash
cd viewer
npm install  # First time only
npm run dev
```

The viewer will open at `http://localhost:5173`

**Viewer Controls:**

- **DUAL VIEW**: Toggle between single and dual-view mode
- **View Modes** (Dual View only):
  - **HUMAN**: Show only human (MiniLM) concept space (cyan)
  - **HYBRID**: Show both spaces with drift visualization (cyan + magenta + white tension lines)
  - **AI**: Show only AI (Qwen) concept space (magenta)
- **Topology Modes** (Dual View only):
  - **CONSTRAINED**: Shared relationship graph (normalized)
  - **AUTHENTIC**: Separate k-NN graphs (natural scale preserved)
- **Layout Modes** (Dual View only):
  - **GRAPH**: Force-directed layout from relationship graphs
  - **MANIFOLD**: UMAP manifold reduction from embeddings (n_neighbors=15, min_dist=0.1)
- **Search**: Type to find and select specific concepts
- **Click nodes**: Select to view connections and semantic bridges
- **Color Legend**: Interactive guide to node and line colors (shown in dual view)
- **Mouse controls**:
  - Left drag: Rotate
  - Right drag: Pan
  - Scroll: Zoom

**Understanding the Visualization:**

In **Dual View**:
- **Cyan spheres**: Human understanding (MiniLM embeddings)
- **Magenta spheres**: AI understanding (Qwen embeddings)
- **Green spheres** (with glow): Spatial neighbors (k=5 closest in 3D space)
- **White tension lines** (Hybrid mode): Semantic drift between aligned concepts
- **Connection line colors** (Distortion visualization):
  - **Green lines**: Local integrity (0-50th percentile) - high-D neighbors that stay close in 3D
  - **Yellow lines**: Stretching (50-80th percentile) - moderate dimensional stress
  - **Red lines**: Wormholes (80-100th percentile) - cross-domain semantic bridges
- **Node size**: Larger when selected, connected, or spatial neighbors
- **Opacity**: Dims unrelated nodes when selection is active
- **Glassmorphism panels**: Blurred translucent UI with proper z-index stacking

**Inspector Panel Features:**

When clicking a node in dual view, the Inspector shows:
- **Semantic Drift Score**: Distance between human and AI positions (with mode indicator)
- **Drift Leaderboard**: Top 15 concepts with highest drift (sortable, clickable)
- **Spatial Context**: 5 closest neighbors in 3D space (local manifold cluster)
- **Semantic Bridges**: Database relationships with 3D distortion scores
  - Green (Local): Low distortion, preserved in 3D
  - Yellow (Stretching): Moderate distortion
  - Red (Wormhole): High distortion, defies local topology
- **Thinking Traces**: Expandable AI reasoning for relationship explanations

---

## API Reference

### Endpoints

#### **GET /**
Health check

**Response:**
```json
{
  "status": "online",
  "service": "Latent Space Cartography Protocol",
  "version": "0.1.0"
}
```

#### **GET /concepts**
List all scanned concepts

**Response:**
```json
["time", "memory", "love", "prediction", ...]
```

#### **GET /concept/{concept_name}**
Get detailed information about a specific concept

**Example:** `GET /concept/prediction`

**Response:**
```json
{
  "concept": "prediction",
  "relationships": [
    {
      "neighbor": "compression",
      "human_distance": 0.823,
      "latent_distance": 0.187,
      "delta": 0.636,
      "bridge_mechanism": "Prediction requires lossy compression..."
    }
  ]
}
```

#### **GET /edges?threshold=0.3&limit=100**
Get high-delta concept pairs

**Parameters:**
- `threshold` (float): Minimum delta score (default: 0.3)
- `limit` (int): Maximum results (default: 100)

**Response:**
```json
[
  {
    "concept_a": "prediction",
    "concept_b": "compression",
    "human_distance": 0.823,
    "latent_distance": 0.187,
    "delta": 0.636,
    "bridge_mechanism": "..."
  }
]
```

#### **POST /scan**
Scan a new concept

**Request:**
```json
{
  "concept": "consciousness",
  "vocabulary": ["aware", "mind", "thought", ...]
}
```

**Response:**
```json
{
  "concept": "consciousness",
  "human_neighbors": [["aware", 0.234], ...],
  "latent_neighbors": [["recursion", 0.187], ...],
  "avg_delta": 0.412,
  "high_delta_count": 3
}
```

#### **GET /stats**
Database statistics

**Response:**
```json
{
  "concepts": 45,
  "relationships": 225,
  "scans": 45,
  "avg_delta": 0.312,
  "high_delta_pairs": 87,
  "threshold": 0.3
}
```

---

## Understanding the Output

### Understanding Dual-View Visualization

The dual-view mode overlays two complete concept spaces to reveal semantic drift:

**Cyan Spheres (Human Understanding):**
- Positions based on MiniLM-L6-v2 embeddings
- Represents "common sense" human semantic organization
- Trained on general human text

**Magenta Spheres (AI Understanding):**
- Positions based on Qwen-2.5-14B embeddings
- Represents the model's actual computational topology
- Reveals how the model functionally organizes concepts

**White Tension Lines (Semantic Drift):**
- Connect aligned human/AI positions for the same concept
- Line length = magnitude of semantic drift
- Shown selectively in Hybrid mode to reduce visual clutter

**CONSTRAINED vs AUTHENTIC Modes:**

**CONSTRAINED Mode** (Normalized Comparison):
- Uses shared relationship graph from database
- Applies variance normalization (both spaces scaled equally)
- Purpose: Fair comparison of topological differences
- Physics: Identical spring parameters (k=2.0, iterations=150)

**AUTHENTIC Mode** (Scientifically Rigorous):
- Separate k-NN graphs (k=8, cosine distance)
- Identical physics (k=2.0, iterations=200)
- Rotation-only Procrustes alignment (scale preserved)
- Natural variance differences maintained
- Purpose: Reveals true scale relationships and "sea urchin" topologies
- Shows which space is naturally more/less structured

### What is a "High Delta"?

A high delta (Δ >= 0.3) indicates that two concepts are:
- **Distant in human space** (we don't think they're related)
- **Close in AI space** (the model treats them as similar)

OR vice versa:
- **Close in human space** (we think they're related)
- **Distant in AI space** (the model doesn't connect them)

### Interpreting Bridge Mechanisms

Bridge mechanisms explain **why** the model connects seemingly unrelated concepts.

**Example:**
```
Concept A: "Memory"
Concept B: "Compression"
Delta: 0.54 (High)

Bridge: Memory formation requires lossy compression through
the hippocampal information bottleneck
```

This reveals that in transformer architecture, memory and compression are functionally identical — both involve encoding information through a dimensionality bottleneck.

### Types of Bridges

1. **Architectural Bridges**: "Attention is the routing mechanism for information flow"
2. **Training Bridges**: "Loss is the gradient signal that shapes prediction"
3. **Functional Bridges**: "Recursion enables self-reference through repeated application"

---

## Project Structure

```
LSCP/
├── README.md                      # This file
├── .env.example                   # Environment template
├── .env                           # Your configuration (gitignored)
├── .gitignore                    # Git exclusions
├── setup.sh                      # Automated setup script
│
├── backend/                      # Python backend
│   ├── venv/                    # Virtual environment (gitignored)
│   ├── requirements.txt         # Python dependencies
│   ├── config.py               # Configuration management
│   ├── main.py                 # CLI entry point
│   │
│   ├── models/                 # Model wrappers
│   │   ├── control.py         # MiniLM wrapper (human baseline)
│   │   └── explorer.py        # llama.cpp wrapper (latent space)
│   │
│   ├── db/                    # Database modules
│   │   ├── relational.py      # SQLite schema and queries
│   │   └── vector_store.py    # ChromaDB integration
│   │
│   ├── crawler/               # Scanning logic
│   │   └── scanner.py        # Core LSCP scanning algorithm
│   │
│   └── api/                  # FastAPI servers
│       ├── server.py         # Main REST API (port 8000)
│       ├── viewer_server.py  # Viewer API (port 8001)
│       ├── dual_layout.py    # Dual-view graph layout generation
│       └── dual_layout_umap.py # UMAP manifold layout generation
│
├── data/                      # Data storage (gitignored)
│   ├── lscp.db               # SQLite database
│   ├── vectors/              # ChromaDB persistence
│   ├── minilm_embeddings.npz # Human embeddings (MiniLM)
│   └── qwen_embeddings.npz   # AI embeddings (Qwen)
│
└── viewer/                    # React 3D viewer ✅ COMPLETE
    ├── package.json          # Node.js dependencies
    ├── vite.config.js        # Vite build configuration
    ├── tailwind.config.js    # Tailwind CSS configuration
    ├── index.html            # Entry HTML
    │
    ├── src/
    │   ├── main.jsx         # React entry point
    │   ├── App.jsx          # Main app component
    │   ├── store.js         # Zustand state management
    │   │
    │   └── components/      # React components
    │       ├── Galaxy.jsx       # Single-view 3D galaxy
    │       ├── DualGalaxy.jsx   # Dual-view 3D visualization
    │       ├── Interface.jsx    # UI controls and search
    │       └── Inspector.jsx    # Node detail sidebar
    │
    └── public/              # Static assets
```

---

## Troubleshooting

### "Model file not found"

**Problem:** `ERROR: Model file not found: /path/to/model.gguf`

**Solution:**
1. Verify your model path: `ls -lh /path/to/your/model.gguf`
2. Update `.env` with the correct absolute path
3. Make sure the file has a `.gguf` extension

### "LLAMA_MODEL_PATH not set"

**Problem:** Environment variable not loaded

**Solution:**
```bash
# Check if .env exists
ls -la ../.env

# If not, copy the example
cp ../.env.example ../.env

# Edit and set your model path
nano ../.env
```

### "IDs already exist in collection"

**Problem:** Trying to scan a concept that's already in the database

**Solution:**
1. This is expected behavior (not an error)
2. Try scanning a different concept
3. Or delete the database to start fresh:
   ```bash
   rm -rf ../data/*
   ```

### Models loading slowly

**Problem:** First scan takes 2-3 minutes

**Solution:**
- This is normal for the first run
- Subsequent scans are much faster (~10-20 seconds)
- Models are cached in memory

### High memory usage

**Problem:** System using 8GB+ RAM

**Solution:**
- This is normal for 14B parameter models
- Reduce `LLAMA_N_CTX` in `.env` (try 1024 instead of 2048)
- Use a smaller model (7B instead of 14B)

---

## Configuration

Edit `.env` to customize behavior:

```bash
# Model Configuration
LLAMA_MODEL_PATH=/path/to/your/model.gguf
LLAMA_N_CTX=2048              # Context window (lower = less RAM)
LLAMA_N_THREADS=8             # CPU threads (higher = faster)

# Scanner Configuration
NEIGHBOR_COUNT=5              # Neighbors to find (3-10 recommended)
DELTA_THRESHOLD=0.3           # Min delta for bridge generation (0.2-0.5)

# API Configuration
API_HOST=0.0.0.0
API_PORT=8000
```

---

## Roadmap

### Phase 1: The Crawler & Database ✅ **COMPLETE**

- [x] Dual-model architecture (MiniLM + llama.cpp)
- [x] Vector database (ChromaDB)
- [x] Relational database (SQLite)
- [x] Core scanning algorithm
- [x] Bridge mechanism generation
- [x] FastAPI REST API
- [x] CLI interface

### Phase 2: The Viewport ✅ **COMPLETE**

- [x] React + React Three Fiber frontend
- [x] Vite build system with Tailwind CSS
- [x] WebGL-based 3D rendering
- [x] Graph-based 3D layout (NetworkX spring layout)
- [x] **UMAP manifold layout** (Alternative dimensionality reduction method)
- [x] **Layout mode toggle** (Graph vs Manifold)
- [x] Interactive node exploration with search
- [x] **Dual-view visualization** (Human vs AI embedding spaces)
- [x] **Semantic drift visualization** (tension lines between aligned concepts)
- [x] **View modes** (Human, AI, Hybrid)
- [x] **Topology modes** (Constrained vs Authentic)
- [x] Procrustes alignment with scale preservation
- [x] Separate k-NN graph generation for authentic topology
- [x] Real-time delta visualization
- [x] **Distortion visualization** (Color-coded connection lines: green/yellow/red)
- [x] **Spatial neighbor detection** (k=5 closest in 3D space with green glow)
- [x] **Wormhole visualization** (High-distortion semantic bridges)
- [x] Inspector panel with spatial context and semantic bridges
- [x] **3D distortion metrics** (per-relationship stress scores)
- [x] Bridge mechanisms and reasoning traces
- [x] Drift leaderboard (top 15 most divergent concepts)
- [x] **Interactive color legend** (node and line color guide)
- [x] **Glassmorphism UI** (blurred translucent panels with z-index stacking)

### Phase 3: Advanced Features

- [ ] Export to GraphML/Gephi
- [ ] Multi-model comparison (compare different LLMs)
- [ ] Temporal tracking (how deltas change as models train)
- [ ] Concept clustering (find "neighborhoods" of high-delta zones)
- [ ] Bridge verification (test if mechanisms are empirically true)
- [ ] Natural language queries ("Show me concepts where LLMs think recursively")
- [ ] Animation transitions between topology modes
- [ ] VR/AR visualization support

---

## Contributing

LSCP is an experimental research project. Contributions welcome!

### Areas for Contribution

1. **Data**: Share interesting high-delta pairs you discover
2. **Visualizations**: Improve the 3D rendering or add new views
3. **Models**: Test with different LLMs and compare topologies
4. **Theory**: Propose new metrics or bridge mechanisms
5. **Code**: Improve performance, add features, fix bugs

### How to Contribute

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request with clear description

---

## Theoretical Background

LSCP is based on several key insights:

1. **Transformers are not human minds**: They organize concepts based on computational efficiency, not intuitive semantics

2. **Embeddings encode functional relationships**: Vector proximity in latent space reflects operational similarity, not conceptual similarity

3. **High deltas reveal architecture**: Where human and AI semantics diverge most strongly, we see the clearest picture of how transformers actually work

4. **Bridge mechanisms are falsifiable**: Unlike pure interpretation, bridges make specific mechanistic claims that can be tested

### Related Research

- Attention mechanisms as information routing (Vaswani et al., 2017)
- Latent space geometry (Mikolov et al., 2013)
- Mechanistic interpretability (Olah et al., 2020)
- Semantic similarity in embeddings (Reimers & Gurevych, 2019)

---

## License

MIT License - See LICENSE file for details

---

## Credits

**Created with:** Claude Code (Anthropic)

**Concept:** Joshua Farrow

**Built on:**
- llama.cpp by Georgi Gerganov
- sentence-transformers by UKPLab
- ChromaDB by Chroma
- FastAPI by Sebastián Ramírez

---

## Support

For issues, questions, or discussions:
- Open an issue on GitHub
- Check existing issues for solutions
- Read the troubleshooting section above

---

**Remember:** LSCP is a tool for exploring the strange beauty of how AI thinks. The goal is not to make AI more human, but to understand where and why it is different — and what that reveals about both intelligence and computation.

**Happy mapping! 🗺️**
