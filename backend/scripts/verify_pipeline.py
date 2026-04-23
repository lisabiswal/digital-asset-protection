# Location: backend/scripts/verify_pipeline.py
import sys, os, random, logging
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from utils.frames import extract_frames
from utils.embeddings import get_embedding_generator
from utils.faiss_index import get_faiss_index
from utils.match_aggregator import aggregate_matches

def run_verify():
    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger("VerifyPipeline")
    
    # 1. Pick a sample video
    raw_videos = [f for f in os.listdir("backend/data/raw") if f.endswith(".mp4")]
    sample_video = os.path.join("backend/data/raw", random.choice(raw_videos))
    logger.info(f"Targeting sample video for verification: {sample_video}")
    
    # 2. Extract Frames
    frames, meta = extract_frames(sample_video)
    
    # 3. Generate Embeddings
    gen = get_embedding_generator()
    embeddings = gen.generate_embeddings_batch(frames)
    
    # 4. Query FAISS
    idx = get_faiss_index()
    all_frame_matches = []
    for emb in embeddings:
        all_frame_matches.append(idx.query(emb, k=5))
        
    # 5. Aggregate Results
    results = aggregate_matches(all_frame_matches, len(frames))
    
    logger.info("--- SCAN RESULTS ---")
    for res in results:
        logger.info(f"MATCH: {res['title']} | Score: {res['similarity_score']:.2f} | Confidence: {res['confidence'].upper()}")
        logger.info(f"       Segment: {res['matched_segment']['start_sec']}s - {res['matched_segment']['end_sec']}s")

if __name__ == "__main__":
    run_verify()
