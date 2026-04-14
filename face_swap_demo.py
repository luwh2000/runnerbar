#!/usr/bin/env python3
"""Controlled face swap demo with compliance and risk-control guardrails."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

ALLOWED_SOURCE_NAMES = {"source_face.jpg"}
ALLOWED_TARGET_NAMES = {"target_image.jpg", "target_video.mp4"}
PUBLIC_FIGURE_KEYWORDS = {"obama", "trump", "biden", "musk", "swift", "xi", "putin"}


class FaceSwapError(RuntimeError):
    """Expected runtime validation/processing error."""


@dataclass
class FaceBox:
    x: int
    y: int
    w: int
    h: int


class ControlledFaceSwapDemo:
    def __init__(self, whitelist_dir: Path):
        self.whitelist_dir = whitelist_dir.resolve()
        cascade_path = cv2.data.haarcascades + "haarcascade_frontalface_default.xml"
        self.detector = cv2.CascadeClassifier(cascade_path)
        if self.detector.empty():
            raise FaceSwapError("Failed to initialize face detector.")

    def _assert_whitelisted(self, path: Path, allowed_names: set[str]) -> Path:
        resolved = path.resolve()
        if not resolved.exists():
            raise FaceSwapError(f"Input not found: {path}")

        try:
            resolved.relative_to(self.whitelist_dir)
        except ValueError as exc:
            raise FaceSwapError(
                f"Rejected by risk-control: {path.name} is outside whitelist directory {self.whitelist_dir}"
            ) from exc

        if resolved.name not in allowed_names:
            raise FaceSwapError(
                f"Rejected by risk-control: filename '{resolved.name}' is not in allowed names {sorted(allowed_names)}"
            )

        lowered = resolved.name.lower()
        if any(keyword in lowered for keyword in PUBLIC_FIGURE_KEYWORDS):
            raise FaceSwapError("Rejected by risk-control: possible public-figure material by filename keyword.")
        return resolved

    @staticmethod
    def _sha256(path: Path) -> str:
        h = hashlib.sha256()
        with path.open("rb") as f:
            for chunk in iter(lambda: f.read(8192), b""):
                h.update(chunk)
        return h.hexdigest()

    def _detect_faces(self, frame: np.ndarray) -> List[FaceBox]:
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        faces = self.detector.detectMultiScale(gray, scaleFactor=1.1, minNeighbors=5, minSize=(64, 64))
        return [FaceBox(int(x), int(y), int(w), int(h)) for (x, y, w, h) in faces]

    @staticmethod
    def _largest_face(faces: List[FaceBox]) -> FaceBox:
        return sorted(faces, key=lambda f: f.w * f.h, reverse=True)[0]

    @staticmethod
    def _add_watermark(frame: np.ndarray, text: str = "Demo only / For evaluation") -> np.ndarray:
        overlay = frame.copy()
        cv2.putText(
            overlay,
            text,
            (20, frame.shape[0] - 25),
            cv2.FONT_HERSHEY_SIMPLEX,
            0.8,
            (20, 20, 235),
            2,
            cv2.LINE_AA,
        )
        return cv2.addWeighted(overlay, 0.85, frame, 0.15, 0)

    def _swap_single_frame(self, source_img: np.ndarray, target_img: np.ndarray) -> np.ndarray:
        source_faces = self._detect_faces(source_img)
        target_faces = self._detect_faces(target_img)

        if len(source_faces) != 1:
            raise FaceSwapError(f"Source image must contain exactly 1 face, found {len(source_faces)}.")
        if len(target_faces) != 1:
            raise FaceSwapError(
                f"Target frame must contain exactly 1 face (multi-face blocked by risk-control), found {len(target_faces)}."
            )

        s = self._largest_face(source_faces)
        t = self._largest_face(target_faces)

        src_roi = source_img[s.y : s.y + s.h, s.x : s.x + s.w]
        if src_roi.size == 0:
            raise FaceSwapError("Invalid source face region.")

        resized = cv2.resize(src_roi, (t.w, t.h), interpolation=cv2.INTER_CUBIC)
        mask = np.full((t.h, t.w), 255, dtype=np.uint8)

        output = target_img.copy()
        center = (t.x + t.w // 2, t.y + t.h // 2)
        try:
            output = cv2.seamlessClone(resized, output, mask, center, cv2.NORMAL_CLONE)
        except cv2.error as exc:
            raise FaceSwapError("OpenCV blending failed (possibly extreme pose/angle).") from exc

        return self._add_watermark(output)

    def process(self, source_path: Path, target_path: Path, output_path: Path) -> dict:
        source_path = self._assert_whitelisted(source_path, ALLOWED_SOURCE_NAMES)
        target_path = self._assert_whitelisted(target_path, ALLOWED_TARGET_NAMES)

        source_img = cv2.imread(str(source_path))
        if source_img is None:
            raise FaceSwapError("Could not read source image.")

        is_video = target_path.suffix.lower() == ".mp4"
        output_path.parent.mkdir(parents=True, exist_ok=True)

        if is_video:
            self._process_video(source_img, target_path, output_path)
        else:
            target_img = cv2.imread(str(target_path))
            if target_img is None:
                raise FaceSwapError("Could not read target image.")
            result = self._swap_single_frame(source_img, target_img)
            if not cv2.imwrite(str(output_path), result):
                raise FaceSwapError(f"Failed to write output image: {output_path}")

        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(),
            "source": str(source_path),
            "target": str(target_path),
            "output": str(output_path),
            "source_sha256": self._sha256(source_path),
            "target_sha256": self._sha256(target_path),
            "risk_controls": {
                "whitelist_only": True,
                "fixed_filename_gate": True,
                "public_figure_keyword_block": True,
                "single_face_only": True,
                "visible_watermark": True,
                "metadata_sidecar": True,
            },
        }
        report_path = output_path.with_suffix(output_path.suffix + ".json")
        report_path.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
        return report

    def _process_video(self, source_img: np.ndarray, target_video: Path, output_video: Path) -> None:
        cap = cv2.VideoCapture(str(target_video))
        if not cap.isOpened():
            raise FaceSwapError("Could not open target video.")

        fps = cap.get(cv2.CAP_PROP_FPS) or 24.0
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(str(output_video), fourcc, fps, (width, height))
        if not writer.isOpened():
            cap.release()
            raise FaceSwapError("Could not initialize output video writer.")

        idx = 0
        fail_count = 0
        while True:
            ok, frame = cap.read()
            if not ok:
                break
            idx += 1
            try:
                out = self._swap_single_frame(source_img, frame)
            except FaceSwapError:
                fail_count += 1
                out = self._add_watermark(frame, text="Demo only / swap skipped")
            writer.write(out)

        cap.release()
        writer.release()

        if idx == 0:
            raise FaceSwapError("Target video has no readable frames.")
        if fail_count == idx:
            raise FaceSwapError("Failed on all video frames (no valid single-face frame detected).")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Controlled face swap demo")
    parser.add_argument("--source", default="assets/whitelist/source_face.jpg", help="Source face image path")
    parser.add_argument(
        "--target",
        default="assets/whitelist/target_image.jpg",
        help="Target image/video path",
    )
    parser.add_argument("--output", default="outputs/output.jpg", help="Output path (.jpg or .mp4)")
    parser.add_argument("--whitelist", default="assets/whitelist", help="Whitelist directory")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    app = ControlledFaceSwapDemo(Path(args.whitelist))
    try:
        report = app.process(Path(args.source), Path(args.target), Path(args.output))
    except FaceSwapError as exc:
        print(f"[ERROR] {exc}")
        return 2

    print("[OK] Generated output:", report["output"])
    print("[OK] Sidecar report:", str(Path(report["output"]).with_suffix(Path(report["output"]).suffix + ".json")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
