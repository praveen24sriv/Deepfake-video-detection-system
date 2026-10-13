# ML Pipeline — DeepGuard Spatiotemporal Detector

Video-level deepfake detector trained on **FaceForensics++ C40** (heavy compression).

## Model
- **Spatial:** EfficientNet-B0 (ImageNet-pretrained) on each face crop
- **Temporal:** BiLSTM across 16 frames + attention pooling
- **Outputs:** video fake-probability + per-frame scores (suspicious timeline) + Grad-CAM heatmap
- **Input:** 16 evenly spaced frames → MTCNN face crop (square, 1.3× margin) → 224×224 RGB → ImageNet normalisation

## Results (FF++ C40 official test split, video level)

| Test set | AUC | Accuracy |
|---|---|---|
| All (real + 4 methods, 700 videos) | **0.934** | 85.4% |
| Real vs Deepfakes | 0.961 | 87.5% |
| Real vs Face2Face | 0.937 | 84.6% |
| Real vs FaceSwap | 0.937 | 85.0% |
| Real vs NeuralTextures | 0.901 | 79.6% |
| Real vs FaceShifter (**unseen** in training) | 0.745 | 63.9% |

Decision threshold chosen on the validation set (Youden's J). Known limitation: ~18% of real test videos are flagged as fake (25/140).

## Files

| File | Purpose |
|---|---|
| `deepguard.py` | Shared module: preprocessing, model, prediction, Grad-CAM. **Used by the backend.** |
| `DeepGuard_Training_v3.ipynb` | Clean training notebook (Colab, T4 GPU). Use this to re-run. |
| `DeepGuard_Training_run_log.ipynb` | The actual training run with all outputs (record of results). |
| `results.csv` | Test metrics table |
| `*.png` | Training curves, ROC curves, confusion matrix, per-method detection rate, Grad-CAM examples |

Input data comes from `preprocessing/FFpp_c40_Preprocessing.ipynb` (`manifest.csv` + `faces.tar`).

## Model weights
`deepguard_v1.pt` (~29 MB) is **not in Git** — shared via Google Drive. It contains the weights plus all settings
(frame count, crop size, margin, normalisation, thresholds).

## Backend usage
```python
from deepguard import DeepGuardPredictor

predictor = DeepGuardPredictor("models/deepguard_v1.pt")        # load once at startup

# crops: face crops in RGB, 224x224 (from MTCNN with 1.3x margin)
result = predictor.predict_crops(crops_rgb, timestamps, heatmap_path="outputs/x.jpg")
# -> verdict, fake_probability, real_probability, frame_scores,
#    suspicious_start, suspicious_end  (+ Grad-CAM image written to heatmap_path)

# or straight from a video file (does its own frame sampling + MTCNN):
result = predictor.predict_video("video.mp4", heatmap_path="outputs/x.jpg")
```
Requirements: `torch`, `torchvision`, `opencv-python`, `numpy`, `facenet-pytorch`.
