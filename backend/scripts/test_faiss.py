import sys
import os
import numpy as np
import logging

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.faiss_index import get_faiss_index

def test_faiss_properties():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("FAISSTest")
    
    idx = get_faiss_index()
    if not idx.index:
        logger.error("FAISS index not loaded. Run build_index.py first.")
        sys.exit(1)
        
    # Test with random normalized vectors
    for i in range(10):
        query = np.random.randn(1280).astype('float32')
        query /= np.linalg.norm(query)
        
        results = idx.query(query, k=10)
        
        for res in results:
            score = res["score"]
            # Property: Score in [0.0, 1.0] for cosine similarity of normalized vectors
            # (Technically IndexFlatIP can give > 1.0 due to floating point or non-unit vectors, 
            # but since we L2-normalized in build_index, it should be <= 1.0)
            assert 0.0 <= score <= 1.01, f"Score out of bounds: {score}"
            assert "video_id" in res
            assert "frame_idx" in res
            
    logger.info("✅ FAISS similarity score property tests passed!")

if __name__ == "__main__":
    try:
        test_faiss_properties()
        print("ALL FAISS PROPERTY TESTS PASSED")
    except AssertionError as e:
        print(f"FAISS PROPERTY TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR DURING TESTING: {e}")
        sys.exit(1)
