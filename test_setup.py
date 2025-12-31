"""
Quick test script to verify LSCP setup
Run from LSCP/backend directory
"""
import sys
import os

# Change to backend directory
os.chdir('backend')

print("Testing LSCP Setup...")
print("="*60)

# Test 1: Import all modules
print("\n1. Testing imports...")
try:
    from config import settings
    from db.relational import LSCPDatabase
    from db.vector_store import VectorStore
    from models.control import ControlModel
    from models.explorer import ExplorerModel
    print("✓ All imports successful")
except Exception as e:
    print(f"✗ Import failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

# Test 2: Check model path
print("\n2. Checking model path...")
if not settings.LLAMA_MODEL_PATH:
    print("✗ LLAMA_MODEL_PATH not set in .env")
    sys.exit(1)

from pathlib import Path
if not Path(settings.LLAMA_MODEL_PATH).exists():
    print(f"✗ Model file not found: {settings.LLAMA_MODEL_PATH}")
    sys.exit(1)

print(f"✓ Model path valid: {settings.LLAMA_MODEL_PATH}")

# Test 3: Initialize databases
print("\n3. Initializing databases...")
try:
    db = LSCPDatabase(settings.SQLITE_DB_PATH)
    vector_store = VectorStore(settings.VECTOR_DB_PATH, settings.CHROMA_COLLECTION_NAME)
    print("✓ Databases initialized")
except Exception as e:
    print(f"✗ Database init failed: {e}")
    sys.exit(1)

# Test 4: Load Control Model (MiniLM)
print("\n4. Loading Control Model (MiniLM)...")
try:
    control = ControlModel(settings.MINILM_MODEL_NAME)
    print("✓ Control model loaded")
except Exception as e:
    print(f"✗ Control model failed: {e}")
    sys.exit(1)

# Test 5: Test embedding generation
print("\n5. Testing embedding generation...")
try:
    test_embedding = control.encode("test")
    print(f"✓ Embedding generated (dimension: {len(test_embedding)})")
except Exception as e:
    print(f"✗ Embedding generation failed: {e}")
    sys.exit(1)

# Test 6: Load Explorer Model (llama.cpp)
print("\n6. Loading Explorer Model (llama.cpp)...")
print("   This may take a minute...")
try:
    explorer = ExplorerModel(
        model_path=settings.LLAMA_MODEL_PATH,
        n_ctx=settings.LLAMA_N_CTX,
        n_threads=settings.LLAMA_N_THREADS
    )
    print("✓ Explorer model loaded")
except Exception as e:
    print(f"✗ Explorer model failed: {e}")
    print(f"   Error details: {str(e)}")
    sys.exit(1)

# Test 7: Test llama embedding
print("\n7. Testing llama embedding generation...")
try:
    llama_embedding = explorer.encode("test")
    print(f"✓ Llama embedding generated (dimension: {len(llama_embedding)})")
except Exception as e:
    print(f"✗ Llama embedding failed: {e}")
    sys.exit(1)

# Test 8: Store and retrieve from vector DB
print("\n8. Testing vector storage...")
try:
    vector_store.add_human_embedding("test_concept", test_embedding)
    vector_store.add_latent_embedding("test_concept", llama_embedding)

    retrieved_human = vector_store.get_human_embedding("test_concept")
    retrieved_latent = vector_store.get_latent_embedding("test_concept")

    if retrieved_human is not None and retrieved_latent is not None:
        print("✓ Vector storage and retrieval working")
    else:
        print("✗ Could not retrieve stored embeddings")
        sys.exit(1)
except Exception as e:
    print(f"✗ Vector storage failed: {e}")
    sys.exit(1)

# Cleanup
db.close()

print("\n" + "="*60)
print("ALL TESTS PASSED!")
print("="*60)
print("\nYou're ready to run the scanner!")
print("\nTry:")
print("  python backend/main.py --scan 'time'")
print("  python backend/main.py --batch --batch-size 5")
