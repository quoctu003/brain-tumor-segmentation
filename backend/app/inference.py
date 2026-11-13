import hashlib
import json
import threading
import time
from pathlib import Path

import nibabel as nib
import numpy as np
import torch
from monai.inferers import sliding_window_inference
from monai.networks.nets import UNet
from scipy.ndimage import label

from .config import Settings
from .imaging import preprocess, region_volumes


class ModelService:
    def __init__(self, config: Settings):
        self.config = config
        self.lock = threading.Lock()
        self.model = None
        self.metadata = None
        self.error = None
        self.device = torch.device("cuda" if config.device == "auto" and torch.cuda.is_available()
                                   else "cpu" if config.device == "auto" else config.device)

    def load(self):
        try:
            metadata = json.loads(self.config.metadata_path.read_text("utf-8"))
            with self.config.model_path.open("rb") as handle:
                digest = hashlib.file_digest(handle, "sha256").hexdigest()
            if digest != metadata.get("weights_sha256"):
                raise ValueError("Checkpoint SHA-256 does not match model_metadata.json")
            package = torch.load(self.config.model_path, map_location="cpu", weights_only=True)
            if package["metadata"]["best_state_id"] != metadata["best_state_id"]:
                raise ValueError("Checkpoint state does not match metadata")
            if package["protocol"] != metadata["protocol"]:
                raise ValueError("Checkpoint protocol does not match metadata")
            prep = metadata["preprocessing"]
            if (prep["modalities"] != ["t1n", "t1c", "t2w", "t2f"] or prep["resample"] or prep["crop"]
                    or prep["clip_percentiles"] != [0.5, 99.5]
                    or prep["foreground"] != "intensity > 0"
                    or prep["normalize"] != "per-modality foreground z-score"):
                raise ValueError("Unsupported preprocessing contract")
            if metadata["protocol"]["total_epochs"] != 50:
                raise ValueError("BrainTumor AI expects the V2 50-epoch experiment")
            expected_architecture = {"spatial_dims": 3, "in_channels": 4, "out_channels": 4,
                                     **metadata["protocol"]["architecture"]}
            if metadata["architecture"] != expected_architecture:
                raise ValueError("Model architecture does not match the checkpoint protocol")
            if metadata["labels"] != {"0": "background", "1": "NCR", "2": "ED", "3": "ET"}:
                raise ValueError("Unsupported segmentation label contract")
            architecture = dict(metadata["architecture"])
            architecture["channels"] = tuple(architecture["channels"])
            architecture["strides"] = tuple(architecture["strides"])
            model = UNet(**architecture)
            model.load_state_dict(package["model_state"], strict=True)
            self.model = model.to(self.device).eval()
            self.metadata = metadata
            self.error = None
        except Exception as exc:
            self.error = str(exc)
            self.model = None
            self.metadata = None

    def status(self):
        meta = self.metadata or {}
        return {"ready": self.model is not None, "device": str(self.device), "error": self.error,
                "name": "3D U-Net · BraTS2023 GLI", "experiment_id": meta.get("protocol", {}).get("experiment_id"),
                "training_epochs": meta.get("protocol", {}).get("total_epochs"), "selected_epoch": meta.get("best_epoch"),
                "state_id": meta.get("best_state_id"), "weights_sha256": meta.get("weights_sha256"),
                "validation": meta.get("validation"), "test": meta.get("test")}

    def predict(self, paths: dict[str, Path], destination: Path, progress):
        if self.model is None:
            raise RuntimeError("Model unavailable; run scripts/prepare_model.py")
        with self.lock, torch.inference_mode():
            started = time.perf_counter()
            progress(10, "Normalizing four MRI modalities")
            array, reference = preprocess(paths, self.metadata)
            image = torch.from_numpy(array).unsqueeze(0)
            protocol = self.metadata["protocol"]
            tta, min_voxels, batch_size, overlap, _ = protocol["inference"]

            def predictor(patches):
                with torch.autocast(device_type=self.device.type, enabled=self.device.type == "cuda"):
                    return self.model(patches).float()

            def infer(volume):
                logits = sliding_window_inference(volume, tuple(protocol["patch_size"]), batch_size,
                         predictor, overlap=overlap, mode="gaussian", sw_device=self.device, device=torch.device("cpu"))
                return logits.softmax(dim=1)

            progress(25, "Segmenting with 3D sliding windows")
            probabilities = infer(image)
            if tta:
                probabilities.add_(infer(image.flip(2)).flip(2)).mul_(0.5)
            mask = probabilities.argmax(1)[0].numpy().astype(np.uint8)
            progress(90, "Removing small components and exporting NIfTI")
            for region in (1, 2, 3):
                components, _ = label(mask == region)
                small = np.bincount(components.ravel()) < min_voxels
                small[0] = False
                mask[small[components]] = 0
            output = nib.Nifti1Image(mask, reference.affine)
            output.header.set_xyzt_units("mm")
            output.header["descrip"] = b"BrainTumor AI: 0 BG, 1 NCR/NET, 2 ED, 3 ET; research only"
            destination.parent.mkdir(parents=True, exist_ok=True)
            temporary = destination.with_name("prediction.tmp.nii.gz")
            nib.save(output, temporary)
            temporary.replace(destination)
            return {"volumes_cm3": region_volumes(mask, reference.affine), "seconds": round(time.perf_counter() - started, 2),
                    "selected_epoch": self.metadata["best_epoch"], "training_epochs": 50,
                    "model_state_id": self.metadata["best_state_id"], "weights_sha256": self.metadata["weights_sha256"],
                    "labels": self.metadata["labels"], "metric_note": "No case Dice without ground-truth segmentation."}
