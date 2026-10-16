"""
DeepGuard PR #9 validation: training vs backend preprocessing parity + live API checks.

Usage (from any folder):
    python parity_check.py --backend <repo>/backend --model <path>/deepguard_v1.pt \
        --videos <labels.csv> [--faces <dir with training crops>] [--out results]

labels.csv columns: path, label (REAL / FAKE / NO_FACE), crops_dir (optional, relative to --faces)

What it checks for every video:
  1. Parity (in-process, the backend's own code): frame indices, face detected per frame,
     face boxes, all 32 crops, the 16 selected crops, the final model tensor (after JPEG +
     normalisation), sequence length and time order -- against the TRAINING preprocessing
     (functions copied from preprocessing/FFpp_c40_Preprocessing.ipynb).
  2. Optional: backend crops vs the actual training JPEGs saved by the preprocessing notebook.
  3. Live API: starts the real backend (uvicorn, normal startup path), POSTs each video to
     /api/v1/analysis, checks verdict / probabilities / NO_FACE / Grad-CAM image.
"""
import argparse
import json
import os
import subprocess
import sys
import time
from pathlib import Path

import cv2
import numpy as np
import pandas as pd
import torch

# ------------------------------------------------------------------ training reference
# Copied from preprocessing/FFpp_c40_Preprocessing.ipynb (cell 5), unchanged.
N_FRAMES, CROP_SIZE, MARGIN = 32, 224, 1.3
mtcnn = None


def ref_sample_frames(path, n=N_FRAMES):
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    if total <= 0:
        cap.release(); return [], []
    wanted = set(np.linspace(0, total - 1, num=min(n, total)).round().astype(int).tolist())
    frames, idxs, i = [], [], 0
    while True:
        ok = cap.grab()
        if not ok: break
        if i in wanted:
            ok, f = cap.retrieve()
            if ok:
                frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB)); idxs.append(i)
        i += 1
        if i > max(wanted): break
    cap.release()
    return frames, idxs


def ref_square_box(box, w, h, margin=MARGIN):
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    side = max(x2 - x1, y2 - y1) * margin
    side = min(side, w, h)
    x1 = int(np.clip(cx - side / 2, 0, w - side)); y1 = int(np.clip(cy - side / 2, 0, h - side))
    return x1, y1, x1 + int(side), y1 + int(side)


def ref_largest(boxes):
    if boxes is None or len(boxes) == 0: return None
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    return boxes[int(np.argmax(areas))]


def ref_crop_video(frames):
    """Training crop_video, plus the per-frame box used (for the parity report)."""
    h, w = frames[0].shape[:2]
    boxes, _ = mtcnn.detect(frames)
    crops, used, detected, last = [], [], [], None
    for f, b in zip(frames, boxes):
        b = ref_largest(b)
        detected.append(b is not None)
        if b is not None:
            last = b
        if last is None:
            continue
        x1, y1, x2, y2 = ref_square_box(last, w, h)
        used.append((x1, y1, x2, y2))
        crops.append(cv2.resize(f[y1:y2, x1:x2], (CROP_SIZE, CROP_SIZE), interpolation=cv2.INTER_AREA))
    if crops and len(crops) < len(frames):
        pad = len(frames) - len(crops)
        crops = [crops[0]] * pad + crops
        used = [used[0]] * pad + used
    return crops, used, detected


def ref_select(items, t=16):
    """Training evaluation frame choice: frame_indices(n, 16, train=False)."""
    n = len(items)
    idx = np.clip(np.round(np.linspace(0, n - 1, t)), 0, n - 1).astype(int)
    return [items[i] for i in idx]


# ------------------------------------------------------------------ helpers
def max_diff(a, b):
    return float(np.abs(np.asarray(a, np.float64) - np.asarray(b, np.float64)).max())


