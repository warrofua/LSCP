"""
LSCP Galaxy Viewer API
Serves 3D visualization data for the semantic space
"""
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from typing import List, Dict, Optional
import numpy as np
import sqlite3
from pathlib import Path
import pickle
import umap

# Initialize FastAPI
app = FastAPI(
    title="LSCP Galaxy Viewer API",
    description="API for visualizing the Latent Space Cartography Protocol",
    version="1.0.0"
)

# Enable CORS for React frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Database path
DB_PATH = Path(__file__).parent.parent.parent / "data" / "lscp.db"
CACHE_PATH = Path(__file__).parent.parent.parent / "data" / "umap_cache.pkl"
VECTOR_DB_PATH = Path(__file__).parent.parent.parent / "data" / "vectors"

# Global cache
_projection_cache = None


def get_graph_layout_3d():
    """Calculate 3D layout using force-directed graph from relationships"""
    try:
        import networkx as nx

        conn = get_db_connection()
        cursor = conn.cursor()

        # Build graph from relationships
        cursor.execute("""
            SELECT ca.name, cb.name, r.human_distance
            FROM relationships r
            JOIN concepts ca ON r.concept_a_id = ca.id
            JOIN concepts cb ON r.concept_b_id = cb.id
        """)

        G = nx.Graph()
        for row in cursor.fetchall():
            # Use inverse distance as weight (closer concepts = stronger connection)
            weight = 1.0 / (1.0 + float(row[2]))
            G.add_edge(row[0], row[1], weight=weight)

        conn.close()

        if len(G.nodes()) == 0:
            return None

        # Use spring layout in 3D
        pos = nx.spring_layout(G, dim=3, k=2, iterations=50, seed=42)

        # Scale positions for better viewing
        coords_dict = {}
        for node, coord in pos.items():
            scaled = coord * 10  # Scale to reasonable viewing bounds
            coords_dict[node] = scaled.tolist()

        return coords_dict

    except Exception as e:
        print(f"Error creating graph layout: {e}")
        import traceback
        traceback.print_exc()
        return None


def calculate_3d_projection():
    """Calculate 3D projection using graph layout and cache it"""
    global _projection_cache

    # Check cache first
    if CACHE_PATH.exists():
        print("Loading cached 3D projection...")
        with open(CACHE_PATH, 'rb') as f:
            _projection_cache = pickle.load(f)
        return _projection_cache

    print("Calculating 3D graph layout... (this may take a moment)")

    # Use graph-based layout
    _projection_cache = get_graph_layout_3d()

    if not _projection_cache:
        print("Failed to calculate layout")
        return None

    # Cache result
    with open(CACHE_PATH, 'wb') as f:
        pickle.dump(_projection_cache, f)

    print(f"Projected {len(_projection_cache)} concepts to 3D space using force-directed layout")
    return _projection_cache


def get_db_connection():
    """Get SQLite connection"""
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    return conn


@app.on_event("startup")
async def startup_event():
    """Calculate projection on startup"""
    calculate_3d_projection()


@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "LSCP Galaxy Viewer API",
        "version": "1.0.0"
    }


@app.get("/api/galaxy")
async def get_galaxy_data():
    """
    Get all nodes with 3D coordinates, delta scores, and relationships
    """
    global _projection_cache

    if _projection_cache is None:
        _projection_cache = calculate_3d_projection()

    if _projection_cache is None:
        raise HTTPException(status_code=500, detail="Failed to calculate 3D projection")

    conn = get_db_connection()
    cursor = conn.cursor()

    # Get all concepts with their aggregate metrics
    cursor.execute("""
        SELECT
            c.id,
            c.name,
            COUNT(DISTINCT r.id) as connection_count,
            AVG(r.human_distance) as avg_distance
        FROM concepts c
        LEFT JOIN relationships r ON (r.concept_a_id = c.id OR r.concept_b_id = c.id)
        GROUP BY c.id, c.name
    """)

    nodes = []
    for row in cursor.fetchall():
        concept_name = row['name']

        # Get 3D coordinates
        coords = _projection_cache.get(concept_name, [0, 0, 0])

        nodes.append({
            "id": row['id'],
            "name": concept_name,
            "position": coords,
            "connections": row['connection_count'] or 0,
            "avgDistance": float(row['avg_distance']) if row['avg_distance'] else 0.0
        })

    # Get all relationships (edges)
    cursor.execute("""
        SELECT
            ca.name as concept_a,
            cb.name as concept_b,
            r.human_distance,
            r.bridge_mechanism,
            r.internal_monologue
        FROM relationships r
        JOIN concepts ca ON r.concept_a_id = ca.id
        JOIN concepts cb ON r.concept_b_id = cb.id
    """)

    edges = []
    for row in cursor.fetchall():
        edges.append({
            "source": row['concept_a'],
            "target": row['concept_b'],
            "distance": float(row['human_distance']),
            "bridge": row['bridge_mechanism'],
            "reasoning": row['internal_monologue']
        })

    conn.close()

    return {
        "nodes": nodes,
        "edges": edges,
        "metadata": {
            "total_nodes": len(nodes),
            "total_edges": len(edges),
            "projection_method": "UMAP"
        }
    }


