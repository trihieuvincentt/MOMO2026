import argparse
import json
import os
import time
from pathlib import Path


def _peak_rss_mb() -> float | None:
    try:
        import psutil

        return psutil.Process(os.getpid()).memory_info().rss / (1024 * 1024)
    except ImportError:
        try:
            import resource
        except ImportError:
            return None
        peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
        return peak / (1024 * 1024) if os.name != "nt" else peak / 1024


def main() -> None:
    parser = argparse.ArgumentParser(description="Measure PaddleOCR startup and per-image latency")
    parser.add_argument("images", nargs="*", type=Path)
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    started = time.perf_counter()
    try:
        from paddleocr import PaddleOCR
    except ImportError as exc:
        raise SystemExit("PaddleOCR is not installed; proof-of-fit was not run.") from exc

    engine = PaddleOCR(lang=args.language, use_textline_orientation=True)
    startup_seconds = time.perf_counter() - started
    results = []
    for image_path in args.images:
        request_started = time.perf_counter()
        engine.predict(str(image_path))
        results.append({"image": image_path.name, "latency_seconds": time.perf_counter() - request_started})

    print(json.dumps({
        "ocr_source": "paddleocr",
        "startup_seconds": startup_seconds,
        "peak_rss_mb": _peak_rss_mb(),
        "model_download_behavior": "record whether first startup downloaded model weights in this environment",
        "request_results": results,
    }, indent=2))


if __name__ == "__main__":
    main()