def backend_trace(analysis_service, detector, video_service, video):
    """Run the backend's analyze() in-process and record what each stage produced."""
    cap = {}
    cropper = getattr(analysis_service, "face_cropper", None)
    if cropper is None:          # old backend code (before the fix): no shared cropper to inspect
        class _Null: pass
        cropper = _Null(); cropper.mtcnn = _Null()
        cropper.mtcnn.detect = cropper.crop = None
    det_orig, crop_orig = cropper.mtcnn.detect, cropper.crop

    def det_spy(frames, *a, **k):
        boxes, probs = det_orig(frames, *a, **k)
        cap["boxes"] = boxes
        return boxes, probs

    def crop_spy(frames):
        crops, detected = crop_orig(frames)
        cap["crops32"], cap["detected"] = [c.copy() for c in crops], list(detected)
        return crops, detected

    if crop_orig is not None:
        cropper.mtcnn.detect, cropper.crop = det_spy, crop_spy
    pc_orig = None
    if detector.available:
        pc_orig = detector.predictor.predict_crops

        def pc_spy(crops, ts, heatmap_path=None):
            cap["model_crops"], cap["model_ts"] = [c.copy() for c in crops], list(ts)
            return pc_orig(crops, ts, heatmap_path=heatmap_path)

        detector.predictor.predict_crops = pc_spy
    try:
        resp = analysis_service.analyze(video, Path(video).name)
    finally:
        cropper.mtcnn.detect, cropper.crop = det_orig, crop_orig
        if pc_orig is not None:
            detector.predictor.predict_crops = pc_orig
    cap["indices"] = [s.index for s in video_service.inspect(video).samples]
    cap["response"] = resp
    return cap


def parity_row(name, video, bt, dg, faces_dir=None, crops_dir=None):
    frames, idxs = ref_sample_frames(video)
    r = dict(video=name)
    r["frame_indices_match"] = idxs == bt["indices"]
    r["n_sampled"] = len(idxs)
    if not frames:
        return r
    ref_crops, ref_boxes, ref_det = ref_crop_video(frames)
    r["faces_detected"] = int(sum(ref_det))
    r["detected_flags_match"] = (ref_det == bt["detected"]) if "detected" in bt else "n/a"
    # face boxes the backend's MTCNN returned vs the training MTCNN (largest face per frame)
    diffs = []
    for a, b in zip(mtcnn.detect(frames)[0], bt.get("boxes", [])):
        a, b = ref_largest(a), ref_largest(b)
        if (a is None) != (b is None):
            diffs.append(np.inf)
        elif a is not None:
            diffs.append(max_diff(a, b))
    r["box_max_diff_px"] = round(max(diffs), 3) if diffs else None
    if not ref_crops:
        r["both_no_face"] = not bt.get("crops32") and bt["response"].detection.verdict == "NO_FACE"
        return r
    if bt.get("crops32"):
        r["crops32_max_pixel_diff"] = max_diff(np.stack(ref_crops), np.stack(bt["crops32"]))
    ref16 = ref_select(ref_crops)
    if "model_crops" in bt:
        r["seq_len"] = len(bt["model_crops"])
        r["crop_shape"] = "x".join(map(str, bt["model_crops"][0].shape))
        be16 = [dg.resample(bt["model_crops"], 16) if len(bt["model_crops"]) != 16 else bt["model_crops"]][0]
        r["crops16_max_pixel_diff"] = max_diff(np.stack(ref16), np.stack(be16))
        r["crops16_mean_pixel_diff"] = round(float(np.abs(np.stack(ref16).astype(float) - np.stack(be16)).mean()), 3)
        t_ref = dg.to_tensor([dg.as_training_jpeg(c) for c in ref16])
        t_be = dg.to_tensor([dg.as_training_jpeg(c) for c in be16])
        r["tensor_shape"] = "x".join(map(str, t_be.shape))
        r["tensor_max_diff"] = float((t_ref - t_be).abs().max())
        r["time_order_ok"] = all(b > a for a, b in zip(bt["model_ts"], bt["model_ts"][1:]))
        ref_ts = ref_select([i / cv2.VideoCapture(str(video)).get(cv2.CAP_PROP_FPS) for i in idxs])
        be_ts = bt["model_ts"] if len(bt["model_ts"]) == 16 else dg.resample(bt["model_ts"], 16)
        r["timestamps_match"] = bool(np.allclose(ref_ts, be_ts))
    if faces_dir and crops_dir:
        folder = Path(faces_dir) / crops_dir
        saved = sorted(folder.glob("*.jpg"))
        if saved:
            train32 = [cv2.cvtColor(cv2.imread(str(p)), cv2.COLOR_BGR2RGB) for p in saved]
            be32 = [dg.as_training_jpeg(c) for c in bt["crops32"]]
            if len(train32) == len(be32):
                d = np.abs(np.stack(train32).astype(np.int16) - np.stack(be32).astype(np.int16))
                r["vs_training_jpegs_mean_diff"] = round(float(d.mean()), 3)
                r["vs_training_jpegs_max_diff"] = int(d.max())
            else:
                r["vs_training_jpegs_mean_diff"] = f"count {len(train32)} vs {len(be32)}"
    return r


