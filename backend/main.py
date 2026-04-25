import os
import uuid
import logging
import shutil
import textwrap
import numpy as np
from fastapi import FastAPI, UploadFile, File, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from models.schemas import (
    HealthResponse, UploadResponse, ProcessResponse, 
    ScanRequest, ScanResponse, MatchesResponse
)
from utils.frames import extract_frames
from utils.embeddings import get_embedding_generator
from utils.faiss_index import get_faiss_index
from utils.match_aggregator import aggregate_matches
from utils.gcs import get_gcs_manager
from utils.db import get_db_manager

# Load environment variables
load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

description_text = textwrap.dedent("""
## Quick Start (Judge Instructions)

This system detects unauthorized sports media by comparing video fingerprints.

### Steps to Test

1. **Upload a video**
   - Endpoint: `POST /upload`
   - Action: Upload a sample clip
   - Output: Returns `upload_id`

2. **Process the video**
   - Endpoint: `POST /process/{upload_id}`
   - Action: Generate fingerprints for the uploaded video

3. **Scan for matches**
   - Endpoint: `POST /scan`
   - Body:
     {
       "upload_id": "<your_upload_id>"
     }

4. **View results**
   - Endpoint: `GET /matches?upload_id=<your_upload_id>`
   - Output: Returns matched videos with similarity scores

""")

app = FastAPI(
    title="🛡️ Sports Asset Protection System",
    description=description_text,
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# In-memory storage for prototype session state
# In production, use Redis
processed_data = {} # upload_id -> { embeddings: np.ndarray, frame_count: int }
scan_results = {}   # upload_id -> List[MatchResult]

# Local directory for temporary storage
STORAGE_DIR = "backend/data/uploads"
os.makedirs(STORAGE_DIR, exist_ok=True)

@app.get("/health", response_model=HealthResponse)
async def health_check():
    faiss_idx = get_faiss_index()
    gcs = get_gcs_manager()
    return {
        "status": "healthy",
        "gcs_initialized": gcs.client is not None,
        "bucket": gcs.bucket_name,
        "index_loaded": faiss_idx.index is not None,
        "dataset_size": faiss_idx.index.ntotal if faiss_idx.index else 0
    }

@app.post("/upload", response_model=UploadResponse)
async def upload_video(file: UploadFile = File(...)):
    upload_id = str(uuid.uuid4())
    file_extension = file.filename.split(".")[-1]
    local_path = os.path.join(STORAGE_DIR, f"{upload_id}.{file_extension}")
    
    try:
        # 1. Save locally first
        with open(local_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # 2. Upload to GCS in the background (or foreground for hackathon simplicity)
        gcs = get_gcs_manager()
        gcs_uri = gcs.upload_video(local_path, upload_id)
        
        return {
            "upload_id": upload_id,
            "status": "uploaded",
            "gcs_path": gcs_uri
        }
    except Exception as e:
        logger.error(f"Upload failed: {e}")
        raise HTTPException(status_code=500, detail="Upload failed")

@app.post("/process/{upload_id}", response_model=ProcessResponse)
async def process_video(upload_id: str):
    # Find the uploaded file
    files = [f for f in os.listdir(STORAGE_DIR) if f.startswith(upload_id)]
    if not files:
        raise HTTPException(status_code=404, detail="Upload not found")
        
    video_path = os.path.join(STORAGE_DIR, files[0])
    
    try:
        # 1. Extract Frames
        frames, meta = extract_frames(video_path)
        
        # 2. Generate Embeddings
        embedding_gen = get_embedding_generator()
        embeddings = embedding_gen.generate_embeddings_batch(frames)
        
        # 3. Store in-memory
        processed_data[upload_id] = {
            "embeddings": embeddings,
            "frame_count": meta["frame_count"]
        }
        
        logger.info(f"Video {upload_id} processed: {meta['frame_count']} frames")
        
        return {
            "upload_id": upload_id,
            "frame_count": meta["frame_count"],
            "status": "processed"
        }
    except Exception as e:
        logger.error(f"Processing failed for {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/scan", response_model=ScanResponse)
async def scan_video(request: ScanRequest):
    upload_id = request.upload_id
    
    if upload_id not in processed_data:
        raise HTTPException(status_code=404, detail="Video not processed yet")
        
    try:
        data = processed_data[upload_id]
        embeddings = data["embeddings"]
        
        # 1. FAISS Query for each frame
        faiss_idx = get_faiss_index()
        all_frame_matches = []
        for emb in embeddings:
            all_frame_matches.append(faiss_idx.query(emb, k=10))
            
        # 2. Aggregate Results
        results = aggregate_matches(all_frame_matches, data["frame_count"])
        
        # 3. Store results
        scan_results[upload_id] = results
        
        logger.info(f"Scan complete for {upload_id}: found {len(results)} matches")
        
        return {
            "upload_id": upload_id,
            "status": "complete",
            "match_count": len(results)
        }
    except Exception as e:
        logger.error(f"Scan failed for {upload_id}: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/matches", response_model=MatchesResponse)
async def get_matches(upload_id: str):
    if upload_id not in scan_results:
        raise HTTPException(status_code=404, detail="Scan results not found")
        
    return {
        "upload_id": upload_id,
        "matches": scan_results[upload_id]
    }

if __name__ == "__main__":
    import uvicorn
    # Use 8080 for Cloud Run compatibility
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))
