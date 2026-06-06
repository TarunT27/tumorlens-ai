import unittest

from TumorLensAI.TumorLensAILogic import TumorLensAILogic


class TumorLensAISlicerWorkflowTests(unittest.TestCase):
    def test_slicer_workflow_requires_slicer_environment(self):
        logic = TumorLensAILogic()

        try:
            import slicer  # type: ignore  # noqa: F401
        except ImportError:
            with self.assertRaisesRegex(RuntimeError, "3D Slicer"):
                logic.loadVolume("missing.nii.gz")
        else:
            self.skipTest("Run full workflow smoke tests manually inside 3D Slicer with sample data.")


if __name__ == "__main__":
    unittest.main()

