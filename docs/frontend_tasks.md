# Tasks — Dev B (Frontend · Integration · Demo)

> **Your domain:** React frontend, API client, UI components, integration wiring, YouTube metadata, demo prep.

---

## Day 1 — Frontend Scaffold + UI Mockups

- [ ] 1. Set up frontend project
  - `npm create vite@latest frontend -- --template react-ts`
  - Install deps: `react-router-dom`, `axios` (or native fetch)
  - Set up routing: `/` (Upload), `/results/:uploadId` (Results)
  - Create `src/types/index.ts` with shared TypeScript types:
    ```ts
    interface MatchResult {
      video_id: string;
      title: string;
      thumbnail_url: string;
      youtube_url: string;
      similarity_score: number;
      confidence: 'strong' | 'partial' | 'weak';
      matched_frames: number;
      matched_segment: { start_sec: number; end_sec: number };
    }
    interface UploadResponse { upload_id: string; status: string; }
    interface ProcessResponse { upload_id: string; frame_count: number; status: string; }
    interface ScanResponse { upload_id: string; status: string; match_count: number; }
    ```

- [ ] 2. Build Upload page (`src/pages/UploadPage.tsx`)
  - Drag-and-drop zone + file picker (accept `video/*`)
  - Show selected filename + file size
  - "Scan for Unauthorized Use" button (disabled until file selected)
  - Static for now — no API calls yet

- [ ] 3. Build Results page (`src/pages/ResultsPage.tsx`)
  - Header: "X potential matches found"
  - Grid of `<MatchCard />` components
  - Use mock data to validate layout

- [ ] 4. Build `<MatchCard />` component (`src/components/MatchCard.tsx`)
  - Thumbnail image
  - Video title
  - Score badge (color-coded: red ≥ 0.8, yellow 0.5–0.8, green < 0.5)
  - Confidence label pill (Strong / Partial / Weak)
  - Matched segment: `00:10 – 00:38` (format seconds → `mm:ss`)
  - "View on YouTube" external link

---

## Day 2 — API Client + Progress UI

- [ ] 5. Create API client (`src/api/client.ts`)
  - Base URL from `import.meta.env.VITE_API_URL`
  - Typed functions:
    ```ts
    uploadVideo(file: File): Promise<UploadResponse>
    processVideo(uploadId: string): Promise<ProcessResponse>
    scanVideo(uploadId: string): Promise<ScanResponse>
    getMatches(uploadId: string): Promise<MatchResult[]>
    ```
  - Handle non-2xx responses, throw typed errors

- [ ] 6. Build `<ProgressTracker />` component
  - 4 steps: Uploading → Processing → Scanning → Done
  - Each step shows: idle / active (spinner) / complete (checkmark) / error
  - Used on Upload page while API calls are in flight

- [ ] 7. Wire Upload page to API
  - On submit: `uploadVideo()` → `processVideo()` → `scanVideo()` → navigate to `/results/:uploadId`
  - Show `<ProgressTracker />` during each step
  - On error: show inline error message, allow retry

---

## Day 3 — Results Wiring + Thumbnail Fetching

- [ ] 8. Wire Results page to API
  - On mount: `getMatches(uploadId)` 
  - Handle loading state, empty state ("No matches found"), error state
  - Sort matches by `similarity_score` descending

- [ ] 9. YouTube thumbnail + metadata
  - Dev A's SQLite stores `thumbnail_url` from YouTube Data API
  - Confirm thumbnail URL format: `https://i.ytimg.com/vi/{VIDEO_ID}/hqdefault.jpg`
  - Use directly in `<MatchCard />` — no additional API call needed from frontend
  - Fallback: grey placeholder if thumbnail fails to load (`onError`)

- [ ] 10. `<ScoreBadge />` component (`src/components/ScoreBadge.tsx`)
  - Renders score as percentage (e.g., `91%`)
  - Color: `#ef4444` (red, strong), `#f59e0b` (yellow, partial), `#22c55e` (green, weak)
  - Small pill shape, monospace font

