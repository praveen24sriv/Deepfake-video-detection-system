# DeepGuard AI — DeepFake Video Detection System using Spatiotemporal Neural Networks

A Major Project (VTU, Dept. of Electronics and Communication Engineering, Nitte Meenakshi Institute of Technology) building a video-level deepfake detector that evaluates **both spatial artifacts within frames and temporal inconsistencies across frames**, instead of relying on single-frame analysis like most conventional detectors.

> **Project status: Phase-2 (Semester VII) — Design & Finalization stage.**
> This repository currently contains a validated data-preprocessing pipeline and a **UI mockup only**. There is no trained model and no backend yet — see [Project Status](#project-status) below for exactly what is and isn't implemented.

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
| Frontend dashboard | ✅ UI implemented — **mock only**, not wired to a backend |
| Detection model (spatiotemporal network) | ❌ Not yet implemented — architecture being finalized in Phase-2 |
| Backend / inference API | ❌ Not yet implemented — framework choice (Node/Express/MongoDB vs. Flask/FastAPI) pending finalization |
| Database | ❌ Not yet implemented |
| Frontend–backend integration | ❌ Not started |
| Deployment | ❌ Not started |

Phase-2 is scoped to **architecture, detailed design, technology stack, and dataset finalization only** — no training or integration work is expected to land in this repo until Phase-3. Note also that the project's target dataset has since been changed to **FaceForensics++ (FF++), C40 (heavy compression) variant**, superseding the Celeb-DF v2 dataset the current preprocessing notebook was built against; that pipeline will need to be re-applied/re-validated against FF++ C40 in the next phase.

## Repository Structure

```
Deepfake-video-detection-system/
├── preprocessing/
│   ├── Celeb_DF_Preprocessing_ipynb.ipynb   # Data cleaning/normalization pipeline (Celeb-DF v2)
│   └── assets/                              # Output charts/plots from the pipeline run
├── frontend/
│   └── vite-project/                        # React + Vite dashboard (mock UI, no backend calls)
├── backend/        # placeholder — not yet implemented
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

### 2. Frontend Dashboard (`frontend/vite-project/`)
A React 18 + Vite single-page app implementing the intended user flow: **video upload → analysis progress → classification result → charts**. This is a **UI mockup**:
- File upload accepts a video and simulates an upload progress bar.
- "Analyze Video" triggers a fixed `setTimeout` delay and then renders a **hardcoded** result object (verdict, confidence score, flagged artifacts, suspicious timeline segment) — it does not call any model or API.
- The "System Analytics" dashboard renders Chart.js bar/donut charts against **static, illustrative data**, not real detection history.
- No `fetch`/`axios` calls exist anywhere in the app — there is nothing for a backend to plug into yet beyond this UI shell.

## Getting Started

### Data Preprocessing Pipeline

```bash
cd preprocessing
pip install -r requirements.txt   # add this file — see Roadmap
jupyter notebook Celeb_DF_Preprocessing_ipynb.ipynb
```

*(No `requirements.txt` currently exists in this folder — dependencies used include standard data-science/CV libraries such as OpenCV, NumPy, and Matplotlib based on the notebook's operations; pin exact versions before Phase-3.)*

### Frontend (Mock UI)

```bash
cd frontend/vite-project
npm install
npm run dev
```

Runs the dashboard at `http://localhost:5173` by default. Built with:
- React 18 + Vite 5
- Chart.js (via `chart.js/auto`) for the analytics charts

No environment variables or API keys are required — the app is fully self-contained and has no external dependencies at runtime.

## Roadmap

Planned for the next implementation phase (Phase-3), once architecture/design finalization (Phase-2) is complete:
- [ ] Re-run and validate the preprocessing pipeline against **FaceForensics++ C40** (replacing Celeb-DF v2)
- [ ] Finalize and implement the spatiotemporal detection model architecture
- [ ] Finalize the backend framework and implement the inference API
- [ ] Add a database layer for storing detection history/reports
- [ ] Connect the existing frontend to the real backend (replace mock `setTimeout` logic and static chart data)
- [ ] Add automated tests for preprocessing and backend modules
- [ ] Deployment setup

## Tech Stack

| Layer | Technology | Status |
|---|---|---|
| Language | Python | In use (preprocessing) |
| Preprocessing | OpenCV, NumPy | In use |
| Frontend | React 18, Vite 5, Chart.js | In use (mock only) |
| Deep Learning Framework | PyTorch / TensorFlow | To be finalized |
| Backend Framework | Node.js/Express/MongoDB *or* Flask/FastAPI | To be finalized |
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
