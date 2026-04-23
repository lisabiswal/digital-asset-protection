# Digital Sports Media Asset Protection System
### 5-Day Prototype Plan · Google Solution Challenge

---

## 1. Problem Definition

**What's happening:** Sports organizations publish official clips (match highlights, press content). These get ripped, re-uploaded with edits (cropped, sped up, text overlays), and redistributed without authorization — generating ad revenue for others.

**What this prototype solves:**
- Upload an official clip → find visually similar videos in a pre-collected dataset
- Return similarity scores and approximate matched timestamps
- Simulate detection of: exact copies, trimmed clips, edited versions

**What it does NOT solve:**
- Real-time internet scraping
- Live platform monitoring
- Legal takedown workflows
- Audio-only detection (optional, not core MVP)

---

## 2. Solution Overview

**Core idea:** Pre-fingerprint a dataset of "suspected infringing" videos offline. When an official clip is uploaded, extract its visual fingerprints (frame embeddings) and query FAISS to find nearest matches.

**Single service architecture** — one FastAPI container on Cloud Run handles upload, processing, matching, and serving the frontend (or frontend is static, hosted separately).

```
Upload → Extract Frames → CNN Embeddings → FAISS Query → Ranked Results
```

**Free services used:**
| Service | Use | Cost |
|---|---|---|
| Cloud Run | FastAPI backend | Free tier |
| Google Cloud Storage | Videos + FAISS index | Free tier (5GB) |
| YouTube Data API v3 | Fetch metadata/thumbnails | Free quota |
| SQLite | Metadata DB | Free (local/in-container) |
| Hugging Face / torchvision | CNN model weights | Free |

---

## 3. System Architecture

### Components

```
┌─────────────────────────────────────────────────────┐
│                   Cloud Run Container                │
│                                                      │
│  ┌──────────┐    ┌──────────────┐    ┌───────────┐  │
│  │ FastAPI  │───▶│  Processing  │───▶│   FAISS   │  │
│  │  Routes  │    │  Pipeline    │    │   Index   │  │
│  └──────────┘    │  (OpenCV +   │    └───────────┘  │
│       │          │  MobileNet)  │          │         │
│       │          └──────────────┘          │         │
│       ▼                                    ▼         │
│  ┌──────────┐                      ┌───────────┐    │
│  │  SQLite  │                      │  GCS      │    │
│  │  (meta)  │                      │  (videos) │    │
│  └──────────┘                      └───────────┘    │
└─────────────────────────────────────────────────────┘
         ▲
         │ HTTP
┌─────────────────┐
│  React Frontend │  (static, served from Cloud Run or GCS)
│  Upload + Results│
└─────────────────┘
```

### Data Flow

```
[User uploads clip]
        │
        ▼
POST /upload → save to GCS → return upload_id
        │
        ▼
POST /process/{id} → extract frames (1fps) → embed each frame (MobileNetV2)
        │
        ▼
POST /scan → query FAISS for each frame → aggregate by video_id → rank
        │
        ▼
GET /matches?upload_id=X → return top 3-5 matches with scores + timestamps
        │
        ▼
[Frontend displays cards: title, thumbnail, score, time range]
```

---

## 4. Core Features (MVP Only)

| Feature | In Scope |
|---|---|
| Upload official clip | ✅ |
| Frame extraction (1fps, OpenCV) | ✅ |
| CNN embedding generation (MobileNetV2) | ✅ |
| FAISS similarity search | ✅ |
| Match ranking + score | ✅ |
| Approximate matched timestamps | ✅ |
| Display thumbnails + YouTube link | ✅ |
| Audio fingerprinting | ⚠️ Optional stretch |
| Real-time scanning | ❌ |
| Automated takedowns | ❌ |

---

## 5. Technical Design

### Frame Extraction
```python
# 1 frame per second using OpenCV
cap = cv2.VideoCapture(video_path)
fps = cap.get(cv2.CAP_PROP_FPS)
frames = []
while cap.isOpened():
    ret, frame = cap.read()
    if not ret: break
    if int(cap.get(cv2.CAP_PROP_POS_FRAMES)) % int(fps) == 0:
        frames.append(frame)
```

### Embedding Model
- **Model:** MobileNetV2 (torchvision, pretrained on ImageNet)
- **Why:** Lightweight, runs on CPU, good visual feature extraction
- **Output:** 1280-dim vector per frame
- **Preprocessing:** resize to 224×224, normalize (ImageNet stats)

