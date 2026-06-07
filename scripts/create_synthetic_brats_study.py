from __future__ import annotations

import argparse
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Create a synthetic 4-channel BraTS-style NIfTI study for MONAI bundle setup checks."
    )
    parser.add_argument(
        "--out",
        default="sample_data/synthetic_brats_mri/imagesTr/synthetic_brats_001.nii.gz",
        help="Output 4-channel NIfTI path.",
    )
    args = parser.parse_args()

    try:
        import nibabel as nib
        import numpy as np
    except ImportError as exc:
        raise SystemExit("This script requires nibabel and numpy. Run scripts/setup_monai.ps1 first.") from exc

    output_path = Path(args.out)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    rng = np.random.default_rng(2026)
    shape = (64, 80, 48)
    x, y, z = np.indices(shape)
    cx, cy, cz = 32, 40, 24

    brain = (((x - cx) / 25) ** 2 + ((y - cy) / 32) ** 2 + ((z - cz) / 20) ** 2) <= 1
    edema = (((x - 40) / 12) ** 2 + ((y - 45) / 15) ** 2 + ((z - 27) / 9) ** 2) <= 1
    tumor_core = (((x - 42) / 6) ** 2 + ((y - 46) / 8) ** 2 + ((z - 28) / 5) ** 2) <= 1
    enhancing_tumor = (((x - 42) / 8) ** 2 + ((y - 46) / 10) ** 2 + ((z - 28) / 7) ** 2) <= 1

    def base_channel(mean: float, noise: float = 0.035):
        image = rng.normal(0.02, noise, size=shape).astype(np.float32)
        image[brain] = rng.normal(mean, noise, size=int(brain.sum())).astype(np.float32)
        return image

    # BraTS bundle channel order: T1c, T1, T2, FLAIR.
    t1c = base_channel(0.36)
    t1 = base_channel(0.30)
    t2 = base_channel(0.24)
    flair = base_channel(0.28)

    t1c[edema] = 0.42
    t1c[enhancing_tumor] = 0.96
    t1c[tumor_core] = 0.20

    t1[edema] = 0.25
    t1[enhancing_tumor] = 0.50
    t1[tumor_core] = 0.16

    t2[edema] = 0.90
    t2[enhancing_tumor] = 0.70
    t2[tumor_core] = 0.52

    flair[edema] = 0.95
    flair[enhancing_tumor] = 0.78
    flair[tumor_core] = 0.44

    image = np.stack([t1c, t1, t2, flair], axis=0)
    image = np.clip(image, 0, 1).astype(np.float32)

    affine = np.array(
        [
            [1.0, 0.0, 0.0, 0.0],
            [0.0, 1.0, 0.0, 0.0],
            [0.0, 0.0, 1.0, 0.0],
            [0.0, 0.0, 0.0, 1.0],
        ]
    )
    nib.save(nib.Nifti1Image(image, affine), output_path)
    print(output_path)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
