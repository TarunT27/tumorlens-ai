from __future__ import annotations

import argparse
from pathlib import Path
import sys


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    sys.path.insert(0, str(repo_root))

    from TumorLensAI.TumorLensAIMONAIClient import TumorLensAIMONAIClient

    parser = argparse.ArgumentParser(description="Run a live MONAI Label inference smoke test.")
    parser.add_argument("--server-url", default="http://127.0.0.1:8000")
    parser.add_argument("--model", default="brats_mri_segmentation")
    parser.add_argument("--image", default="synthetic_brats_001")
    parser.add_argument("--output-dir", default="reports/monai_smoke")
    parser.add_argument("--timeout", type=float, default=300.0)
    args = parser.parse_args()

    output_dir = repo_root / args.output_dir
    client = TumorLensAIMONAIClient(args.server_url, inference_timeout=args.timeout)

    status = client.check_status()
    if not status.reachable:
        raise SystemExit(f"MONAI Label server is not reachable: {status.message}")
    if args.model not in status.models:
        raise SystemExit(f"Model '{args.model}' was not found. Available models: {', '.join(status.models)}")

    payload = client.run_inference_image_id(args.model, args.image, output_dir=output_dir)
    labelmap = payload.get("labelmap")
    if not labelmap or not Path(labelmap).exists():
        raise SystemExit("MONAI inference completed, but no labelmap file was materialized.")

    label_names = payload.get("label_names") or payload.get("labels") or {}
    latencies = payload.get("latencies") or {}
    print("MONAI inference smoke passed")
    print(f"Server: {args.server_url}")
    print(f"Model: {args.model}")
    print(f"Image: {args.image}")
    print(f"Labelmap: {labelmap}")
    if label_names:
        print(f"Labels: {', '.join(str(name) for name in label_names)}")
    if "total" in latencies:
        print(f"Total latency: {latencies['total']}s")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