- [ ] 11. Format helper (`src/utils/format.ts`)
  - `formatSeconds(secs: number): string` → `"01:23"`
  - `formatSegment(start: number, end: number): string` → `"01:10 – 01:38"`

- [ ] **Checkpoint (with Dev A):** Full flow works end-to-end with real backend. Upload a clip → see real match cards.

---

## Day 4 — Integration + Polish

- [ ] 12. Connect frontend to deployed Cloud Run URL
  - Set `VITE_API_URL` in `.env.production` to Cloud Run endpoint
  - Test all flows on live backend
  - Fix any CORS issues (Dev A adds CORS middleware on FastAPI)

- [ ] 13. Handle edge cases in UI
  - File too large (> 100MB): show error before upload
  - Unsupported format: validate `video/*` MIME type
  - No matches found: show friendly empty state with icon
  - API timeout: show "Processing is taking longer than expected" message

- [ ] 14. Deploy frontend
  - `npm run build` → `dist/`
  - Option A: `gcloud storage cp -r dist/* gs://your-bucket/frontend/` (serve as static from GCS)
  - Option B: Copy `dist/` into Docker image, serve via FastAPI `StaticFiles` (coordinate with Dev A)

- [ ] 15. UI polish pass
  - Consistent spacing, font, color tokens (use CSS variables)
  - Smooth transitions on page navigation
  - Responsive layout (works on laptop screen for demo)
  - Favicon + page title: "SportsGuard"

---

## Day 5 — Demo Prep

- [ ] 16. Prepare demo videos (3 test cases)
  - **Test 1:** Exact copy of a dataset clip → expect strong match (≥ 0.85)
  - **Test 2:** Trimmed version (10–20s from middle) → expect partial match (0.6–0.85)
  - **Test 3:** Speed-changed or text-overlay version → expect match despite edits
  - **Test 4:** Completely unrelated clip → expect no matches
  - Save all 4 as named files in `demo/` folder

- [ ] 17. Write demo script (`demo/SCRIPT.md`)
  - Step-by-step walkthrough (what to click, what to say)
  - Expected output for each test case
  - Talking points: fingerprinting concept, FAISS scale, variant detection

- [ ] 18. Record backup screenshots/video
  - Screen-record the full demo flow while on a good connection
  - Save as fallback in case of live network issues during presentation

- [ ] 19. Final end-to-end smoke test
  - Run all 4 demo videos on live Cloud Run URL
  - Verify thumbnails load, scores are reasonable, links work
  - Check mobile/laptop layout looks clean

---

## Key Files You Own

```
frontend/
├── src/
│   ├── pages/
│   │   ├── UploadPage.tsx
│   │   └── ResultsPage.tsx
│   ├── components/
│   │   ├── DropZone.tsx
│   │   ├── MatchCard.tsx
│   │   ├── ProgressTracker.tsx
│   │   └── ScoreBadge.tsx
│   ├── api/
│   │   └── client.ts
│   ├── types/
│   │   └── index.ts
│   └── utils/
│       └── format.ts
├── .env.example          ← VITE_API_URL=http://localhost:8000
├── .env.production       ← VITE_API_URL=https://your-cloudrun-url
├── vite.config.ts
└── tsconfig.json

demo/
├── test1_exact_copy.mp4
├── test2_trimmed.mp4
├── test3_edited.mp4
├── test4_unrelated.mp4
└── SCRIPT.md
```

---

## Coordination Points with Dev A

| When | What to sync |
|---|---|
| End of Day 1 | Confirm API response shapes match your TypeScript types |
| End of Day 2 | Dev A gives you a running local backend URL to test against |
| Day 3 morning | Agree on final `/matches` response format before wiring |
| Day 4 morning | Get Cloud Run URL, confirm CORS is enabled |
| Day 5 morning | Joint smoke test — both of you run the full demo flow together |