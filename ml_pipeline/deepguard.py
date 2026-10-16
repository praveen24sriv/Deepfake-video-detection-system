"""
DeepGuard — shared preprocessing + model + inference + Grad-CAM.

ONE file used by BOTH the training notebook and the backend, so the model always
sees identical inputs (no training/serving mismatch).

Pipeline (identical to preprocessing/FFpp_c40_Preprocessing.ipynb):
    video -> N evenly spaced frames (RGB) -> MTCNN face box (largest face,
    reuse last box when a frame has no detection) -> square crop x1.3 margin
    -> 224x224 -> /255 -> ImageNet mean/std -> CNN (EfficientNet-B0) -> LSTM

Backend usage (app/services/detector.py):
    from deepguard import DeepGuardPredictor
    predictor = DeepGuardPredictor("models/deepguard_v1.pt")       # once, at startup
    result = predictor.predict_video(video_path, heatmap_path=out_jpg)
    # result keys: verdict, fake_probability, real_probability, frame_scores,
    #              timestamps, suspicious_start, suspicious_end, stats

Requirements: torch, torchvision, opencv-python, numpy, facenet-pytorch
"""
from __future__ import annotations

import cv2
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F
import torchvision

# ---------------------------------------------------------------- settings
N_FRAMES = 16          # frames the model sees
N_EXTRACT = 32         # frames sampled and cropped per video (training preprocessing)
CROP_SIZE = 224
MARGIN = 1.3
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)


# ---------------------------------------------------------------- preprocessing
def sample_frames(path, n: int = N_FRAMES):
    """Return (frames_rgb, timestamps_sec, fps) for n evenly spaced frames, in order."""
    cap = cv2.VideoCapture(str(path))
    total = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    if total <= 0:
        cap.release()
        return [], [], fps
    wanted = sorted(set(np.linspace(0, total - 1, num=min(n, total)).round().astype(int).tolist()))
    wanted_set, last = set(wanted), wanted[-1]
    frames, idxs, i = [], [], 0
    while i <= last:
        if not cap.grab():
            break
        if i in wanted_set:
            ok, f = cap.retrieve()
            if ok:
                frames.append(cv2.cvtColor(f, cv2.COLOR_BGR2RGB))
                idxs.append(i)
        i += 1
    cap.release()
    return frames, [k / fps for k in idxs], fps


def square_box(box, w, h, margin: float = MARGIN):
    """Square box around the face centre, side = longest face side x margin, clamped to the frame."""
    x1, y1, x2, y2 = box
    cx, cy = (x1 + x2) / 2, (y1 + y2) / 2
    side = max(x2 - x1, y2 - y1) * margin
    side = min(side, w, h)
    x1 = int(np.clip(cx - side / 2, 0, w - side))
    y1 = int(np.clip(cy - side / 2, 0, h - side))
    return x1, y1, x1 + int(side), y1 + int(side)


def largest(boxes):
    if boxes is None or len(boxes) == 0:
        return None
    areas = (boxes[:, 2] - boxes[:, 0]) * (boxes[:, 3] - boxes[:, 1])
    return boxes[int(np.argmax(areas))]


def blur_score(rgb) -> float:
    return float(cv2.Laplacian(cv2.cvtColor(rgb, cv2.COLOR_RGB2GRAY), cv2.CV_64F).var())


class FaceCropper:
    """MTCNN face cropping with exactly the rules used to build the training set."""

    def __init__(self, device=None, mtcnn=None):
        if mtcnn is None:
            from facenet_pytorch import MTCNN
            device = device or ("cuda" if torch.cuda.is_available() else "cpu")
            mtcnn = MTCNN(keep_all=True, device=device, select_largest=True, post_process=False)
        self.mtcnn = mtcnn

    def crop(self, frames):
        """Return (crops_rgb, detected_flags). Empty crops list = no face in the whole clip."""
        if not frames:
            return [], []
        h, w = frames[0].shape[:2]
        boxes, _ = self.mtcnn.detect(frames)
        crops, detected, last = [], [], None
        for f, b in zip(frames, boxes):
            b = largest(b)
            detected.append(b is not None)
            if b is not None:
                last = b
            if last is None:
                crops.append(None)            # before the first detection -> back-filled below
                continue
            x1, y1, x2, y2 = square_box(last, w, h)
            crops.append(cv2.resize(f[y1:y2, x1:x2], (CROP_SIZE, CROP_SIZE), interpolation=cv2.INTER_AREA))
        first = next((c for c in crops if c is not None), None)
        if first is None:
            return [], detected
        return [first if c is None else c for c in crops], detected


