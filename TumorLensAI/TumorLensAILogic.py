"""Core workflow orchestration for TumorLens AI."""

from __future__ import annotations

from dataclasses import asdict, dataclass
import csv
from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Any

try:
    from .TumorLensAIMetrics import MeasurementReport, TumorLensAIMetrics
    from .TumorLensAIMONAIClient import ServerStatus, TumorLensAIMONAIClient
except ImportError:  # pragma: no cover - supports Slicer loading as a loose scripted module.
    from TumorLensAIMetrics import MeasurementReport, TumorLensAIMetrics
    from TumorLensAIMONAIClient import ServerStatus, TumorLensAIMONAIClient


@dataclass
class SegmentationResult:
    volumeNodeId: str
    segmentationNodeId: str
    modelName: str
    labels: list[str]
    createdAt: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


class TumorLensAILogic:
    """Public API used by the future UI layer and Slicer scripted module."""

    def __init__(self, monai_client: TumorLensAIMONAIClient | None = None, metrics: TumorLensAIMetrics | None = None):
        self.monai_client = monai_client or TumorLensAIMONAIClient()
        self.metrics = metrics or TumorLensAIMetrics()

    def loadVolume(self, path: str | Path) -> Any:
        slicer = self._require_slicer()
        path = str(path)
        loaded = slicer.util.loadVolume(path, returnNode=True)

        if isinstance(loaded, tuple):
            success, volume_node = loaded
        else:
            volume_node = loaded
            success = volume_node is not None

        if not success or volume_node is None:
            raise RuntimeError(f"Could not load volume: {path}")
        return volume_node

    def connectMonaiServer(self, url: str = "http://127.0.0.1:8000") -> ServerStatus:
        self.monai_client = TumorLensAIMONAIClient(url)
        return self.monai_client.check_status()

    def runSegmentation(self, volumeNode: Any, modelName: str = "deepedit") -> Any:
        slicer = self._require_slicer()

        with tempfile.TemporaryDirectory(prefix="tumorlensai_") as tmpdir:
            exported_volume = Path(tmpdir) / "input_volume.nii.gz"
            if not slicer.util.saveNode(volumeNode, str(exported_volume)):
                raise RuntimeError("Failed to export selected volume before MONAI Label inference.")

            response = self.monai_client.run_inference_file(modelName, exported_volume, output_dir=tmpdir)
            labelmap_path = self._labelmap_path_from_response(response)
            if not labelmap_path:
                raise RuntimeError(
                    "MONAI Label inference did not return a labelmap path. "
                    "Use simulateSegmentation for a no-server demo or check the deployed MONAI app response shape."
                )

            return self._load_labelmap_as_segmentation(labelmap_path, volumeNode, modelName)

    def simulateSegmentation(self, volumeNode: Any, name: str = "Simulated Tumor") -> Any:
        """Create a small ellipsoid-like segmentation for demos without MONAI Label."""

        slicer = self._require_slicer()
        import vtk  # type: ignore

        segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", name)
        segmentation_node.CreateDefaultDisplayNodes()
        segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(volumeNode)

        labelmap_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLLabelMapVolumeNode", f"{name} Labelmap")
        labelmap_node.CopyOrientation(volumeNode)
        slicer.modules.volumes.logic().CreateLabelVolumeFromVolume(slicer.mrmlScene, labelmap_node, volumeNode)

        image_data = labelmap_node.GetImageData()
        dims = image_data.GetDimensions()
        image_data.AllocateScalars(vtk.VTK_UNSIGNED_CHAR, 1)
        image_data.GetPointData().GetScalars().Fill(0)
        center = [dimension / 2.0 for dimension in dims]
        radii = [max(dimension / 8.0, 2.0) for dimension in dims]

        for z in range(dims[2]):
            for y in range(dims[1]):
                for x in range(dims[0]):
                    normalized = (
                        ((x - center[0]) / radii[0]) ** 2
                        + ((y - center[1]) / radii[1]) ** 2
                        + ((z - center[2]) / radii[2]) ** 2
                    )
                    if normalized <= 1.0:
                        image_data.SetScalarComponentFromDouble(x, y, z, 0, 1)
        image_data.Modified()
        labelmap_node.Modified()

        segmentations_logic = slicer.modules.segmentations.logic()
        segmentations_logic.ImportLabelmapToSegmentationNode(labelmap_node, segmentation_node)
        segmentation_node.GetSegmentation().GetSegment(segmentation_node.GetSegmentation().GetNthSegmentID(0)).SetName(name)
        slicer.mrmlScene.RemoveNode(labelmap_node)
        return segmentation_node

    def createClosedSurface(self, segmentationNode: Any) -> Any:
        slicer = self._require_slicer()
        segmentationNode.CreateClosedSurfaceRepresentation()

        sh_node = slicer.vtkMRMLSubjectHierarchyNode.GetSubjectHierarchyNode(slicer.mrmlScene)
        folder_item_id = sh_node.CreateFolderItem(sh_node.GetSceneItemID(), "TumorLensAI Models")
        slicer.modules.segmentations.logic().ExportAllSegmentsToModels(segmentationNode, folder_item_id)

        model_nodes = slicer.util.getNodesByClass("vtkMRMLModelNode")
        if not model_nodes:
            raise RuntimeError("Closed surface representation was created, but no model node was exported.")
        return model_nodes[-1]

    def computeTumorMetrics(self, volumeNode: Any, segmentationNode: Any) -> MeasurementReport:
        return self.metrics.compute_from_slicer_nodes(volumeNode, segmentationNode)

    def exportReport(self, report: MeasurementReport | dict[str, Any], outputPath: str | Path) -> None:
        path = Path(outputPath)
        path.parent.mkdir(parents=True, exist_ok=True)
        report_dict = report.to_dict() if hasattr(report, "to_dict") else dict(report)

        if path.suffix.lower() == ".json":
            path.write_text(json.dumps(report_dict, indent=2), encoding="utf-8")
            return

        if path.suffix.lower() == ".csv":
            self._write_csv(report_dict, path)
            return

        raise ValueError("Report output path must end with .json or .csv")

    def buildSegmentationResult(self, volumeNode: Any, segmentationNode: Any, modelName: str) -> SegmentationResult:
        segmentation = segmentationNode.GetSegmentation()
        labels = [
            segmentation.GetSegment(segmentation.GetNthSegmentID(index)).GetName()
            for index in range(segmentation.GetNumberOfSegments())
        ]
        return SegmentationResult(
            volumeNodeId=volumeNode.GetID(),
            segmentationNodeId=segmentationNode.GetID(),
            modelName=modelName,
            labels=labels,
            createdAt=datetime.now(timezone.utc).isoformat(),
        )

    def _load_labelmap_as_segmentation(self, labelmap_path: str | Path, reference_volume_node: Any, model_name: str) -> Any:
        slicer = self._require_slicer()
        loaded = slicer.util.loadLabelVolume(str(labelmap_path), returnNode=True)
        success, labelmap_node = loaded if isinstance(loaded, tuple) else (loaded is not None, loaded)
        if not success or labelmap_node is None:
            raise RuntimeError(f"Could not load MONAI labelmap: {labelmap_path}")

        segmentation_node = slicer.mrmlScene.AddNewNodeByClass("vtkMRMLSegmentationNode", f"TumorLensAI {model_name} Segmentation")
        segmentation_node.CreateDefaultDisplayNodes()
        segmentation_node.SetReferenceImageGeometryParameterFromVolumeNode(reference_volume_node)
        slicer.modules.segmentations.logic().ImportLabelmapToSegmentationNode(labelmap_node, segmentation_node)
        slicer.mrmlScene.RemoveNode(labelmap_node)
        return segmentation_node

    def _labelmap_path_from_response(self, response: dict[str, Any]) -> str | None:
        for key in ("label", "labelmap", "result", "file", "path"):
            value = response.get(key)
            if isinstance(value, str) and Path(value).exists():
                return value
            if isinstance(value, dict):
                nested_path = self._labelmap_path_from_response(value)
                if nested_path:
                    return nested_path
        return None

    def _write_csv(self, report_dict: dict[str, Any], path: Path) -> None:
        scalar_keys = [
            "studyId",
            "modality",
            "tumorVolumeCm3",
            "voxelCount",
            "surfaceAreaMm2",
            "boundingBoxMm",
            "centerOfMassMm",
            "warnings",
        ]
        with path.open("w", newline="", encoding="utf-8") as csv_file:
            writer = csv.DictWriter(csv_file, fieldnames=["metric", "value"])
            writer.writeheader()
            for key in scalar_keys:
                writer.writerow({"metric": key, "value": json.dumps(report_dict.get(key))})
            for label, payload in report_dict.get("labelBreakdown", {}).items():
                writer.writerow({"metric": f"labelBreakdown.{label}", "value": json.dumps(payload)})

    def _require_slicer(self) -> Any:
        try:
            import slicer  # type: ignore
        except ImportError as exc:
            raise RuntimeError("This workflow requires running inside 3D Slicer.") from exc
        return slicer
