# Tasks — Dev A (Backend · ML · Infrastructure)

> **Your domain:** Frame extraction, CNN embeddings, FAISS, FastAPI endpoints, Docker, Cloud Run, GCS, dataset indexing.

---

## Day 1 — Setup + Dataset

- [x] 1. Set up project structure
  - Create `backend/` directory layout (utils/, models/, scripts/, data/)
  - Write `requirements.txt` (fastapi, uvicorn, opencv-python, torch, torchvision, faiss-cpu, sqlite3)
  - Create `main.py` with FastAPI app skeleton and `GET /health` endpoint
  - Set up GCS client config and service account env handling

- [x] 2. Collect dataset
  - Install `yt-dlp`, download 3–5 sports clips (≤480p)
  - Run `scripts/make_variants.sh` to generate variants per clip:
    - Trimmed (`ffmpeg -ss 10 -t 30`)
    - Speed-changed (`setpts=0.75*PTS`)
    - Text overlay (`drawtext`)
    - Cropped (`crop=iw/2:ih/2`)
  - Target: ~15–20 total videos in `data/raw/`

---

## Day 2 — Fingerprinting Pipeline

- [x] 3. Frame extraction (`utils/frames.py`)
  - `extract_frames(video_path) -> List[np.ndarray]` at 1fps
  - Return metadata: `{duration_secs, frame_count}`
  - Handle corrupted/unreadable videos gracefully

- [x] 4. CNN embeddings (`utils/embeddings.py`)
  - Load MobileNetV2 pretrained (torchvision), strip classifier head
  - `generate_embedding(frame: np.ndarray) -> np.ndarray` → 1280-dim
  - Preprocess: resize 224×224, normalize with ImageNet stats
  - L2-normalize output for cosine similarity
  - `generate_embeddings_batch(frames) -> np.ndarray`

- [x] 4.2* Property test — embedding normalization
  - Assert `np.linalg.norm(embedding) ≈ 1.0` and `embedding.shape == (1280,)`

---

## Day 3 — FAISS + Matching

- [x] 5. Dataset indexer (`scripts/build_index.py`)
  - For each video in `data/raw/`: extract frames → generate embeddings
  - Build `faiss.IndexFlatIP` index, add all embeddings
  - Save `data/index.faiss` and `data/meta.db` (SQLite: videos table)
  - Store `faiss_start_idx / faiss_end_idx` per video in SQLite

- [x] 6. FAISS index module (`utils/faiss_index.py`)
  - `FAISSIndex` class: load from disk, `query(embedding, k=10)`
  - Returns `[(video_id, frame_idx, score)]`

- [x] 6.2* Property test — similarity score bounds
  - Assert all returned scores are in `[0.0, 1.0]`

- [x] 7. Match aggregator (`utils/match_aggregator.py`)
  - Group FAISS results by `video_id`
  - Compute `match_ratio = matched_frames / total_query_frames`
  - Compute `confidence = match_ratio × avg_similarity`
  - Label: strong ≥ 0.6, partial 0.3–0.6, weak < 0.3
  - Return top 5 ranked by confidence

- [x] 7.2* Property test — confidence thresholds
  - Assert confidence labels match expected thresholds

- [x] 8. Core API endpoints
  - `POST /upload` — validate file, save to GCS, return `upload_id`
  - `POST /process/{upload_id}` — extract frames + embeddings, store in-memory/temp
  - `POST /scan` — run FAISS query + aggregation, store results
  - `GET /matches?upload_id=X` — return ranked matches JSON

- [x] **Checkpoint:** Full pipeline works locally. Upload → process → scan → results returns real data.

---

## Day 4 — Docker + GCS + Cloud Run

- [ ] 9. GCS utilities (`utils/gcs.py`)
  - `upload_video(file_path, upload_id)` → GCS path
  - `download_video(upload_id)` → local temp path
  - Handle quota errors and network timeouts

- [ ] 10. SQLite schema + operations
  - Init script: `videos` table with all metadata fields
  - CRUD: insert video, get by id, list all

- [ ] 11. Dockerfile
  - Base: `python:3.11-slim`
  - Copy `data/index.faiss` + `data/meta.db` into image
  - `CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]`
  - Verify image size < 2GB

- [ ] 12. Cloud Run deploy (`deploy/cloud-run-deploy.sh`)
  - Push image to GCR
  - Deploy with: memory 2Gi, CPU 2, timeout 300s, `--allow-unauthenticated`

---

## Day 5 — Tuning + Polish + Demo Prep

- [ ] 13. Threshold tuning
  - Test all variant types (exact copy, trimmed, speed-changed, overlay, crop)
  - Adjust `MATCH_THRESHOLD` and `MIN_FRAME_MATCHES` for best precision/recall
  - Document final values in `README.md`

- [ ] 14. Error handling + logging
  - Add try/catch around GCS, FAISS, and torch operations
  - Return proper HTTP status codes (400, 422, 500) with error messages
  - Add structured logging with timestamps and processing times

- [ ] 15. Performance check
  - Measure end-to-end time for a 60s clip
  - Implement batch embedding if single-frame is too slow
  - Ensure Cloud Run cold start < 10s (index pre-loaded at startup)

- [ ] **Final checkpoint:** All 4 variant types detected correctly on live Cloud Run URL.

---

## Key Files You Own

```
backend/
├── main.py
├── utils/
│   ├── frames.py
│   ├── embeddings.py
│   ├── faiss_index.py
│   ├── match_aggregator.py
│   └── gcs.py
├── models/schemas.py
├── scripts/
│   └── build_index.py
├── data/
│   ├── raw/         ← dataset videos
│   ├── index.faiss  ← built on Day 3
│   └── meta.db
├── Dockerfile
└── deploy/cloud-run-deploy.sh
```