# ------------------------------------------------------------------ API
def start_api(backend, model, port, log):
    env = dict(os.environ, DEMO_MODE="false", MODEL_PATH=str(model), MODEL_DEVICE="")
    proc = subprocess.Popen(
        [sys.executable, "-m", "uvicorn", "app.main:app", "--host", "127.0.0.1", "--port", str(port)],
        cwd=backend, env=env, stdout=open(log, "w"), stderr=subprocess.STDOUT)
    import requests
    for _ in range(240):
        if proc.poll() is not None:
            raise RuntimeError("backend exited during startup, see " + str(log))
        try:
            if requests.get(f"http://127.0.0.1:{port}/api/v1/health", timeout=2).ok:
                return proc
        except requests.RequestException:
            pass
        time.sleep(1)
    proc.kill()
    raise RuntimeError("backend did not start in 240 s, see " + str(log))


def api_row(port, name, video, label, out_dir):
    import requests
    base = f"http://127.0.0.1:{port}"
    t0 = time.time()
    with open(video, "rb") as fh:
        res = requests.post(f"{base}/api/v1/analysis", files={"file": (Path(video).name, fh, "video/mp4")},
                            timeout=600)
    r = dict(video=name, expected=label, http=res.status_code, api_seconds=round(time.time() - t0, 1))
    if not res.ok:
        r["error"] = res.text[:200]
        return r, None
    j = res.json()
    d, p, m = j["detection"], j["preprocessing"], j["model"]
    fake_p = d["confidence"] if d["verdict"] == "FAKE" else round(1 - d["confidence"], 4) if d["verdict"] == "REAL" else None
    r.update(verdict=d["verdict"], confidence=d["confidence"], fake_prob=fake_p, correct=d["verdict"] == label,
             faces_detected=p["faces_detected"], frames_without_face=p["frames_without_face"],
             model_frames_used=p["model_frames_used"], demo_mode=m["demo_mode"],
             suspicious=f'{d["timeline"]["suspicious_start"]}-{d["timeline"]["suspicious_end"]}')
    heat = None
    url = j["meta"]["heatmap_url"]
    if url:
        hr = requests.get(base + url, timeout=30)
        img = cv2.imdecode(np.frombuffer(hr.content, np.uint8), cv2.IMREAD_COLOR) if hr.ok else None
        r["gradcam"] = "ok" if img is not None and img.shape[:2] == (224, 224) else "bad"
        if img is not None:
            heat = img
            cv2.imwrite(str(out_dir / f"gradcam_{name}.jpg"), img)
    else:
        r["gradcam"] = "none"
    return r, heat


