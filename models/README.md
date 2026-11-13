Run `python scripts/prepare_model.py` from BrainTumorAI/ to import the verified V2 inference bundle.

- `unet_v2_best.pth`: selected epoch 45 from the completed 50-epoch run.
- `model_metadata.json`: architecture, preprocessing, SHA-256, selected state and recorded metrics.
- `evaluation.json`: original per-case validation/test results for provenance.

The source export is named `unet_v1_demo.pth` but its protocol is `unet_v2_resumable_001`.
Weights and dataset files are intentionally excluded from Git. Training optimizer states remain in the original `runs_v2/`.
