from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(description="Create a synthetic MRI-like NIfTI study for TumorLens AI setup checks.")
    parser.add_argument(
        "--out",
        default="sample_data/synthetic_brain_mri/imagesTr/synthetic_brain_001.nii.gz",
        help="Output NIfTI path.",
    )
    args = parser.parse_args()

    try:
        import nibabel as nib
        import numpy as np
    except ImportError as exc:
        raise SystemExit("This script requires nibabel and numpy. Run scripts/setup_monai.ps1 first.") from exc

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(42)
    shape = (80, 96, 64)
    z, y, x = np.indices(shape)
    cx, cy, cz = 40, 48, 32

    brain = (((x - cx) / 28) ** 2 + ((y - cy) / 36) ** 2 + ((z - cz) / 24) ** 2) <= 1
    tumor = (((x - 52) / 7) ** 2 + ((y - 54) / 9) ** 2 + ((z - 36) / 6) ** 2) <= 1
    edema = (((x - 50) / 13) ** 2 + ((y - 53) / 15) ** 2 + ((z - 35) / 10) ** 2) <= 1

    image = rng.normal(20, 4, size=shape).astype(np.float32)
    image[brain] = rng.normal(85, 8, size=int(brain.sum())).astype(np.float32)
    image[edema] = 120
    image[tumor] = 175
    image = np.clip(image, 0, 255).astype(np.float32)

    affine = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.2, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    nib.save(nib.Nifti1Image(image, affine), output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
