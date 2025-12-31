"""
LSCP Configuration
Centralized settings for the Latent Space Cartography Protocol
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# Project root directory
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
VECTOR_DB_PATH = DATA_DIR / "vectors"
SQLITE_DB_PATH = DATA_DIR / "lscp.db"

# Path to .env file (in project root)
ENV_FILE = PROJECT_ROOT / ".env"

# Load environment variables
load_dotenv(ENV_FILE)

class Settings:
    """Application settings"""

    # DeepSeek API Configuration
    DEEPSEEK_API_KEY: str = os.getenv("DEEPSEEK_API_KEY", "")
    DEEPSEEK_BASE_URL: str = "https://api.deepseek.com"
    DEEPSEEK_MODEL: str = "deepseek-reasoner"

    # Control Model (Human Baseline)
    MINILM_MODEL_NAME: str = "sentence-transformers/all-MiniLM-L6-v2"

    # Database Configuration
    CHROMA_COLLECTION_NAME: str = "lscp_embeddings"
    SQLITE_DB_PATH: str = str(SQLITE_DB_PATH)
    VECTOR_DB_PATH: str = str(VECTOR_DB_PATH)

    # Crawler Configuration
    NEIGHBOR_COUNT: int = int(os.getenv("NEIGHBOR_COUNT", "5"))
    DELTA_THRESHOLD: float = float(os.getenv("DELTA_THRESHOLD", "0.3"))

    # API Configuration
    API_HOST: str = os.getenv("API_HOST", "0.0.0.0")
    API_PORT: int = int(os.getenv("API_PORT", "8000"))

settings = Settings()

# Ensure data directories exist
VECTOR_DB_PATH.mkdir(parents=True, exist_ok=True)
DATA_DIR.mkdir(parents=True, exist_ok=True)
