import cv2
import numpy as np
import logging
from typing import List, Tuple, Dict

logger = logging.getLogger(__name__)

def extract_frames(video_path: str) -> Tuple[List[np.ndarray], Dict]:
    """
    Extracts frames from a video file at 1 frame per second.
    
    Args:
        video_path (str): Path to the video file.
        
    Returns:
        Tuple[List[np.ndarray], Dict]: A list of extracted frames and a metadata dictionary.
        
    Raises:
        ValueError: If the video file cannot be opened or read.
    """
    cap = cv2.VideoCapture(video_path)
    
    if not cap.isOpened():
        logger.error(f"Failed to open video file: {video_path}")
        raise ValueError(f"Could not open video file: {video_path}")
    
    fps = cap.get(cv2.CAP_PROP_FPS)
    if fps == 0:
        logger.error(f"Could not determine FPS for video: {video_path}")
        cap.release()
        raise ValueError(f"Invalid FPS (0) for video: {video_path}")
        
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    duration_secs = total_frames / fps
    
    logger.info(f"Extracting frames from {video_path} (FPS: {fps:.2f}, Duration: {duration_secs:.2f}s)")
    
    frames = []
    frame_idx = 0
    
    # We want 1 frame per second.
    # The interval in terms of frame indices is exactly 'fps'.
    # We'll take frames at index 0, int(1*fps), int(2*fps), etc.
    
    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break
            
        # Check if current frame index is a multiple of the frame rate (approx 1fps)
        if frame_idx % int(round(fps)) == 0:
            # OpenCV reads in BGR, we usually want RGB for ML models
            frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            frames.append(frame_rgb)
            
        frame_idx += 1
        
    cap.release()
    
    metadata = {
        "duration_secs": round(duration_secs, 2),
        "frame_count": len(frames),
        "original_fps": round(fps, 2)
    }
    
    logger.info(f"Successfully extracted {len(frames)} frames from {video_path}")
    
    return frames, metadata

if __name__ == "__main__":
    # Quick test if run directly
    import sys
    if len(sys.argv) > 1:
        logging.basicConfig(level=logging.INFO)
        try:
            frames, meta = extract_frames(sys.argv[1])
            print(f"Metadata: {meta}")
            print(f"First frame shape: {frames[0].shape if frames else 'N/A'}")
        except Exception as e:
            print(f"Error: {e}")
