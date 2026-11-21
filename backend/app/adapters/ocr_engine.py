from dataclasses import dataclass, field
from pathlib import Path
from threading import Lock
from typing import Callable


@dataclass(frozen=True)
class OCRRegion:
    text: str
    confidence: float | None = None
    box: list[list[float]] | None = None


@dataclass(frozen=True)
class OCRResult:
    text: str
    regions: list[OCRRegion] = field(default_factory=list)
    warnings: list[str] = field(default_factory=list)
    ocr_source: str = "paddleocr"


class PaddleOCREngine:
    """Lazy PaddleOCR adapter. Model is initialized once per process/language."""

    _SUPPORTED_LANGUAGES = {"en", "vi", "ch", "japan", "korean", "fr", "german"}

    def __init__(self, ocr_factory: Callable[[str], object] | None = None) -> None:
        self._ocr_factory = ocr_factory or self._default_factory
        self._engines: dict[str, object] = {}
        self._lock = Lock()

    @staticmethod
    def _default_factory(language: str):
        from paddleocr import PaddleOCR

        return PaddleOCR(lang=language, use_textline_orientation=True, enable_mkldnn=False)

    def _get_engine(self, language_hint: str | None):
        language = (language_hint or "en").strip().lower()
        if language not in self._SUPPORTED_LANGUAGES:
            language = "en"
        with self._lock:
            if language not in self._engines:
                self._engines[language] = self._ocr_factory(language)
            return self._engines[language]

    @staticmethod
    def _from_v3(results) -> list[OCRRegion]:
        regions: list[OCRRegion] = []
        if not isinstance(results, (list, tuple)):
            results = [results]
        for page in results:
            if hasattr(page, "json"):
                page = page.json
            if isinstance(page, dict) and "res" in page:
                page = page["res"]
            if not isinstance(page, dict):
                continue
            texts = page.get("rec_texts") or []
            scores = page.get("rec_scores") or []
            boxes = page.get("rec_polys") or page.get("dt_polys") or []
            for index, text in enumerate(texts):
                if not str(text).strip():
                    continue
                confidence = None
                if index < len(scores):
                    try:
                        confidence = float(scores[index])
                    except (TypeError, ValueError):
                        confidence = None
                box = None
                if index < len(boxes):
                    try:
                        box = [[float(point[0]), float(point[1])] for point in boxes[index]]
                    except (TypeError, ValueError, IndexError):
                        box = None
                regions.append(OCRRegion(str(text), confidence, box))
        return regions

    @staticmethod
    def _from_legacy(results) -> list[OCRRegion]:
        regions: list[OCRRegion] = []
        if not results:
            return regions
        pages = results if isinstance(results, (list, tuple)) else [results]
        for page in pages:
            if not page:
                continue
            for item in page:
                try:
                    box, (text, confidence) = item
                    points = [[float(point[0]), float(point[1])] for point in box]
                    regions.append(OCRRegion(str(text), float(confidence), points))
                except (TypeError, ValueError, IndexError):
                    continue
        return regions

    def extract(self, image_path: Path, language_hint: str | None = None) -> OCRResult:
        engine = self._get_engine(language_hint)
        warnings: list[str] = []
        if language_hint and language_hint.strip().lower() not in self._SUPPORTED_LANGUAGES:
            warnings.append("Unsupported OCR language hint; English model was used.")
        if hasattr(engine, "predict"):
            result = engine.predict(str(image_path))
            regions = self._from_v3(result)
        else:
            result = engine.ocr(str(image_path), cls=True)
            regions = self._from_legacy(result)
        text = "\n".join(region.text for region in regions)
        if not text.strip():
            warnings.append("No readable text was extracted.")
        return OCRResult(text=text, regions=regions, warnings=warnings)
