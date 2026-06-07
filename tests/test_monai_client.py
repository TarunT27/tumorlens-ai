import json
from pathlib import Path
import tempfile
import unittest

from TumorLensAI.TumorLensAIMONAIClient import TumorLensAIMONAIClient


class TumorLensAIMONAIClientTests(unittest.TestCase):
    def test_status_extracts_models_from_models_endpoint(self):
        def transport(method, url, headers, body, timeout):
            self.assertEqual(method, "GET")
            if url.endswith("/info"):
                return 200, {"name": "MONAI Label"}
            if url.endswith("/models"):
                return 200, {"models": {"deepedit": {}, "segmentation": {}}}
            return 404, {}

        client = TumorLensAIMONAIClient("http://example.test", transport=transport)

        status = client.check_status()

        self.assertTrue(status.reachable)
        self.assertEqual(status.models, ["deepedit", "segmentation"])

    def test_status_reports_unreachable_server(self):
        def transport(method, url, headers, body, timeout):
            raise TimeoutError("server timeout")

        client = TumorLensAIMONAIClient("http://example.test", transport=transport)

        status = client.check_status()

        self.assertFalse(status.reachable)
        self.assertIn("server timeout", status.message)

    def test_status_extracts_models_from_info_when_models_endpoint_missing(self):
        def transport(method, url, headers, body, timeout):
            if url.endswith("/info"):
                return 200, {"models": {"deepedit": {}, "brats_mri_segmentation": {}}}
            if url.endswith("/models"):
                return 404, {}
            return 404, {}

        client = TumorLensAIMONAIClient("http://example.test", transport=transport)

        status = client.check_status()

        self.assertTrue(status.reachable)
        self.assertEqual(status.models, ["deepedit", "brats_mri_segmentation"])

    def test_json_request_sends_encoded_payload(self):
        captured = {}

        def transport(method, url, headers, body, timeout):
            captured["body"] = body
            return 200, {"ok": True}

        client = TumorLensAIMONAIClient("http://example.test", transport=transport)
        status_code, payload = client._json_request("POST", "/demo", {"model": "deepedit"})

        self.assertEqual(status_code, 200)
        self.assertEqual(payload, {"ok": True})
        self.assertEqual(json.loads(captured["body"].decode("utf-8")), {"model": "deepedit"})

    def test_file_inference_materializes_multipart_labelmap(self):
        boundary = "tumorlens-test-boundary"
        label_bytes = b"synthetic-nifti-labelmap"
        raw_response = (
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="params"\r\n'
            "Content-Type: application/json\r\n\r\n"
            '{"label_names":{"whole tumor":1},"latencies":{"total":1.2}}\r\n'
            f"--{boundary}\r\n"
            'Content-Disposition: form-data; name="image"; filename="prediction.nii.gz"\r\n'
            "Content-Type: application/octet-stream\r\n\r\n"
        ).encode("utf-8") + label_bytes + f"\r\n--{boundary}--\r\n".encode("utf-8")

        def transport(method, url, headers, body, timeout):
            client_for_parser = TumorLensAIMONAIClient("http://example.test")
            payload = client_for_parser._parse_response_body(
                raw_response,
                f"multipart/form-data; boundary={boundary}",
            )
            return 200, payload

        client = TumorLensAIMONAIClient("http://example.test", transport=transport)

        with tempfile.TemporaryDirectory() as tmpdir:
            input_path = Path(tmpdir) / "input.nii.gz"
            input_path.write_bytes(b"input")

            payload = client.run_inference_file("brats_mri_segmentation", input_path, output_dir=tmpdir)

            self.assertEqual(payload["label_names"], {"whole tumor": 1})
            self.assertIn("labelmap", payload)
            self.assertEqual(Path(payload["labelmap"]).read_bytes(), label_bytes)

    def test_registered_image_inference_uses_image_query(self):
        captured = {}

        def transport(method, url, headers, body, timeout):
            captured["method"] = method
            captured["url"] = url
            captured["timeout"] = timeout
            return 200, {"labelmap": "already-on-disk.nii.gz"}

        client = TumorLensAIMONAIClient("http://example.test", inference_timeout=123, transport=transport)

        payload = client.run_inference_image_id("brats_mri_segmentation", "synthetic brats 001")

        self.assertEqual(payload["labelmap"], "already-on-disk.nii.gz")
        self.assertEqual(captured["method"], "POST")
        self.assertIn("/infer/brats_mri_segmentation?image=synthetic+brats+001", captured["url"])
        self.assertEqual(captured["timeout"], 123)


if __name__ == "__main__":
    unittest.main()
