# DeepGuard AI — DeepFake Video Detection System using Spatiotemporal Neural Networks

A Major Project (VTU, Dept. of Electronics and Communication Engineering, Nitte Meenakshi Institute of Technology) building a video-level deepfake detector that evaluates **both spatial artifacts within frames and temporal inconsistencies across frames**, instead of relying on single-frame analysis like most conventional detectors.

> **Project status: Phase-2 (Semester VII) — Design & Finalization stage.**
> This repository currently contains a validated data-preprocessing pipeline, a **FastAPI backend** (video validation, frame sampling, face detection and quality filtering), and a **React frontend** connected to it. There is **no trained model yet**, so the backend returns `MODEL_UNAVAILABLE` instead of a REAL/FAKE verdict — see [Project Status](#project-status) below for exactly what is and isn't implemented.

---

## Table of Contents
- [Motivation](#motivation)
- [Project Status](#project-status)
- [Repository Structure](#repository-structure)
- [What's Implemented](#whats-implemented)
- [Getting Started](#getting-started)
- [Roadmap](#roadmap)
- [Tech Stack](#tech-stack)
- [Team](#team)

---

## Motivation

GAN-, VAE-, and diffusion-based deepfakes are increasingly hard to catch with detectors that only look at static, single-frame spatial artifacts. These approaches degrade sharply once video is compressed for social media, and they miss manipulation cues that only show up across a sequence of frames (irregular blinking, unnatural motion, flickering face boundaries). This project's goal is a **spatiotemporal** detector that jointly models intra-frame spatial textures and inter-frame temporal patterns, with an emphasis on staying accurate under real-world compression.

## Project Status

| Component | Status |
|---|---|
| Data preprocessing pipeline | ✅ Implemented and validated (Phase-1, Celeb-DF v2) |
| Frontend | ✅ Home and Analyze Video pages, wired to the FastAPI backend |
| Detection model (spatiotemporal network) | ❌ Not yet implemented — architecture being finalized in Phase-2 |
| Backend / inference API | ⚠️ FastAPI preprocessing API implemented; returns `MODEL_UNAVAILABLE` until a trained model is integrated |
| Database | ❌ Not yet implemented |
| Frontend–backend integration | ✅ Upload → `POST /api/v1/analysis` → real results |
| Deployment | ❌ Not started |

Phase-2 is scoped to **architecture, detailed design, technology stack, and dataset finalization only** — no training or integration work is expected to land in this repo until Phase-3. Note also that the project's target dataset has since been changed to **FaceForensics++ (FF++), C40 (heavy compression) variant**, superseding the Celeb-DF v2 dataset the current preprocessing notebook was built against; that pipeline will need to be re-applied/re-validated against FF++ C40 in the next phase.

## Repository Structure

```
Deepfake-video-detection-system/
├── preprocessing/
│   ├── Celeb_DF_Preprocessing_ipynb.ipynb   # Data cleaning/normalization pipeline (Celeb-DF v2)
│   └── assets/                              # Output charts/plots from the pipeline run
├── frontend/
│   └── vite-project/                        # React + Vite app (Home, Analyze Video) calling the FastAPI backend
├── backend/                                 # FastAPI preprocessing API (no trained model yet)
├── ml_pipeline/     # placeholder — not yet implemented
└── docs/            # placeholder — architecture/design docs to be added in Phase-2
```

## What's Implemented

### 1. Data Preprocessing Pipeline (`preprocessing/`)
A Jupyter notebook that takes the Celeb-DF v2 image dataset and produces a clean, model-ready dataset:
- **Frame inventory** — loads and catalogs the full 90,824-image dataset (40,288 real / 40,536 fake).
- **Blur filtering** — Laplacian-variance thresholding (threshold = 80) to discard low-quality/motion-blurred frames.
- **Resolution & corruption checks** — minimum resolution enforcement and file-integrity verification.
- **Normalization** — resize to 224×224 with ImageNet mean/std normalization.
- **Dataset split** — 80/10/10 train/validation/test split.

Output charts (class balance, before/after cleaning counts, split proportions) are saved in `preprocessing/assets/`.

> ⚠️ This notebook was built and validated against **Celeb-DF v2**. The project has since moved to **FaceForensics++ C40** as the target dataset — this pipeline is not yet re-validated against FF++ C40's different compression characteristics and manipulation-category structure.

### 2. Frontend (`frontend/vite-project/`)
A React 18 + Vite app with two pages, **Home** and **Analyze Video**, using a small hash-based router (no extra dependencies):
- Upload an MP4, AVI or MOV video (drag-and-drop or Browse Files) with client-side type, empty-file and size (500 MB by default) checks and a video preview.
- "Analyze Video" sends the file to `POST /api/v1/analysis` and renders **only what the API returns**: verdict (when available), confidence (only for REAL/FAKE), frames sampled, face and blur statistics, processing time and the explanation image.
- `MODEL_UNAVAILABLE` is shown as a neutral notice — the video is never labelled real or fake without a model verdict.
- The explanation image is labelled a **development visualization** (an edge-based overlay), not Grad-CAM.
- A small connection indicator uses `GET /api/v1/health`; network errors, 400/413/422/500 responses and malformed responses are handled with clear messages and a retry option.
- No mock data, fake progress or hardcoded results.

### 3. Backend (`backend/`)
A FastAPI service that validates the upload, samples about 10 frames, detects and crops the largest face (OpenCV Haar cascade), filters blurry crops and resizes to 224 × 224. Endpoints: `GET /api/v1/health`, `POST /api/v1/analysis` (multipart field `file`) and `GET /api/v1/analytics` (in-memory counters). With `DEMO_MODE=true` (default) it returns `MODEL_UNAVAILABLE`; with `DEMO_MODE=false` it returns an error because the trained model is not integrated yet.

## Getting Started

### Data Preprocessing Pipeline

```bash
cd preprocessing
pip install -r requirements.txt   # add this file — see Roadmap
jupyter notebook Celeb_DF_Preprocessing_ipynb.ipynb
```

*(No `requirements.txt` currently exists in this folder — dependencies used include standard data-science/CV libraries such as OpenCV, NumPy, and Matplotlib based on the notebook's operations; pin exact versions before Phase-3.)*

### Backend

Requires Python 3.10+.

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate     Mac/Linux: source .venv/bin/activate
pip install -r requirements.txt
python -m uvicorn app.main:app --port 8000
```

Check it at `http://127.0.0.1:8000/api/v1/health` (interactive docs at `/docs`). An optional `.env` can be created from `.env.example`.

### Frontend

Requires Node.js 18+. Start the backend first, in a separate terminal.

```bash
cd frontend/vite-project
npm install
npm run dev
```

Open `http://localhost:5173`. The Vite dev server proxies `/api` and `/outputs` to `http://127.0.0.1:8000` (override with `VITE_PROXY_TARGET`), so no CORS setup is needed. Optional settings: `VITE_API_BASE_URL` (call a backend on another origin directly) and `VITE_MAX_UPLOAD_MB` (client-side size check, default 500).

## Roadmap

Planned for the next implementation phase (Phase-3), once architecture/design finalization (Phase-2) is complete:
- [ ] Re-run and validate the preprocessing pipeline against **FaceForensics++ C40** (replacing Celeb-DF v2)
- [ ] Finalize and implement the spatiotemporal detection model architecture
- [ ] Integrate the trained model into the inference API (preprocessing API already implemented with FastAPI)
- [ ] Add a database layer for storing detection history/reports
- [ ] Replace the development visualization with real Grad-CAM once a model exists
- [ ] Add automated tests for preprocessing and backend modules
- [ ] Deployment setup

## Tech Stack

| Layer | Technology | Status |
|---|---|---|
| Language | Python | In use (preprocessing) |
| Preprocessing | OpenCV, NumPy | In use |
| Frontend | React 18, Vite 5 | In use |
| Deep Learning Framework | PyTorch / TensorFlow | To be finalized |
| Backend Framework | FastAPI | In use (preprocessing API) |
| Dataset | FaceForensics++ (FF++) C40 | Finalized (replaces Celeb-DF v2) |

## Team

| Name | USN |
|---|---|
| Aryan Rajput | 1NT23EC023 |
| Ojaswi | 1NT23EC097 |
| Praveen Raj Srivastav | 1NT23EC110 |

**Guide:** Ms. Ayesha Siddiqua, Assistant Professor, Dept. of ECE, NMIT
**Department:** Electronics and Communication Engineering, Nitte Meenakshi Institute of Technology, Bengaluru

---

*This README reflects the actual state of the code in this repository as of Phase-2. Sections marked "not yet implemented" are intentionally left undetailed rather than describing planned functionality as if it already exists.*
