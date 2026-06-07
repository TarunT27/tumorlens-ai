# Sample Data

Use public research datasets only. Do not commit patient data or private scans.

Recommended starting point:

- Medical Segmentation Decathlon `Task01_BrainTumour`
- BraTS-style public brain tumor MRI volumes

Expected first milestone format:

```text
sample_data/
  Task01_BrainTumour/
    imagesTr/
      *.nii.gz
```

Keep large datasets outside Git. Add only small synthetic fixtures if needed for tests.

## Synthetic Local Demo

Run this to generate a small fake 4-channel BraTS-style NIfTI volume for MONAI bundle connectivity checks:

```bash
powershell -ExecutionPolicy Bypass -File scripts/create_synthetic_brats_study.ps1
```

Output:

```text
sample_data/synthetic_brats_mri/imagesTr/synthetic_brats_001.nii.gz
```

This image has shape `(4, X, Y, Z)` with channels ordered as T1c, T1, T2, and FLAIR. It is for setup and demo plumbing only, not a real medical image, and should not be used to evaluate model quality.

The older single-channel generator is still available for generic volume-loading checks:

```bash
powershell -ExecutionPolicy Bypass -File scripts/create_synthetic_study.ps1
```
