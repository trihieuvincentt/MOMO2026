import json
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))


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
    import argparse

    from backend.app.adapters.ocr_engine import PaddleOCREngine

    parser = argparse.ArgumentParser(description="Measure PaddleOCR startup and latency")
    parser.add_argument("images", nargs="+", type=Path)
    parser.add_argument("--language", default="en")
    args = parser.parse_args()

    engine = PaddleOCREngine()
    started = time.perf_counter()
    engine._get_engine(args.language)
    startup_seconds = time.perf_counter() - started

    requests = []
    for image in args.images:
        request_started = time.perf_counter()
        result = engine.extract(image, args.language)
        requests.append({
            "image": image.name,
            "latency_seconds": time.perf_counter() - request_started,
            "text_chars": len(result.text),
            "warning_count": len(result.warnings),
        })

    print(json.dumps({
        "ocr_source": "paddleocr",
        "startup_seconds": startup_seconds,
        "rss_mb_after_startup": _peak_rss_mb(),
        "request_results": requests,
        "model_cache_dir": str(Path.home() / ".paddlex" / "official_models"),
    }, indent=2))


if __name__ == "__main__":
    main()