### Similarity Metric
- **FAISS index type:** `IndexFlatIP` (inner product = cosine similarity on normalized vectors)
- **Normalization:** L2-normalize all embeddings before indexing/querying

### Match Threshold Logic
```python
MATCH_THRESHOLD = 0.80   # per-frame cosine similarity
MIN_FRAME_MATCHES = 3    # minimum matching frames to count as a hit

# Per dataset video:
match_count = frames_above_threshold_for_video
avg_score = mean(top_frame_similarities_for_video)
confidence = (match_count / total_query_frames) * avg_score
```

- `confidence > 0.6` → Strong match
- `0.3 < confidence < 0.6` → Partial match
- `< 0.3` → No match

---

## 6. Dataset Strategy

### Collection (Pre-demo, before Day 1)
Collect 3–5 sports clips from YouTube using `yt-dlp` (free):
```bash
yt-dlp -f "best[height<=480]" "https://youtube.com/watch?v=..." -o "data/raw/%(id)s.%(ext)s"
```

### Variants to include per clip
| Type | How to create |
|---|---|
| Exact copy | Same file |
| Trimmed | `ffmpeg -ss 10 -t 30 -i input.mp4 trimmed.mp4` |
| Speed-changed | `ffmpeg -filter:v "setpts=0.75*PTS" input.mp4 fast.mp4` |
| Text overlay | `ffmpeg -vf "drawtext=text='GOAL':fontsize=40" input.mp4 overlay.mp4` |
| Cropped | `ffmpeg -vf "crop=iw/2:ih/2" input.mp4 cropped.mp4` |

**Target: ~15–20 total videos in dataset**

### Indexing Script (run once before demo)
```
python scripts/build_index.py
  → reads data/raw/*.mp4
  → extracts frames → generates embeddings
  → builds FAISS index → saves to data/index.faiss
  → saves metadata to data/meta.db (SQLite)
```

### SQLite Schema
```sql
CREATE TABLE videos (
  id TEXT PRIMARY KEY,       -- youtube_id or filename hash
  title TEXT,
  thumbnail_url TEXT,
  youtube_url TEXT,
  duration_secs INTEGER,
  frame_count INTEGER,
  faiss_start_idx INTEGER,   -- first FAISS vector index for this video
  faiss_end_idx INTEGER
);
```

---

## 7. API Design

### `POST /upload`
Upload official clip for scanning.
```json
// Request: multipart/form-data
{ "file": <video_file> }

// Response
{ "upload_id": "abc123", "status": "uploaded", "gcs_path": "gs://bucket/uploads/abc123.mp4" }
```

### `POST /process/{upload_id}`
Extract frames and generate embeddings for uploaded clip.
```json
// Response
{ "upload_id": "abc123", "frame_count": 42, "status": "processed" }
```

### `POST /scan`
Run FAISS matching against dataset.
```json
// Request
{ "upload_id": "abc123" }

// Response
{ "upload_id": "abc123", "status": "complete", "match_count": 3 }
```

### `GET /matches?upload_id=abc123`
Return ranked match results.
```json
{
  "upload_id": "abc123",
  "matches": [
    {
      "video_id": "dQw4w9WgXcQ",
      "title": "Champions League Highlights",
      "thumbnail_url": "https://i.ytimg.com/vi/dQw4w9WgXcQ/hqdefault.jpg",
      "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ",
      "similarity_score": 0.91,
      "confidence": "strong",
      "matched_frames": 28,
      "matched_segment": { "start_sec": 10, "end_sec": 38 }
    }
  ]
}
```

### `GET /health`
```json
{ "status": "ok", "index_loaded": true, "dataset_size": 18 }
```

---

## 8. Frontend Plan

**Stack:** React + TypeScript + Vite (simple, no heavy deps)

### Pages

#### Upload Page (`/`)
- Drag-and-drop video upload area
- "Scan for Unauthorized Use" button
- Progress indicator (uploading → processing → scanning)
- Shows estimated time

#### Results Page (`/results/:upload_id`)
- Header: "3 potential matches found" (or "No matches found")
- Match cards grid, each showing:
  - Video thumbnail
  - Title
  - Similarity score (color-coded: red > 0.8, yellow 0.5–0.8, green < 0.5)
  - Confidence label (Strong / Partial / Weak)
  - Matched segment: `00:10 – 00:38`
  - "View on YouTube" link
- Sort by score descending

### State Flow
```
idle → uploading (POST /upload) → processing (POST /process) 
     → scanning (POST /scan) → polling GET /matches → results
```

---

## 9. Cloud Deployment Plan

