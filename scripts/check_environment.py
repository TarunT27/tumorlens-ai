from __future__ import annotations

import importlib.util
import os
import shutil
import subprocess
import sys
from pathlib import Path


def command_exists(command: str) -> bool:
    return shutil.which(command) is not None


def run(command: list[str]) -> str | None:
    try:
        completed = subprocess.run(command, check=False, capture_output=True, text=True)
    except OSError:
        return None
    return (completed.stdout or completed.stderr).strip()


def find_slicer(repo_root: Path) -> list[Path]:
    candidates: list[Path] = []
    path_hit = shutil.which("Slicer")
    if path_hit:
        candidates.append(Path(path_hit))

    roots = [
        Path("C:/Program Files"),
        Path("C:/Program Files (x86)"),
        Path(os.environ.get("LOCALAPPDATA", "")),
        Path(os.environ.get("APPDATA", "")),
    ]
    for root in roots:
        if not root.exists():
            continue
        try:
            candidates.extend(root.rglob("Slicer.exe"))
        except OSError:
            continue

    return sorted({candidate.resolve() for candidate in candidates if candidate.exists()})


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    slicer_candidates = find_slicer(repo_root)
    synthetic_study = repo_root / "sample_data" / "synthetic_brain_mri" / "imagesTr"
    synthetic_brats_study = repo_root / "sample_data" / "synthetic_brats_mri" / "imagesTr"
    msd_study = repo_root / "sample_data" / "Task01_BrainTumour" / "imagesTr"

    print("TumorLens AI environment check")
    print(f"Repo: {repo_root}")
    print(f"Python: {sys.version.split()[0]} ({sys.executable})")
    print(f"uv: {'found' if command_exists('uv') else 'missing'}")
    print(f"3D Slicer: {slicer_candidates[0] if slicer_candidates else 'not found'}")
    print(f"NVIDIA GPU check: {run(['nvidia-smi']) or 'nvidia-smi not available'}")

    monailabel_cli = command_exists("monailabel")
    monailabel_import = importlib.util.find_spec("monailabel") is not None
    print(f"MONAI Label CLI: {'found' if monailabel_cli else 'not found'}")
    print(f"MONAI Label Python package: {'found' if monailabel_import else 'not found'}")
    print(f"MONAI radiology app: {'found' if (repo_root / 'monai_app' / 'radiology').exists() else 'not found'}")
    print(f"Synthetic study path: {'found' if synthetic_study.exists() else 'not found'}")
    print(f"Synthetic BraTS study path: {'found' if synthetic_brats_study.exists() else 'not found'}")
    print(f"MSD brain tumor study path: {'found' if msd_study.exists() else 'not found'}")

    if sys.version_info >= (3, 13):
        print("Note: Python 3.13+ is fine for repo tests, but MONAI Label/PyTorch should use a separate older env.")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