def as_training_jpeg(crop_rgb: np.ndarray, quality: int = 95) -> np.ndarray:
    """Training crops were saved as JPEG (quality 95) and read back; apply the same round trip
    so the model sees inputs exactly like the ones it was trained and evaluated on."""
    ok, buf = cv2.imencode(".jpg", cv2.cvtColor(crop_rgb, cv2.COLOR_RGB2BGR), [cv2.IMWRITE_JPEG_QUALITY, quality])
    return cv2.cvtColor(cv2.imdecode(buf, cv2.IMREAD_COLOR), cv2.COLOR_BGR2RGB) if ok else crop_rgb


def to_tensor(crops) -> torch.Tensor:
    """List of HxWx3 uint8 RGB crops -> (T, 3, H, W) float tensor, ImageNet-normalised."""
    x = torch.from_numpy(np.stack(crops)).permute(0, 3, 1, 2).float().div_(255.0)
    mean = torch.tensor(MEAN).view(1, 3, 1, 1)
    std = torch.tensor(STD).view(1, 3, 1, 1)
    return (x - mean) / std


def resample(items, n):
    """Pick n evenly spaced items (repeats allowed when the list is shorter than n)."""
    idx = np.linspace(0, len(items) - 1, n).round().astype(int)
    return [items[i] for i in idx]


# ---------------------------------------------------------------- model
class DeepGuardNet(nn.Module):
    """EfficientNet-B0 per frame (spatial) + BiLSTM across frames (temporal).

    temporal='lstm' -> main model;  temporal='mean' -> CNN-only baseline (plain average of frames).
    Returns (video_logit [B], frame_logits [B, T]).
    """

    def __init__(self, temporal: str = "lstm", hidden: int = 256, pretrained: bool = True, dropout: float = 0.3):
        super().__init__()
        weights = torchvision.models.EfficientNet_B0_Weights.IMAGENET1K_V1 if pretrained else None
        base = torchvision.models.efficientnet_b0(weights=weights)
        self.features = base.features                    # (N, 1280, 7, 7) for 224x224 input
        self.pool = nn.AdaptiveAvgPool2d(1)
        self.temporal = temporal
        feat_dim = 1280
        if temporal == "lstm":
            self.rnn = nn.LSTM(feat_dim, hidden, batch_first=True, bidirectional=True)
            out_dim = 2 * hidden
        elif temporal == "mean":
            self.rnn = None
            out_dim = feat_dim
        else:
            raise ValueError("temporal must be 'lstm' or 'mean'")
        self.drop = nn.Dropout(dropout)
        self.frame_head = nn.Linear(out_dim, 1)
        self.attn = nn.Linear(out_dim, 1)
        self.video_head = nn.Linear(out_dim, 1)

    def forward(self, x):                                # x: (B, T, 3, H, W)
        b, t = x.shape[:2]
        f = self.features(x.flatten(0, 1))
        f = self.pool(f).flatten(1).view(b, t, -1)       # (B, T, 1280)
        h = self.rnn(f)[0] if self.rnn is not None else f
        h = self.drop(h)
        frame_logits = self.frame_head(h).squeeze(-1)    # (B, T)
        if self.rnn is not None:
            w = torch.softmax(self.attn(h).squeeze(-1), dim=1)
            pooled = (w.unsqueeze(-1) * h).sum(1)        # attention pooling over time
        else:
            pooled = h.mean(1)                           # baseline: plain average
        video_logit = self.video_head(pooled).squeeze(-1)
        return video_logit, frame_logits


# ---------------------------------------------------------------- Grad-CAM
def gradcam(model: DeepGuardNet, clip: torch.Tensor, frame_idx: int) -> np.ndarray:
    """Grad-CAM for one frame of a clip. clip: (T,3,H,W) normalised, on the model's device.
    Returns an HxW map in [0, 1] (where the model looked when scoring this frame as fake)."""
    model.eval()
    store = {}

    def hook(_m, _i, out):
        out.retain_grad()
        store["a"] = out

    handle = model.features.register_forward_hook(hook)
    # cuDNN's LSTM only runs backward in training mode. A 1-layer LSTM has no dropout, so switching
    # just the LSTM to train mode gives identical outputs; CNN batch-norm and dropout stay in eval mode.
    if model.rnn is not None:
        model.rnn.train()
    try:
        with torch.enable_grad():
            _, frame_logits = model(clip.unsqueeze(0).float())
            model.zero_grad(set_to_none=True)
            frame_logits[0, frame_idx].backward()
        act = store["a"][frame_idx].detach()             # (1280, 7, 7)
        grad = store["a"].grad[frame_idx].detach()
    finally:
        handle.remove()
        model.eval()
    weights = grad.mean(dim=(1, 2), keepdim=True)
    cam = F.relu((weights * act).sum(0))
    cam = cam / (cam.max() + 1e-8)
    cam = F.interpolate(cam[None, None], size=tuple(clip.shape[-2:]), mode="bilinear", align_corners=False)[0, 0]
    return cam.cpu().numpy()


