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

Run this to generate a small fake MRI-like NIfTI volume:

```bash
powershell -ExecutionPolicy Bypass -File scripts/create_synthetic_study.ps1
```

Output:

```text
sample_data/synthetic_brain_mri/imagesTr/synthetic_brain_001.nii.gz
```

This is for setup and demo plumbing only. It is not a real medical image and should not be used to evaluate model quality.
