import sys
import os
import numpy as np
import logging

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.embeddings import get_embedding_generator

def test_embedding_properties():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("PropertyTest")
    
    gen = get_embedding_generator()
    
    # Test with random frames
    for i in range(10):
        # Random RGB frame
        frame = np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8)
        
        embedding = gen.generate_embedding(frame)
        
        # Property 1: Shape is (1280,)
        assert embedding.shape == (1280,), f"Expected shape (1280,), got {embedding.shape}"
        
        # Property 2: L2 Norm is approximately 1.0
        norm = np.linalg.norm(embedding)
        assert np.isclose(norm, 1.0, atol=1e-5), f"Expected L2 norm ~1.0, got {norm}"
        
        # Property 3: No NaN or Inf
        assert not np.isnan(embedding).any(), "Embedding contains NaN"
        assert not np.isinf(embedding).any(), "Embedding contains Inf"
        
    logger.info("✅ Single embedding property tests passed!")
    
    # Test batch properties
    batch_size = 8
    frames = [np.random.randint(0, 255, (224, 224, 3), dtype=np.uint8) for _ in range(batch_size)]
    embeddings = gen.generate_embeddings_batch(frames)
    
    assert embeddings.shape == (batch_size, 1280), f"Expected batch shape {(batch_size, 1280)}, got {embeddings.shape}"
    for emb in embeddings:
        assert np.isclose(np.linalg.norm(emb), 1.0, atol=1e-5)
        
    logger.info("✅ Batch embedding property tests passed!")

if __name__ == "__main__":
    try:
        test_embedding_properties()
        print("ALL PROPERTY TESTS PASSED")
    except AssertionError as e:
        print(f"PROPERTY TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"ERROR DURING TESTING: {e}")
        sys.exit(1)