### Dockerfile (single container)
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
# Copy pre-built FAISS index + SQLite into image (for demo simplicity)
COPY data/index.faiss data/
COPY data/meta.db data/
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
```

### FAISS Index Strategy (stateless container)
For demo: **bundle index into Docker image** (simplest, no cold-load latency).
```
data/index.faiss  (~10–50MB for 20 videos)  → baked into image
data/meta.db      (~small)                  → baked into image
```
Uploaded videos → write to GCS (container is ephemeral).

### Cloud Run Config
```yaml
# cloud-run-deploy.sh
gcloud run deploy sports-media-guard \
  --image gcr.io/$PROJECT_ID/sports-media-guard \
  --platform managed \
  --region us-central1 \
  --memory 2Gi \
  --cpu 2 \
  --timeout 300 \
  --allow-unauthenticated \
  --set-env-vars GCS_BUCKET=your-bucket-name
```

### GCS Bucket
```
gs://sports-media-guard-demo/
  uploads/          ← user-uploaded clips (temp)
  dataset/          ← original dataset videos
```

### Frontend Deployment
Build React app → `npm run build` → deploy `dist/` to GCS as static site (free).
Or serve from FastAPI using `StaticFiles`.

---

## 10. 5-Day Execution Plan

**Dev A** = Backend / ML / Infrastructure  
**Dev B** = Frontend / Dataset / Integration

---

### Day 1 — Setup + Dataset + Project Scaffold

| Dev A | Dev B |
|---|---|
| Set up GCP project, enable Cloud Run + GCS APIs | Set up React + TypeScript + Vite frontend scaffold |
| Create GCS bucket, configure service account | Design Upload page UI (static, no backend yet) |
| Collect 3–5 YouTube clips with `yt-dlp` | Create Results page UI with mock data |
| Create ffmpeg variants (trimmed, sped up, overlay, crop) | Set up routing (`/`, `/results/:id`) |
| Set up FastAPI project structure | Set up API client (`api.ts` with typed fetch functions) |
| Implement `GET /health` | Implement upload drag-and-drop component |

**End of Day 1:** Both repos initialized, dataset collected (~15 videos), UI mockups working with static data.

---

### Day 2 — Fingerprinting Pipeline

| Dev A | Dev B |
|---|---|
| Implement frame extraction (`utils/frames.py`) | Implement progress/status polling UI |
| Implement MobileNetV2 embedding (`utils/embeddings.py`) | Wire upload page to `POST /upload` |
| Test pipeline on 2–3 dataset videos end-to-end | Style match cards (thumbnail, score badge, segment) |
| Write `scripts/build_index.py` (index builder) | Implement `GET /matches` result rendering |

**End of Day 2:** Frame extraction + embedding pipeline works. Frontend connects to upload endpoint.

---

### Day 3 — FAISS Matching + Core API

| Dev A | Dev B |
|---|---|
| Run `build_index.py` on full dataset → generate `index.faiss` + `meta.db` | Integrate full API flow: upload → process → scan → results |
| Implement `POST /process/{id}` | Handle loading states + errors in frontend |
| Implement `POST /scan` with FAISS query + aggregation | Test frontend end-to-end with real backend |
| Implement `GET /matches` with ranking | Add YouTube thumbnail fetching from metadata |
| Tune MATCH_THRESHOLD with test clips | Polish results page with real data |

**End of Day 3:** Full pipeline works locally. Upload a clip → get real match results.

---

### Day 4 — Integration + Docker + GCS

| Dev A | Dev B |
|---|---|
| Write Dockerfile, test container locally | Fix any integration bugs found during full flow testing |
| Implement GCS upload for incoming videos | Add score color-coding + confidence labels |
| Build Docker image, push to GCR | Build production frontend (`npm run build`) |
| Deploy to Cloud Run (test endpoint) | Configure frontend to point to Cloud Run URL |
| Fix any container/environment issues | Deploy frontend (GCS static or serve from FastAPI) |

**End of Day 4:** Running on Cloud Run. Both devs can demo full flow on live URL.

---

### Day 5 — Polish + Demo Prep

| Dev A | Dev B |
|---|---|
| Final threshold tuning with all dataset variants | UI polish: animations, loading states, typography |
| Ensure index is correctly bundled in Docker image | Prepare 3 demo videos (exact copy, trimmed, edited) |
| Test cold start + response times | Write demo script, practice walkthrough |
| Set up monitoring/logs on Cloud Run | Record backup screenshots in case of live issues |
| Final deploy with production build | Prepare slide deck summary (optional) |

**End of Day 5:** Demo-ready. All variant types detected correctly.

---

## 11. Demo Flow

**Pre-loaded dataset:** 5 original clips (sports highlights), with 3 variants each = ~18 total videos indexed.

### Step-by-step script

1. **Open app** → show upload page
2. **Upload Test 1:** Upload an exact copy of a dataset clip
   - Expected: Strong match, score ~0.90–0.95, full timestamp range
3. **Upload Test 2:** Upload a trimmed version (e.g., 10-second clip from the middle)
   - Expected: Partial match, score ~0.75–0.85, narrow timestamp range
4. **Upload Test 3:** Upload speed-changed or text-overlay version
   - Expected: Match detected despite edits, score ~0.65–0.80
5. **Upload Test 4:** Upload a completely unrelated video
   - Expected: "No matches found" or very low scores < 0.3
6. **Show results card:** Explain score, matched segment, YouTube link

**Talking points:**
- "This simulates what a rights holder sees when they upload their official clip"
- "Even with edits like crop or text overlay, the visual fingerprint is preserved"
- "FAISS enables sub-second search across thousands of videos at scale"

---

## 12. Limitations

| Limitation | Impact |
|---|---|
| Dataset is pre-collected, not live-scraped | Only detects from known dataset — not real-world internet |
| No real-time scanning | Must manually upload to trigger search |
| FAISS index bundled in image | Re-deploying required to add new videos to dataset |
| CPU inference only | MobileNet embedding ~2–5s per minute of video |
| Single region (Cloud Run) | No geographic distribution |
| No audio fingerprinting (MVP) | Can miss audio-matched but visually different clips |
| ~15–20 video dataset | Not representative of real scale |

---

## 13. Folder Structure

```
sports-media-guard/
├── backend/
│   ├── main.py                   # FastAPI app, all routes
│   ├── utils/
│   │   ├── frames.py             # OpenCV frame extraction
│   │   ├── embeddings.py         # MobileNetV2 embedding
│   │   ├── faiss_index.py        # FAISS load/query
│   │   └── gcs.py                # GCS upload/download helpers
│   ├── models/
│   │   └── schemas.py            # Pydantic request/response models
│   ├── scripts/
│   │   └── build_index.py        # One-time dataset indexing script
│   ├── data/
│   │   ├── raw/                  # Dataset videos (local, pre-demo)
│   │   ├── index.faiss           # Built FAISS index (bundled in image)
│   │   └── meta.db               # SQLite metadata
│   ├── Dockerfile
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── src/
│   │   ├── pages/
│   │   │   ├── UploadPage.tsx
│   │   │   └── ResultsPage.tsx
│   │   ├── components/
│   │   │   ├── DropZone.tsx
│   │   │   ├── MatchCard.tsx
│   │   │   ├── ProgressTracker.tsx
│   │   │   └── ScoreBadge.tsx
│   │   ├── api/
│   │   │   └── client.ts         # Typed API fetch functions
│   │   ├── types/
│   │   │   └── index.ts          # Shared TypeScript types
│   │   └── main.tsx
│   ├── vite.config.ts
│   ├── tsconfig.json
│   └── package.json
│
├── scripts/
│   ├── collect_dataset.sh        # yt-dlp download commands
│   └── make_variants.sh          # ffmpeg variant generation
│
├── deploy/
│   └── cloud-run-deploy.sh
│
└── README.md
```

---

## 14. Risks and Mitigations

| Risk | Likelihood | Mitigation |
|---|---|---|
| Slow CPU inference on Cloud Run | High | Use MobileNetV2 (fast), process async, show progress UI |
| Cold start latency (FAISS load) | Medium | Bundle index in image, use Cloud Run min-instances=1 if needed (free tier allows) |
| False positives on unrelated clips | Medium | Tune MIN_FRAME_MATCHES + MATCH_THRESHOLD with real test clips on Day 3 |
| GCS upload timeout for large files | Low | Limit upload to 60–120 sec clips for demo; validate size on frontend |
| YouTube Data API quota exceeded | Low | Cache thumbnails/metadata in SQLite after first fetch; ~10,000 units/day free |
| FAISS index mismatch after rebuild | Low | Version-stamp index + metadata together; validate on startup via `/health` |
| Docker image too large | Low | Use `python:3.11-slim`, exclude raw dataset videos from image |
| Demo network issues (live) | Medium | Pre-record screen capture as backup; pre-warm Cloud Run before presentation |

---

*Built for Google Solution Challenge · 2 developers · 5 days · All free services*