import json
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


if __name__ == "__main__":
    unittest.main()

