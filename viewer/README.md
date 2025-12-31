# LSCP Viewer

Interactive 3D visualization for the Latent Space Cartography Protocol.

## Overview

The LSCP Viewer provides a WebGL-based 3D interface for exploring semantic differences between human conceptual organization (MiniLM embeddings) and AI latent space representations (Qwen embeddings).

## Features

### Visualization Modes

- **Single View**: Traditional 3D force-directed graph with color-coded semantic divergence
- **Dual View**: Overlapping Human (cyan) and AI (magenta) concept spaces with:
  - Semantic drift visualization (white tension lines)
  - Distortion-coded connection lines (green/yellow/red)
  - Spatial neighbor detection with green glow effect
  - Wormhole visualization (high-distortion bridges)

### Layout Modes (Dual View)

- **GRAPH**: Force-directed layout from relationship graphs (NetworkX spring layout)
- **MANIFOLD**: UMAP manifold reduction (n_neighbors=15, min_dist=0.1)

### Topology Modes (Dual View)

- **CONSTRAINED**: Shared relationship graph (normalized for comparison)
- **AUTHENTIC**: Separate k-NN graphs (natural scale preserved, scientifically rigorous)

### View Modes (Dual View)

- **HUMAN**: Show only human understanding (cyan spheres)
- **HYBRID**: Show both spaces with drift visualization
- **AI**: Show only AI understanding (magenta spheres)

### Interactive Features

- **Search**: Real-time concept search and selection
- **Inspector Panel**:
  - Semantic drift scores (graph vs manifold modes)
  - Drift leaderboard (top 15 most divergent concepts)
  - Spatial context (5 closest 3D neighbors)
  - Semantic bridges (database relationships with distortion metrics)
  - Thinking traces (expandable AI reasoning)
- **Color Legend**: Interactive guide to node and line colors
- **Mouse Controls**:
  - Left drag: Rotate camera
  - Right drag: Pan camera
  - Scroll: Zoom in/out

### Visual Elements

**Nodes:**
- Cyan spheres: Human understanding (MiniLM-L6-v2)
- Magenta spheres: AI understanding (Qwen-2.5-14B)
- Green spheres (with glow): Spatial neighbors (k=5 closest in 3D)
- Size increases when selected, connected, or spatial neighbors

**Connection Lines:**
- Green: Local integrity (0-50th percentile) - low distortion
- Yellow: Stretching (50-80th percentile) - moderate distortion
- Red: Wormholes (80-100th percentile) - high distortion, defies local topology
- White: Semantic drift between aligned human/AI positions (Hybrid mode)

**UI:**
- Glassmorphism panels with 30px blur
- Proper z-index stacking (canvas behind UI)
- Translucent backgrounds with saturation boost

## Quick Start

### Prerequisites

- Node.js 18+ (npm 9+)
- LSCP backend running on `http://localhost:8001`

### Installation

```bash
npm install
```

### Development

```bash
npm run dev
```

Opens at `http://localhost:5173` with hot module replacement.

### Build

```bash
npm run build
```

Outputs production build to `dist/` directory.

### Preview Build

```bash
npm run preview
```

## Tech Stack

- **React 18**: UI framework
- **Vite 6**: Build tool and dev server
- **React Three Fiber**: React renderer for Three.js
- **Three.js**: WebGL 3D rendering
- **Zustand**: Lightweight state management
- **Tailwind CSS**: Utility-first styling

## Project Structure

```
viewer/
├── src/
│   ├── main.jsx              # React entry point
│   ├── App.jsx               # Main app component
│   ├── store.js              # Zustand state management
│   ├── index.css             # Global styles (glassmorphism, etc.)
│   └── components/
│       ├── Galaxy.jsx        # Single-view 3D visualization
│       ├── DualGalaxy.jsx    # Dual-view visualization
│       ├── Interface.jsx     # Top controls and search
│       └── Inspector.jsx     # Right sidebar panel
├── public/                   # Static assets
├── package.json              # Dependencies
├── vite.config.js            # Vite configuration
└── tailwind.config.js        # Tailwind CSS configuration
```

## API Dependencies

The viewer requires the LSCP backend API running on port 8001 with the following endpoints:

- `GET /api/galaxy` - Single-view graph data
- `GET /api/galaxy/dual` - Dual-view graph layout data
- `GET /api/galaxy/manifold` - Dual-view UMAP manifold data
- `GET /api/node/:name` - Node details and relationships

## Configuration

Update `API_URL` in `src/App.jsx` if the backend is running on a different host:

```javascript
const API_URL = 'http://localhost:8001'; // Change if needed
```

## Performance

- Optimized for 100-500 nodes
- Uses `useMemo` for expensive calculations
- Percentile-based distortion thresholds for adaptive coloring
- Point lights for spatial neighbor glow effects
- Separate k-NN graph computation for authentic topology mode

## Browser Support

- Chrome 90+
- Firefox 88+
- Safari 14+ (requires `-webkit-backdrop-filter` for glassmorphism)
- Edge 90+

## Development Notes

### Key Components

**DualGalaxy.jsx**: Core 3D visualization
- Calculates 3D distances for spatial neighbors
- Computes percentile-based distortion thresholds
- Renders nodes with emissive materials and point lights
- Handles selection state and camera controls

**Inspector.jsx**: Sidebar information panel
- Displays drift scores (mode-aware: graph vs manifold)
- Shows spatial context (5 closest 3D neighbors)
- Lists semantic bridges with distortion metrics
- Expandable thinking traces for AI reasoning

**Interface.jsx**: Top control panel
- View mode toggles (Human/Hybrid/AI)
- Topology mode toggles (Constrained/Authentic)
- Layout mode toggles (Graph/Manifold)
- Search functionality
- Interactive color legend

### State Management

Uses Zustand for global state:
- `nodes`: Single-view graph nodes
- `dualNodes`: Dual-view aligned nodes
- `selectedNode`: Currently selected node
- `selectedNodeData`: Detailed node information
- `viewMode`: Human/Hybrid/AI
- `topologyMode`: Constrained/Authentic
- `layoutMode`: Graph/Manifold
- `isDualView`: Toggle dual-view mode

## Contributing

See the main LSCP README for contribution guidelines.

## License

MIT License - See LICENSE file for details

---

Part of the **Latent Space Cartography Protocol** (LSCP) project.
