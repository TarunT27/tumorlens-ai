"""Measurement utilities for TumorLens AI.

The array-based functions are intentionally Slicer-independent so they can be
unit-tested in a normal Python environment. Slicer node helpers are layered on
top and only import Slicer when called from inside the application.
"""

from __future__ import annotations

from dataclasses import asdict, dataclass, field
from typing import Any, Iterable


@dataclass
class MeasurementReport:
    studyId: str
    modality: str
    tumorVolumeCm3: float
    voxelCount: int
    surfaceAreaMm2: float
    boundingBoxMm: list[float]
    centerOfMassMm: list[float]
    labelBreakdown: dict[str, dict[str, Any]]
    warnings: list[str] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TumorLensAIMetrics:
    """Compute quantitative measurements from tumor labelmaps."""

    BACKGROUND_LABEL = 0

    def compute_from_label_array(
        self,
        label_array: Any,
        spacing: Iterable[float] = (1.0, 1.0, 1.0),
        origin: Iterable[float] = (0.0, 0.0, 0.0),
        label_names: dict[int, str] | None = None,
        study_id: str = "",
        modality: str = "MRI",
    ) -> MeasurementReport:
        spacing_xyz = self._triple(spacing, "spacing")
        origin_xyz = self._triple(origin, "origin")
        voxels = self._positive_voxels(label_array)
        warnings: list[str] = []

        if not voxels:
            return MeasurementReport(
                studyId=study_id,
                modality=modality,
                tumorVolumeCm3=0.0,
                voxelCount=0,
                surfaceAreaMm2=0.0,
                boundingBoxMm=[0.0, 0.0, 0.0],
                centerOfMassMm=[0.0, 0.0, 0.0],
                labelBreakdown={},
                warnings=["No positive tumor labels were found."],
            )

        voxel_volume_mm3 = spacing_xyz[0] * spacing_xyz[1] * spacing_xyz[2]
        label_breakdown = self._label_breakdown(voxels, voxel_volume_mm3, label_names)
        bbox_mm = self._bounding_box_mm(voxels, spacing_xyz)
        center_mm = self._center_of_mass_mm(voxels, spacing_xyz, origin_xyz)
        surface_area_mm2 = self._surface_area_mm2(voxels, spacing_xyz)

        return MeasurementReport(
            studyId=study_id,
            modality=modality,
            tumorVolumeCm3=round(len(voxels) * voxel_volume_mm3 / 1000.0, 6),
            voxelCount=len(voxels),
            surfaceAreaMm2=round(surface_area_mm2, 6),
            boundingBoxMm=[round(value, 6) for value in bbox_mm],
            centerOfMassMm=[round(value, 6) for value in center_mm],
            labelBreakdown=label_breakdown,
            warnings=warnings,
        )

    def compute_from_slicer_nodes(self, volume_node: Any, segmentation_node: Any) -> MeasurementReport:
        slicer = self._require_slicer()

        spacing = volume_node.GetSpacing()
        origin = volume_node.GetOrigin()
        study_id = volume_node.GetName() if hasattr(volume_node, "GetName") else ""
        modality = volume_node.GetAttribute("DICOM.Modality") or "MRI"

        segmentation = segmentation_node.GetSegmentation()
        segment_count = segmentation.GetNumberOfSegments()
        if segment_count == 0:
            return self.compute_from_label_array([], spacing, origin, study_id=study_id, modality=modality)

        merged_array = None
        label_names: dict[int, str] = {}

        for index in range(segment_count):
            segment_id = segmentation.GetNthSegmentID(index)
            segment = segmentation.GetSegment(segment_id)
            label_value = index + 1
            label_names[label_value] = segment.GetName()
            segment_array = slicer.util.arrayFromSegmentBinaryLabelmap(
                segmentation_node,
                segment_id,
                volume_node,
            )

            if merged_array is None:
                merged_array = segment_array * label_value
            else:
                merged_array[segment_array > 0] = label_value

        return self.compute_from_label_array(
            merged_array,
            spacing=spacing,
            origin=origin,
            label_names=label_names,
            study_id=study_id,
            modality=modality,
        )

    def _positive_voxels(self, label_array: Any) -> list[tuple[int, int, int, int]]:
        voxels: list[tuple[int, int, int, int]] = []

        if hasattr(label_array, "shape"):
            shape = label_array.shape
            if len(shape) != 3:
                raise ValueError("label_array must be 3-dimensional with z, y, x indexing")
            for z in range(shape[0]):
                for y in range(shape[1]):
                    for x in range(shape[2]):
                        label = int(label_array[z, y, x])
                        if label != self.BACKGROUND_LABEL:
                            voxels.append((x, y, z, label))
            return voxels

        for z, plane in enumerate(label_array):
            for y, row in enumerate(plane):
                for x, label in enumerate(row):
                    label_int = int(label)
                    if label_int != self.BACKGROUND_LABEL:
                        voxels.append((x, y, z, label_int))
        return voxels

    def _label_breakdown(
        self,
        voxels: list[tuple[int, int, int, int]],
        voxel_volume_mm3: float,
        label_names: dict[int, str] | None,
    ) -> dict[str, dict[str, Any]]:
        counts: dict[int, int] = {}
        for *_coords, label in voxels:
            counts[label] = counts.get(label, 0) + 1

        breakdown: dict[str, dict[str, Any]] = {}
        for label in sorted(counts):
            name = label_names.get(label, f"Label {label}") if label_names else f"Label {label}"
            breakdown[str(label)] = {
                "name": name,
                "voxelCount": counts[label],
                "volumeCm3": round(counts[label] * voxel_volume_mm3 / 1000.0, 6),
            }
        return breakdown

    def _bounding_box_mm(
        self,
        voxels: list[tuple[int, int, int, int]],
        spacing_xyz: tuple[float, float, float],
    ) -> list[float]:
        xs = [voxel[0] for voxel in voxels]
        ys = [voxel[1] for voxel in voxels]
        zs = [voxel[2] for voxel in voxels]
        return [
            (max(xs) - min(xs) + 1) * spacing_xyz[0],
            (max(ys) - min(ys) + 1) * spacing_xyz[1],
            (max(zs) - min(zs) + 1) * spacing_xyz[2],
        ]

    def _center_of_mass_mm(
        self,
        voxels: list[tuple[int, int, int, int]],
        spacing_xyz: tuple[float, float, float],
        origin_xyz: tuple[float, float, float],
    ) -> list[float]:
        count = len(voxels)
        mean_x = sum(voxel[0] + 0.5 for voxel in voxels) / count
        mean_y = sum(voxel[1] + 0.5 for voxel in voxels) / count
        mean_z = sum(voxel[2] + 0.5 for voxel in voxels) / count
        return [
            origin_xyz[0] + mean_x * spacing_xyz[0],
            origin_xyz[1] + mean_y * spacing_xyz[1],
            origin_xyz[2] + mean_z * spacing_xyz[2],
        ]

    def _surface_area_mm2(
        self,
        voxels: list[tuple[int, int, int, int]],
        spacing_xyz: tuple[float, float, float],
    ) -> float:
        occupied = {(x, y, z) for x, y, z, _label in voxels}
        face_areas = {
            (1, 0, 0): spacing_xyz[1] * spacing_xyz[2],
            (-1, 0, 0): spacing_xyz[1] * spacing_xyz[2],
            (0, 1, 0): spacing_xyz[0] * spacing_xyz[2],
            (0, -1, 0): spacing_xyz[0] * spacing_xyz[2],
            (0, 0, 1): spacing_xyz[0] * spacing_xyz[1],
            (0, 0, -1): spacing_xyz[0] * spacing_xyz[1],
        }
        surface_area = 0.0
        for x, y, z in occupied:
            for (dx, dy, dz), area in face_areas.items():
                if (x + dx, y + dy, z + dz) not in occupied:
                    surface_area += area
        return surface_area

    def _triple(self, values: Iterable[float], name: str) -> tuple[float, float, float]:
        triple = tuple(float(value) for value in values)
        if len(triple) != 3:
            raise ValueError(f"{name} must contain exactly 3 values")
        if name == "spacing" and any(value <= 0 for value in triple):
            raise ValueError("spacing values must be greater than zero")
        return triple

    def _require_slicer(self) -> Any:
        try:
            import slicer  # type: ignore
        except ImportError as exc:
            raise RuntimeError("Slicer metrics require running inside 3D Slicer.") from exc
        return slicer

