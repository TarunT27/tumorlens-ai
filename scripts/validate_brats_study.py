from __future__ import annotations

import argparse
from pathlib import Path


def nifti_paths(studies_path: Path) -> list[Path]:
    if studies_path.is_file():
        return [studies_path]
    return sorted([*studies_path.glob("*.nii"), *studies_path.glob("*.nii.gz")])


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate a BraTS-style study for the MONAI BraTS bundle.")
    parser.add_argument("--studies", required=True, help="Study directory or NIfTI image path.")
    args = parser.parse_args()

    try:
        import nibabel as nib
    except ImportError as exc:
        raise SystemExit("This script requires nibabel. Run scripts/setup_monai.ps1 first.") from exc

    studies_path = Path(args.studies)
    if not studies_path.exists():
        raise SystemExit(f"Studies path does not exist: {studies_path}")

    images = nifti_paths(studies_path)
    if not images:
        raise SystemExit(f"No NIfTI images found in: {studies_path}")

    for image_path in images:
        image = nib.load(str(image_path))
        shape = image.shape
        if len(shape) != 4 or shape[0] != 4:
            raise SystemExit(
                f"{image_path} has shape {shape}; expected a 4D channel-first NIfTI "
                "(4, X, Y, Z) for T1c, T1, T2, and FLAIR."
            )
        if any(axis % 8 != 0 for axis in shape[1:]):
            raise SystemExit(
                f"{image_path} has spatial shape {shape[1:]}; each spatial dimension should be divisible by 8."
            )
        print(f"BraTS-compatible image: {image_path} shape={shape}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
