"""
FastAPI Server for LSCP
Provides API endpoints for querying the semantic cartography
"""
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional, Dict
import uvicorn

from config import settings
from db.relational import LSCPDatabase
from db.vector_store import VectorStore
from models.control import ControlModel
from models.explorer import ExplorerModel
from crawler.scanner import LSCPScanner

# Initialize FastAPI
app = FastAPI(
    title="Latent Space Cartography Protocol",
    description="API for exploring semantic deltas between human and AI concept spaces",
    version="0.1.0"
)

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global instances (initialized on startup)
db: Optional[LSCPDatabase] = None
vector_store: Optional[VectorStore] = None
scanner: Optional[LSCPScanner] = None


# Request/Response Models
class ScanRequest(BaseModel):
    concept: str
    vocabulary: Optional[List[str]] = None


class ScanResponse(BaseModel):
    concept: str
    human_neighbors: List[tuple]
    latent_neighbors: List[tuple]
    avg_delta: float
    high_delta_count: int


class ConceptResponse(BaseModel):
    concept: str
    relationships: List[Dict]


class EdgeResponse(BaseModel):
    concept_a: str
    concept_b: str
    human_distance: float
    latent_distance: float
    delta: float
    bridge_mechanism: Optional[str]


# Startup/Shutdown Events
@app.on_event("startup")
async def startup_event():
    """Initialize models and databases on server start"""
    global db, vector_store, scanner

    print("Initializing LSCP Server...")

    # Initialize databases
    db = LSCPDatabase(settings.SQLITE_DB_PATH)
    vector_store = VectorStore(settings.VECTOR_DB_PATH, settings.CHROMA_COLLECTION_NAME)

    # Initialize models (this will take some time)
    try:
        control_model = ControlModel(settings.MINILM_MODEL_NAME)
        explorer_model = ExplorerModel(
            model_path=settings.LLAMA_MODEL_PATH,
            n_ctx=settings.LLAMA_N_CTX,
            n_threads=settings.LLAMA_N_THREADS
        )

        # Initialize scanner
        scanner = LSCPScanner(
            control_model=control_model,
            explorer_model=explorer_model,
            vector_store=vector_store,
            database=db,
            neighbor_count=settings.NEIGHBOR_COUNT,
            delta_threshold=settings.DELTA_THRESHOLD
        )

        print("LSCP Server ready!")

    except Exception as e:
        print(f"Error initializing models: {e}")
        print("Server will start but scanning will not work until models are loaded.")


@app.on_event("shutdown")
async def shutdown_event():
    """Cleanup on server shutdown"""
    global db
    if db:
        db.close()
    print("LSCP Server shutdown complete")


# Endpoints
@app.get("/")
async def root():
    """Health check"""
    return {
        "status": "online",
        "service": "Latent Space Cartography Protocol",
        "version": "0.1.0"
    }


@app.get("/concepts")
async def get_all_concepts() -> List[str]:
    """Get list of all scanned concepts"""
    if not vector_store:
        raise HTTPException(status_code=503, detail="Vector store not initialized")

    concepts = vector_store.get_all_concepts()
    return concepts


@app.get("/concept/{concept_name}")
async def get_concept(concept_name: str) -> ConceptResponse:
    """Get detailed information about a specific concept"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    result = db.get_concept_neighbors(concept_name)

    if not result.get("relationships"):
        raise HTTPException(status_code=404, detail=f"Concept '{concept_name}' not found")

    return ConceptResponse(**result)


@app.get("/edges")
async def get_edge_concepts(threshold: float = 0.3, limit: int = 100) -> List[EdgeResponse]:
    """Get high-delta concept pairs (the 'Edge')"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    edges = db.get_high_delta_relationships(threshold=threshold, limit=limit)
    return [EdgeResponse(**edge) for edge in edges]


@app.post("/scan")
async def scan_concept(request: ScanRequest, background_tasks: BackgroundTasks) -> Dict:
    """
    Scan a new concept
    If vocabulary not provided, uses existing database concepts
    """
    if not scanner:
        raise HTTPException(status_code=503, detail="Scanner not initialized")

    # Use existing concepts as vocabulary if not provided
    vocabulary = request.vocabulary
    if not vocabulary:
        vocabulary = vector_store.get_all_concepts()

    # If vocabulary is still empty, use a minimal set
    if not vocabulary:
        vocabulary = [request.concept]

    # Ensure concept is in vocabulary
    if request.concept not in vocabulary:
        vocabulary.append(request.concept)

    try:
        result = scanner.scan_concept(request.concept, vocabulary)
        return result
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Scan failed: {str(e)}")


@app.get("/stats")
async def get_stats() -> Dict:
    """Get database statistics"""
    if not db:
        raise HTTPException(status_code=503, detail="Database not initialized")

    cursor = db.conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM concepts")
    concept_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM relationships")
    relationship_count = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM scans")
    scan_count = cursor.fetchone()[0]

    cursor.execute("SELECT AVG(delta) FROM relationships")
    avg_delta = cursor.fetchone()[0] or 0

    cursor.execute("SELECT COUNT(*) FROM relationships WHERE delta >= ?", (settings.DELTA_THRESHOLD,))
    high_delta_count = cursor.fetchone()[0]

    return {
        "concepts": concept_count,
        "relationships": relationship_count,
        "scans": scan_count,
        "avg_delta": round(avg_delta, 4),
        "high_delta_pairs": high_delta_count,
        "threshold": settings.DELTA_THRESHOLD
    }


def run_server():
    """Run the FastAPI server"""
    uvicorn.run(
        "api.server:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=False
    )


if __name__ == "__main__":
    run_server()
