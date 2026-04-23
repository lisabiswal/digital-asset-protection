from pydantic import BaseModel
from typing import List, Optional

class UploadResponse(BaseModel):
    upload_id: str
    status: str
    gcs_path: Optional[str] = None

class ProcessResponse(BaseModel):
    upload_id: str
    frame_count: int
    status: str

class ScanRequest(BaseModel):
    upload_id: str

class ScanResponse(BaseModel):
    upload_id: str
    status: str
    match_count: int

class MatchSegment(BaseModel):
    start_sec: int
    end_sec: int

class MatchResult(BaseModel):
    video_id: str
    title: str
    thumbnail_url: str
    youtube_url: str
    similarity_score: float
    confidence: str
    matched_frames: int
    matched_segment: MatchSegment

class MatchesResponse(BaseModel):
    upload_id: str
    matches: List[MatchResult]

class HealthResponse(BaseModel):
    status: str
    gcs_initialized: bool
    bucket: str
    index_loaded: bool
    dataset_size: int