def overlay_heatmap(crop_rgb: np.ndarray, cam: np.ndarray, alpha: float = 0.4) -> np.ndarray:
    heat = cv2.applyColorMap((cam * 255).astype(np.uint8), cv2.COLORMAP_JET)
    heat = cv2.cvtColor(heat, cv2.COLOR_BGR2RGB)
    return np.clip(crop_rgb * (1 - alpha) + heat * alpha, 0, 255).astype(np.uint8)


# ---------------------------------------------------------------- timeline
def suspicious_segment(frame_probs, timestamps, threshold):
    """Longest run of consecutive frames scored >= threshold -> (start_sec, end_sec) or (None, None)."""
    best, cur_start, best_len = None, None, 0
    for i, p in enumerate(frame_probs):
        if p >= threshold:
            cur_start = i if cur_start is None else cur_start
            if i - cur_start + 1 > best_len:
                best_len, best = i - cur_start + 1, (cur_start, i)
        else:
            cur_start = None
    if best is None:
        return None, None
    return float(timestamps[best[0]]), float(timestamps[best[1]])


# ---------------------------------------------------------------- inference
def _logit(p: float) -> float:
    p = min(max(float(p), 1e-6), 1 - 1e-6)
    return float(np.log(p / (1 - p)))


class DeepGuardPredictor:
    def __init__(self, model_path, device=None, cropper: FaceCropper | None = None):
        self.device = torch.device(device or ("cuda" if torch.cuda.is_available() else "cpu"))
        ckpt = torch.load(model_path, map_location=self.device, weights_only=False)
        self.cfg = ckpt["config"]
        self.model = DeepGuardNet(temporal=self.cfg["temporal"], hidden=self.cfg["hidden"], pretrained=False)
        self.model.load_state_dict(ckpt["state_dict"])
        self.model.to(self.device).eval()
        self.n_frames = int(self.cfg["n_frames"])
        self.threshold = float(self.cfg["threshold"])
        self.frame_threshold = float(self.cfg.get("frame_threshold", self.threshold))
        self._cropper = cropper            # MTCNN is only loaded if predict_video() is used

    @property
    def cropper(self) -> FaceCropper:
        if self._cropper is None:
            self._cropper = FaceCropper(self.device)
        return self._cropper

    def predict_video(self, path, heatmap_path=None) -> dict:
        # Same as training: 32 frames sampled and cropped, then 16 of them (rounded linspace).
        frames, timestamps, _ = sample_frames(path, N_EXTRACT)
        crops, detected = self.cropper.crop(frames)
        if len(crops) > self.n_frames:
            keep = np.linspace(0, len(crops) - 1, self.n_frames).round().astype(int)
            crops = [crops[i] for i in keep]
            timestamps = [timestamps[i] for i in keep]
        stats = dict(
            frames_sampled=len(frames),
            faces_detected=int(sum(detected)),
            frames_without_face=len(frames) - int(sum(detected)),
            blur_scores=[blur_score(c) for c in crops],
        )
        if not crops:
            return dict(verdict="NO_FACE", fake_probability=0.0, real_probability=0.0, frame_scores=[],
                        timestamps=timestamps, suspicious_start=None, suspicious_end=None, stats=stats)
        return {**self.predict_crops(crops, timestamps, heatmap_path), "stats": stats}

    def predict_crops(self, crops, timestamps, heatmap_path=None) -> dict:
        """Crops must come from FaceCropper (RGB, 224x224). Resampled to the trained frame count."""
        if len(crops) != self.n_frames:
            crops, timestamps = resample(crops, self.n_frames), resample(list(timestamps), self.n_frames)
        crops = [as_training_jpeg(c) for c in crops]
        clip = to_tensor(crops).to(self.device)
        with torch.no_grad():
            video_logit, frame_logits = self.model(clip.unsqueeze(0))
        raw_p_fake = float(torch.sigmoid(video_logit)[0])
        # Re-centre scores so the validation-chosen threshold maps to exactly 0.5. Verdicts are unchanged;
        # the reported probability/confidence just becomes meaningful (raw scores cluster near 1).
        p_fake = float(torch.sigmoid(video_logit - _logit(self.threshold))[0])
        frame_probs = torch.sigmoid(frame_logits - _logit(self.frame_threshold))[0].cpu().numpy()
        start, end = suspicious_segment(frame_probs, timestamps, 0.5)
        if p_fake < 0.5:
            start = end = None
        if heatmap_path is not None:
            k = int(frame_probs.argmax())
            cam = gradcam(self.model, clip, k)
            cv2.imwrite(str(heatmap_path), cv2.cvtColor(overlay_heatmap(crops[k], cam), cv2.COLOR_RGB2BGR))
        return dict(
            verdict="FAKE" if p_fake >= 0.5 else "REAL",
            fake_probability=p_fake,
            real_probability=1.0 - p_fake,
            raw_fake_probability=raw_p_fake,
            frame_scores=[float(p) for p in frame_probs],
            timestamps=[float(t) for t in timestamps],
            suspicious_start=start,
            suspicious_end=end,
        )
