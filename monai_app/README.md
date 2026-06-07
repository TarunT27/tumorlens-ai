# MONAI Label Setup Notes

TumorLens AI treats MONAI Label as a separate AI inference server. This keeps GPU-heavy inference outside 3D Slicer and makes the Slicer extension a clean workflow client.

## Recommended Starter Path

Install MONAI Label in a Python environment compatible with your CUDA/PyTorch setup, then download the radiology sample app and a public dataset.

```bash
powershell -ExecutionPolicy Bypass -File scripts/setup_monai.ps1
powershell -ExecutionPolicy Bypass -File scripts/download_monai_radiology_app.ps1
powershell -ExecutionPolicy Bypass -File scripts/download_monai_brats_bundle.ps1
```

For a brain tumor demo, use a public BraTS-style or Medical Segmentation Decathlon `Task01_BrainTumour` dataset. Place NIfTI files under a local studies directory such as:

```text
datasets/Task01_BrainTumour/imagesTr
```

Start the server:

```bash
powershell -ExecutionPolicy Bypass -File scripts/start_monai_server.ps1 -StudiesPath datasets/Task01_BrainTumour/imagesTr -UseBrainTumorBundle
```

By default, MONAI Label serves at:

```text
http://127.0.0.1:8000
```

## Hugging Face MONAI BraTS Bundle

The recommended Hugging Face model bundle for this project is `MONAI/brats_mri_segmentation`, installed locally under:

```text
monai_app/bundles/brats_mri_segmentation
```

This bundle is a 3D BraTS MRI segmentation model for aligned T1c, T1, T2, and FLAIR volumes. It outputs tumor core, whole tumor, and enhancing tumor channels. Downloaded bundle files are ignored by Git; rerun `scripts/download_monai_brats_bundle.ps1` to refresh or reinstall them.

`scripts/start_monai_server.ps1 -UseBrainTumorBundle` registers this local bundle under the MONAI Label radiology app's ignored `model/` directory, then starts the server with:

```text
--conf models deepedit --conf bundles brats_mri_segmentation
```

Use `scripts/create_synthetic_brats_study.ps1` for server/connectivity checks only. It creates a small channel-first 4-channel NIfTI with shape `(4, X, Y, Z)` and channel order T1c, T1, T2, and FLAIR. Meaningful BraTS inference requires a compatible public BraTS-style study with the same four-channel input contract.

With the server running, verify live model inference:

```bash
powershell -ExecutionPolicy Bypass -File scripts/test_monai_inference.ps1
```

The smoke test calls `/infer/brats_mri_segmentation?image=synthetic_brats_001` and saves the returned labelmap under `reports/monai_smoke`.

## Notes

- Keep private patient data out of this portfolio project.
- GPU support is recommended for real inference.
- The current Slicer client wrapper handles JSON responses and MONAI multipart responses that include a binary labelmap/image part.
- No external API key is required. MONAI Label runs locally.