@app.get("/api/node/{node_name}")
async def get_node_detail(node_name: str):
    """
    Get detailed information about a specific node
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    # Get concept info
    cursor.execute("SELECT * FROM concepts WHERE name = ?", (node_name,))
    concept = cursor.fetchone()

    if not concept:
        raise HTTPException(status_code=404, detail=f"Concept '{node_name}' not found")

    # Get all relationships
    cursor.execute("""
        SELECT
            cb.name as connected_to,
            r.human_distance,
            r.bridge_mechanism,
            r.internal_monologue,
            'outgoing' as direction
        FROM relationships r
        JOIN concepts ca ON r.concept_a_id = ca.id
        JOIN concepts cb ON r.concept_b_id = cb.id
        WHERE ca.name = ?

        UNION ALL

        SELECT
            ca.name as connected_to,
            r.human_distance,
            r.bridge_mechanism,
            r.internal_monologue,
            'incoming' as direction
        FROM relationships r
        JOIN concepts ca ON r.concept_a_id = ca.id
        JOIN concepts cb ON r.concept_b_id = cb.id
        WHERE cb.name = ?
    """, (node_name, node_name))

    # Deduplicate relationships by target (keep first occurrence)
    seen_targets = set()
    relationships = []
    for row in cursor.fetchall():
        target = row['connected_to']
        if target not in seen_targets:
            seen_targets.add(target)
            relationships.append({
                "target": target,
                "distance": float(row['human_distance']),
                "bridge": row['bridge_mechanism'],
                "reasoning": row['internal_monologue'],
                "direction": row['direction']
            })

    conn.close()

    coords = _projection_cache.get(node_name, [0, 0, 0]) if _projection_cache else [0, 0, 0]

    return {
        "id": concept['id'],
        "name": node_name,
        "position": coords,
        "relationships": relationships,
        "relationship_count": len(relationships)
    }


@app.get("/api/search")
async def search_concepts(q: str):
    """
    Search for concepts by name
    """
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT id, name
        FROM concepts
        WHERE name LIKE ?
        ORDER BY name
        LIMIT 10
    """, (f"%{q}%",))

    results = []
    for row in cursor.fetchall():
        coords = _projection_cache.get(row['name'], [0, 0, 0]) if _projection_cache else [0, 0, 0]
        results.append({
            "id": row['id'],
            "name": row['name'],
            "position": coords
        })

    conn.close()

    return {"results": results}


@app.get("/api/galaxy/dual")
async def get_dual_galaxy_data():
    """
    Get dual-view galaxy data with Human (MiniLM) and AI (Qwen) positions
    Graph-based layout (force-directed)
    """
    try:
        from dual_layout import generate_dual_layout
        result = generate_dual_layout()
        return result
    except Exception as e:
        print(f"Error generating dual layout: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate dual layout: {str(e)}")


@app.get("/api/galaxy/manifold")
async def get_manifold_galaxy_data():
    """
    Get manifold-view galaxy data with UMAP-reduced positions
    Manifold-based layout (dimensionality reduction)
    """
    try:
        from dual_layout_umap import generate_umap_layout
        result = generate_umap_layout()
        return result
    except Exception as e:
        print(f"Error generating UMAP layout: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to generate UMAP layout: {str(e)}")


@app.get("/api/stats")
async def get_stats():
    """Get database statistics"""
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as count FROM concepts")
    total_concepts = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM relationships")
    total_relationships = cursor.fetchone()['count']

    cursor.execute("SELECT COUNT(*) as count FROM scans")
    total_scans = cursor.fetchone()['count']

    cursor.execute("SELECT AVG(human_distance) as avg FROM relationships")
    avg_distance = cursor.fetchone()['avg']

    conn.close()

    return {
        "concepts": total_concepts,
        "relationships": total_relationships,
        "scans": total_scans,
        "avgDistance": float(avg_distance) if avg_distance else 0.0
    }


if __name__ == "__main__":
    import uvicorn
    print("Starting LSCP Galaxy Viewer API...")
    print(f"Database: {DB_PATH}")
    print("Visit http://localhost:8001/docs for API documentation")
    uvicorn.run(app, host="0.0.0.0", port=8001)