# ------------------------------------------------------------------ main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--backend", required=True)
    ap.add_argument("--model", required=True)
    ap.add_argument("--videos", required=True)
    ap.add_argument("--faces", default=None)
    ap.add_argument("--out", default="results")
    ap.add_argument("--port", type=int, default=8765)
    a = ap.parse_args()

    backend, out = Path(a.backend).resolve(), Path(a.out).resolve()
    out.mkdir(parents=True, exist_ok=True)
    vids = pd.read_csv(a.videos, dtype=str).fillna("")

    # backend code, in-process (same modules uvicorn will load)
    os.environ.update(DEMO_MODE="false", MODEL_PATH=str(Path(a.model).resolve()), MODEL_DEVICE="")
    cwd = os.getcwd(); os.chdir(backend); sys.path.insert(0, str(backend))
    from app.services.analysis_service import analysis_service
    from app.services.detector import detector
    from app.services.video_service import video_service
    from app.services import deepguard as dg
    from app.config import settings
    settings.output_dir.mkdir(parents=True, exist_ok=True)
    analysis_service.initialize()
    os.chdir(cwd)

    global mtcnn
    from facenet_pytorch import MTCNN
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    mtcnn = MTCNN(keep_all=True, device=dev, select_largest=True, post_process=False)   # as in training

    cfg = detector.predictor.cfg
    print(f"model: {cfg['version']} {cfg['run']} | test AUC {cfg['test_auc']} | threshold {cfg['threshold']} "
          f"| device {detector.predictor.device}")
    print(f"normalisation: checkpoint mean/std {tuple(cfg['mean'])}/{tuple(cfg['std'])} "
          f"| deepguard.py {dg.MEAN}/{dg.STD} | match: {tuple(cfg['mean']) == dg.MEAN and tuple(cfg['std']) == dg.STD}")

    def vname(v):
        return getattr(v, "video", "") or Path(v.path).stem

    def training_score(crops_dir):
        """Score from the saved training crops, as the test set was evaluated (16 evenly spaced)."""
        if not (a.faces and crops_dir):
            return None
        saved = sorted((Path(a.faces) / crops_dir).glob("*.jpg"))
        if not saved:
            return None
        crops = ref_select([cv2.cvtColor(cv2.imread(str(q)), cv2.COLOR_BGR2RGB) for q in saved])
        pr = detector.predictor
        with torch.no_grad():
            logit, _ = pr.model(dg.to_tensor(crops).unsqueeze(0).to(pr.device))
        return round(float(torch.sigmoid(logit - dg._logit(pr.threshold))[0]), 4)

    parity, inproc = [], {}
    for v in vids.itertuples():
        name = vname(v)
        bt = backend_trace(analysis_service, detector, video_service, v.path)
        resp = bt["response"]
        heat = None
        if resp.meta.heatmap_url:
            heat = cv2.imread(str(settings.output_dir / Path(resp.meta.heatmap_url).name))
        inproc[name] = (resp, heat, training_score(getattr(v, "crops_dir", "") or None))
        parity.append(parity_row(name, v.path, bt, dg, a.faces, getattr(v, "crops_dir", "") or None))
        print("parity", name, "done")
    parity = pd.DataFrame(parity)
    parity.to_csv(out / "parity.csv", index=False)

    proc = start_api(backend, Path(a.model).resolve(), a.port, out / "backend.log")
    try:
        rows = []
        for v in vids.itertuples():
            name = vname(v)
            r, heat = api_row(a.port, name, v.path, v.label, out)
            resp, ip_heat, tscore = inproc[name]
            r["inprocess_verdict"] = resp.detection.verdict
            r["inprocess_confidence"] = resp.detection.confidence
            if tscore is not None:
                r["training_crops_fake_prob"] = tscore
            if heat is not None and ip_heat is not None:
                r["gradcam_vs_inprocess_mean_diff"] = round(float(np.abs(heat.astype(float) - ip_heat).mean()), 2)
            rows.append(r)
            print("api", name, r.get("verdict"), r.get("confidence"))
    finally:
        proc.terminate()
    api = pd.DataFrame(rows)
    api.to_csv(out / "api_results.csv", index=False)

    pd.set_option("display.width", 250); pd.set_option("display.max_columns", 30)
    print("\n=== PARITY: training preprocessing vs backend ===")
    print(parity.to_string(index=False))
    print("\n=== LIVE API ===")
    print(api.to_string(index=False))
    with open(out / "summary.json", "w") as fh:
        json.dump(dict(model=cfg["version"], test_auc=cfg["test_auc"], threshold=cfg["threshold"],
                       n_videos=len(api), api_verdicts_correct=int(api.get("correct", pd.Series()).sum()),
                       torch=torch.__version__), fh, indent=1)
    print("\nsaved:", sorted(p.name for p in out.iterdir()))


if __name__ == "__main__":
    main()
