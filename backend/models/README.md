# Model weights

Put the trained model here:

```
backend/models/deepguard_v1.pt
```

- Download `deepguard_v1.pt` (~29 MB) from the team's Google Drive (shared by Ojaswi).
- It is NOT committed to git (`*.pt` is in `.gitignore`).
- Trained with `ml_pipeline/DeepGuard_Training_v3.ipynb`: EfficientNet-B0 + BiLSTM on FaceForensics++ C40, test AUC 0.934.
- To run the backend without the model, set `DEMO_MODE=true` in `backend/.env`.
