import os
import sys
import sqlite3
import faiss
import numpy as np
import logging
from glob import glob

# Add backend to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.frames import extract_frames
from utils.embeddings import get_embedding_generator

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Constants
DATA_DIR = os.path.join("backend", "data")
RAW_DIR = os.path.join(DATA_DIR, "raw")
INDEX_PATH = os.path.join(DATA_DIR, "index.faiss")
DB_PATH = os.path.join(DATA_DIR, "meta.db")
EMBEDDING_DIM = 1280

def init_db():
    """Initializes the SQLite database with the videos table."""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS videos (
            id TEXT PRIMARY KEY,
            title TEXT,
            thumbnail_url TEXT,
            youtube_url TEXT,
            duration_secs REAL,
            frame_count INTEGER,
            faiss_start_idx INTEGER,
            faiss_end_idx INTEGER
        )
    ''')
    conn.commit()
    return conn

def build_index():
    """Extracts frames, generates embeddings, and builds the FAISS index."""
    if not os.path.exists(RAW_DIR):
        logger.error(f"Raw data directory not found: {RAW_DIR}")
        return

    conn = init_db()
    cursor = conn.cursor()
    
    # Initialize FAISS index
    # IndexFlatIP is used for inner product (cosine similarity on L2-normalized vectors)
    index = faiss.IndexFlatIP(EMBEDDING_DIM)
    
    embedding_gen = get_embedding_generator()
    
    video_files = glob(os.path.join(RAW_DIR, "*.mp4"))
    logger.info(f"Found {len(video_files)} videos in {RAW_DIR}")
    
    current_faiss_idx = 0
    
    for video_path in video_files:
        video_id = os.path.basename(video_path)
        logger.info(f"Processing video: {video_id}")
        
        try:
            # Extract frames
            frames, meta = extract_frames(video_path)
            
            if not frames:
                logger.warning(f"No frames extracted for {video_id}. Skipping.")
                continue
            
            # Generate embeddings
            embeddings = embedding_gen.generate_embeddings_batch(frames)
            
            # Add to FAISS index
            index.add(embeddings.astype('float32'))
            
            # Update database
            faiss_start_idx = current_faiss_idx
            faiss_end_idx = current_faiss_idx + len(frames)
            
            cursor.execute('''
                INSERT OR REPLACE INTO videos 
                (id, title, duration_secs, frame_count, faiss_start_idx, faiss_end_idx)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                video_id,
                video_id.replace(".mp4", "").replace("_", " ").title(),
                meta["duration_secs"],
                meta["frame_count"],
                faiss_start_idx,
                faiss_end_idx
            ))
            
            current_faiss_idx = faiss_end_idx
            logger.info(f"Added {len(frames)} vectors to index for {video_id} (Indices: {faiss_start_idx}-{faiss_end_idx})")
            
        except Exception as e:
            logger.error(f"Error processing {video_id}: {e}")
            continue

    # Save index and DB
    faiss.write_index(index, INDEX_PATH)
    conn.commit()
    conn.close()
    
    logger.info(f"Indexing complete. Index saved to {INDEX_PATH}. Database saved to {DB_PATH}.")
    logger.info(f"Total vectors in index: {index.ntotal}")

if __name__ == "__main__":
    build_index()
