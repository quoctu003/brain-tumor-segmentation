"""Render actual demo MRI slices with the recorded prediction, without identifiers."""
from pathlib import Path

import nibabel as nib
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import ListedColormap

ROOT = Path(__file__).resolve().parents[1]


def main():
    image = np.asarray(nib.load(ROOT / "demo/t2f.nii.gz").dataobj)
    mask = np.asarray(nib.load(ROOT / "demo/segmentation.nii.gz").dataobj)
    center = np.median(np.argwhere(mask > 0), axis=0).astype(int)
    cmap = ListedColormap(["#ef5b6c", "#4dc796", "#fabc53"])
    low, high = np.percentile(image[image > 0], [1, 99])
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), facecolor="#10171d")
    for axis, panel in enumerate(axes):
        slc = [slice(None)] * 3
        slc[axis] = center[axis]
        values = np.rot90(image[tuple(slc)])
        labels = np.rot90(mask[tuple(slc)])
        panel.imshow(values, cmap="gray", vmin=low, vmax=high)
        panel.imshow(np.ma.masked_equal(labels, 0), cmap=cmap, vmin=1, vmax=3, alpha=0.65, interpolation="nearest")
        panel.set_axis_off()
    fig.subplots_adjust(0, 0, 1, 1, wspace=0.02)
    destination = ROOT / "frontend/public/demo-preview.png"
    destination.parent.mkdir(exist_ok=True)
    fig.savefig(destination, dpi=100, facecolor=fig.get_facecolor(), bbox_inches="tight", pad_inches=0.08)
    plt.close(fig)
    print(destination)


if __name__ == "__main__":
    main()
