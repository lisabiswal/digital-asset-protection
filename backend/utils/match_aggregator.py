import sqlite3
import os
import logging
from typing import List, Dict
import numpy as np

logger = logging.getLogger(__name__)

# Paths relative to backend root
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, "data", "meta.db")

def get_video_metadata(video_ids: List[str]) -> Dict[str, Dict]:
    """Fetches full metadata for a list of video IDs from the SQLite database."""
    if not video_ids:
        return {}
        
    placeholders = ','.join(['?'] * len(video_ids))
    metadata = {}
    
    try:
        conn = sqlite3.connect(DB_PATH)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM videos WHERE id IN ({placeholders})", video_ids)
        rows = cursor.fetchall()
        for row in rows:
            metadata[row['id']] = dict(row)
        conn.close()
    except Exception as e:
        logger.error(f"Error fetching video metadata: {e}")
        
    return metadata

def aggregate_matches(faiss_results: List[List[Dict]], total_query_frames: int) -> List[Dict]:
    """
    Aggregates frame-level FAISS results into video-level matches.
    
    Args:
        faiss_results: A list of lists, where each sublist contains the top k matches for a query frame.
        total_query_frames: The total number of frames in the query video.
        
    Returns:
        List[Dict]: Ranked list of video matches.
    """
    if total_query_frames == 0:
        return []

    # Map video_id -> { matched_frames: set(query_frame_indices), total_score: float }
    video_stats = {}
    
    for query_frame_idx, top_k_matches in enumerate(faiss_results):
        for match in top_k_matches:
            vid = match["video_id"]
            score = match["score"]
            
            if vid not in video_stats:
                video_stats[vid] = {
                    "matched_frames": set(),
                    "scores": [],
                    "frame_pairs": [] # (query_frame, target_frame)
                }
            
            # We only count a frame as matched if score is above a threshold
            # Although the requirement says aggregate, a threshold helps filter noise.
            # plan.md mentions MATCH_THRESHOLD = 0.80
            if score >= 0.70: 
                video_stats[vid]["matched_frames"].add(query_frame_idx)
                video_stats[vid]["scores"].append(score)
                video_stats[vid]["frame_pairs"].append((query_frame_idx, match["frame_idx"]))

    # Fetch metadata for all matched videos
    metadata_map = get_video_metadata(list(video_stats.keys()))
    
    aggregated_results = []
    
    for vid, stats in video_stats.items():
        if not stats["scores"]:
            continue
            
        matched_count = len(stats["matched_frames"])
        avg_score = np.mean(stats["scores"])
        match_ratio = matched_count / total_query_frames
        
        # Confidence logic from plan.md: confidence = match_ratio * avg_similarity
        confidence_score = match_ratio * avg_score
        
        # Labeling
        if confidence_score >= 0.6:
            label = "strong"
        elif confidence_score >= 0.3:
            label = "partial"
        else:
            label = "weak"
            
        # Determine matched segment (simplified: min and max matched query seconds)
        matched_query_frames = sorted(list(stats["matched_frames"]))
        start_sec = matched_query_frames[0]
        end_sec = matched_query_frames[-1]
        
        meta = metadata_map.get(vid, {}) or {}

        thumbnail_url = meta.get("thumbnail_url") or ""
        youtube_url = meta.get("youtube_url") or ""
        title = meta.get("title") or vid
        
        aggregated_results.append({
            "video_id": vid,
            "title": title,
            "thumbnail_url": thumbnail_url,
            "youtube_url": youtube_url,
            "similarity_score": float(avg_score),
            "confidence": label,
            "confidence_score": float(confidence_score),
            "matched_frames": matched_count,
            "matched_segment": {
                "start_sec": int(start_sec),
                "end_sec": int(end_sec)
            }
        })

    # Rank by confidence score descending
    aggregated_results.sort(key=lambda x: x["confidence_score"], reverse=True)
    
    return aggregated_results[:5] # Return top 5
