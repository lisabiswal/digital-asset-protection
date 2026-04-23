import os
import faiss
import sqlite3
import numpy as np
import logging
from typing import List, Tuple, Dict, Optional

logger = logging.getLogger(__name__)

# Paths relative to backend root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
INDEX_PATH = os.path.join(BASE_DIR, "data", "index.faiss")
DB_PATH = os.path.join(BASE_DIR, "data", "meta.db")

class FAISSIndex:
    def __init__(self):
        self.index = None
        self.video_metadata = []
        self._load_index()
        self._load_metadata()

    def _load_index(self):
        if not os.path.exists(INDEX_PATH):
            logger.error(f"FAISS index file not found at {INDEX_PATH}")
            return
        
        try:
            self.index = faiss.read_index(INDEX_PATH)
            logger.info(f"Loaded FAISS index with {self.index.ntotal} vectors")
        except Exception as e:
            logger.error(f"Error loading FAISS index: {e}")

    def _load_metadata(self):
        if not os.path.exists(DB_PATH):
            logger.error(f"SQLite database file not found at {DB_PATH}")
            return
        
        try:
            conn = sqlite3.connect(DB_PATH)
            cursor = conn.cursor()
            cursor.execute("SELECT id, faiss_start_idx, faiss_end_idx FROM videos ORDER BY faiss_start_idx")
            self.video_metadata = cursor.fetchall()
            conn.close()
            logger.info(f"Loaded metadata for {len(self.video_metadata)} videos")
        except Exception as e:
            logger.error(f"Error loading metadata: {e}")

    def _map_index_to_video(self, global_idx: int) -> Tuple[Optional[str], int]:
        """
        Maps a global FAISS index to a video_id and a local frame_idx.
        """
        # Since ranges are ordered, we can do a binary search or just linear search for small datasets
        for video_id, start, end in self.video_metadata:
            if start <= global_idx < end:
                frame_idx = global_idx - start
                return video_id, frame_idx
        return None, -1

    def query(self, embedding: np.ndarray, k: int = 10) -> List[Dict]:
        """
        Queries the index for the top k similar frames.
        
        Returns:
            List[Dict]: List of matches with keys: video_id, frame_idx, score
        """
        if self.index is None:
            logger.error("FAISS index is not initialized.")
            return []

        # Ensure embedding is float32 and has batch dimension
        query_vector = embedding.astype('float32').reshape(1, -1)
        
        scores, indices = self.index.search(query_vector, k)
        
        results = []
        for score, idx in zip(scores[0], indices[0]):
            if idx == -1:
                continue
                
            video_id, frame_idx = self._map_index_to_video(int(idx))
            if video_id:
                results.append({
                    "video_id": video_id,
                    "frame_idx": frame_idx,
                    "score": float(score)
                })
        
        return results

# Singleton instance
_faiss_index = None

def get_faiss_index():
    global _faiss_index
    if _faiss_index is None:
        _faiss_index = FAISSIndex()
    return _faiss_index

if __name__ == "__main__":
    # Quick test
    logging.basicConfig(level=logging.INFO)
    idx = get_faiss_index()
    if idx.index:
        # Query with a random vector
        dummy_query = np.random.randn(1280).astype('float32')
        dummy_query /= np.linalg.norm(dummy_query)
        
        res = idx.query(dummy_query, k=5)
        print(f"Query Results: {res}")
