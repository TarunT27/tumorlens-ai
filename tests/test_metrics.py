import csv
import json
import tempfile
import unittest
from pathlib import Path

from TumorLensAI.TumorLensAIMetrics import TumorLensAIMetrics
from TumorLensAI.TumorLensAILogic import TumorLensAILogic


class TumorLensAIMetricsTests(unittest.TestCase):
    def test_computes_expected_metrics_for_synthetic_cube(self):
        label_array = [
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 1, 1, 0], [0, 1, 1, 0], [0, 0, 0, 0]],
            [[0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0], [0, 0, 0, 0]],
        ]

        report = TumorLensAIMetrics().compute_from_label_array(
            label_array,
            spacing=(2.0, 3.0, 4.0),
            label_names={1: "Enhancing Tumor"},
            study_id="synthetic-case",
        )

        self.assertEqual(report.studyId, "synthetic-case")
        self.assertEqual(report.voxelCount, 8)
        self.assertEqual(report.tumorVolumeCm3, 0.192)
        self.assertEqual(report.boundingBoxMm, [4.0, 6.0, 8.0])
        self.assertEqual(report.centerOfMassMm, [4.0, 6.0, 8.0])
        self.assertEqual(report.surfaceAreaMm2, 208.0)
        self.assertEqual(report.labelBreakdown["1"]["name"], "Enhancing Tumor")

    def test_empty_labelmap_returns_warning(self):
        report = TumorLensAIMetrics().compute_from_label_array([[[0]]])

        self.assertEqual(report.voxelCount, 0)
        self.assertEqual(report.tumorVolumeCm3, 0.0)
        self.assertIn("No positive tumor labels", report.warnings[0])

    def test_report_export_json_and_csv(self):
        report = TumorLensAIMetrics().compute_from_label_array([[[1]]], spacing=(1, 1, 1))
        logic = TumorLensAILogic()

        with tempfile.TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "report.json"
            csv_path = Path(tmpdir) / "report.csv"

            logic.exportReport(report, json_path)
            logic.exportReport(report, csv_path)

            payload = json.loads(json_path.read_text(encoding="utf-8"))
            self.assertIn("tumorVolumeCm3", payload)

            with csv_path.open(newline="", encoding="utf-8") as csv_file:
                rows = list(csv.DictReader(csv_file))
            self.assertTrue(any(row["metric"] == "tumorVolumeCm3" for row in rows))


if __name__ == "__main__":
    unittest.main()

