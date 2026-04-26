from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from threading import Lock

from PIL import Image
from ultralytics import YOLO

from app.core.config import get_settings


@dataclass(slots=True)
class LoadedModel:
    path: str
    version: str
    names: dict[str, str]
    model: YOLO


class ModelRuntime:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._lock = Lock()
        self._violation_model: LoadedModel | None = None
        self._plate_model: LoadedModel | None = None

    def _version(self, path: Path) -> str:
        stat = path.stat()
        return f"{path.name}:{int(stat.st_mtime)}"

    def _load(self, path_str: str) -> LoadedModel:
        path = Path(path_str)
        model = YOLO(str(path))
        return LoadedModel(
            path=str(path),
            version=self._version(path),
            names={str(key): str(value) for key, value in model.names.items()},
            model=model,
        )

    def warmup(self) -> dict[str, dict]:
        with self._lock:
            if self._violation_model is None:
                self._violation_model = self._load(self.settings.violation_model_path)
            if self._plate_model is None:
                self._plate_model = self._load(self.settings.plate_model_path)
        return {
            "violation_detection": {
                "version": self._violation_model.version,
                "names": self._violation_model.names,
            },
            "plate_detection": {
                "version": self._plate_model.version,
                "names": self._plate_model.names,
            },
        }

    @property
    def violation_model(self) -> LoadedModel:
        self.warmup()
        assert self._violation_model is not None
        return self._violation_model

    @property
    def plate_model(self) -> LoadedModel:
        self.warmup()
        assert self._plate_model is not None
        return self._plate_model

    def detect_violations(self, image: Image.Image, *, max_det: int) -> list[dict]:
        result = self.violation_model.model.predict(image, verbose=False, max_det=max_det, conf=0.01)[0]
        detections: list[dict] = []
        for box in result.boxes:
            cls_index = int(box.cls.item())
            label = self.violation_model.names[str(cls_index)]
            bbox = [float(value) for value in box.xyxy[0].tolist()]
            detections.append(
                {
                    "label": label,
                    "confidence": float(box.conf.item()),
                    "bbox": bbox,
                }
            )
        return detections

    def detect_plate_tokens(self, image: Image.Image) -> list[dict]:
        result = self.plate_model.model.predict(image, verbose=False, max_det=24, conf=0.01)[0]
        detections: list[dict] = []
        for box in result.boxes:
            cls_index = int(box.cls.item())
            label = self.plate_model.names[str(cls_index)]
            bbox = [float(value) for value in box.xyxy[0].tolist()]
            detections.append(
                {
                    "label": label,
                    "confidence": float(box.conf.item()),
                    "bbox": bbox,
                }
            )
        return detections


runtime = ModelRuntime()
