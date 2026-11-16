from pathlib import Path
from threading import Lock
import base64
import time

import cv2
import numpy as np
from ultralytics import YOLO


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT = Path(__file__).resolve().parents[2]

YOLO_MODEL_PATH = BASE_DIR / "models" / "pothole_best.pt"
VGG19_MODEL_PATH = (
    PROJECT_ROOT
    / "runs"
    / "vgg19"
    / "roadguard_vgg19"
    / "best_vgg19_finetuned.keras"
)

VGG19_IMAGE_SIZE = (224, 224)

_yolo_model = None
_vgg19_model = None
_yolo_lock = Lock()
_vgg19_lock = Lock()


def get_model():
    """Load YOLOv8 once, on the first scan request."""
    global _yolo_model

    with _yolo_lock:
        if _yolo_model is None:
            if not YOLO_MODEL_PATH.is_file():
                raise FileNotFoundError(
                    f"YOLOv8 weights not found: {YOLO_MODEL_PATH}"
                )
            _yolo_model = YOLO(str(YOLO_MODEL_PATH))

        return _yolo_model


def get_vgg19_model():
    """Load the trained Keras VGG19 classifier once."""
    global _vgg19_model

    with _vgg19_lock:
        if _vgg19_model is None:
            if not VGG19_MODEL_PATH.is_file():
                raise FileNotFoundError(
                    f"VGG19 weights not found: {VGG19_MODEL_PATH}"
                )

            try:
                from tensorflow.keras.models import load_model
            except ImportError as error:
                raise RuntimeError(
                    "TensorFlow is required to run the VGG19 classifier."
                ) from error

            _vgg19_model = load_model(
                str(VGG19_MODEL_PATH),
                compile=False
            )

        return _vgg19_model


def _predict_vgg19(image):
    """
    Run binary VGG19 classification.

    The trained model includes VGG19 preprocess_input in its own graph.
    Therefore, this function passes RGB float32 pixels in the [0, 255]
    range and must NOT preprocess them a second time.
    """
    model = get_vgg19_model()
    started = time.perf_counter()

    resized = cv2.resize(image, VGG19_IMAGE_SIZE)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB)
    batch = np.expand_dims(rgb.astype(np.float32), axis=0)

    prediction = np.asarray(model.predict(batch, verbose=0))
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    if prediction.size == 0:
        raise RuntimeError("VGG19 returned an empty prediction.")

    flat = prediction.reshape(-1)

    if flat.size == 1:
        pothole_probability = float(np.clip(flat[0], 0.0, 1.0))
    elif flat.size == 2:
        probabilities = np.clip(flat, 0.0, 1.0)
        total = float(probabilities.sum())
        if total > 0:
            probabilities = probabilities / total
        pothole_probability = float(probabilities[1])
    else:
        raise RuntimeError(
            "Unsupported VGG19 output shape. Expected one sigmoid value "
            "or two class probabilities."
        )

    label = "pothole" if pothole_probability >= 0.5 else "no_pothole"
    confidence = (
        pothole_probability
        if label == "pothole"
        else 1.0 - pothole_probability
    )

    return {
        "label": label,
        "confidence": round(confidence, 4),
        "pothole_probability": round(pothole_probability, 4),
        "inference_time_ms": round(elapsed_ms, 2),
    }


def _predict_yolov8(image, confidence=0.25):
    """Run YOLOv8 detection and return boxes plus an annotated image."""
    model = get_model()

    started = time.perf_counter()
    results = model.predict(
        source=image,
        imgsz=320,
        conf=confidence,
        device="cpu",
        verbose=False,
    )
    elapsed_ms = (time.perf_counter() - started) * 1000.0

    if not results:
        raise RuntimeError("YOLOv8 returned no prediction result.")

    result = results[0]
    detections = []

    if result.boxes is not None:
        for box in result.boxes:
            x1, y1, x2, y2 = box.xyxy[0].cpu().tolist()
            detections.append(
                {
                    "class": "pothole",
                    "confidence": round(float(box.conf[0]), 4),
                    "box": {
                        "x1": round(x1, 2),
                        "y1": round(y1, 2),
                        "x2": round(x2, 2),
                        "y2": round(y2, 2),
                    },
                    "bboxPct": {
                        "x": round((x1 / image.shape[1]) * 100, 2),
                        "y": round((y1 / image.shape[0]) * 100, 2),
                        "width": round(
                            ((x2 - x1) / image.shape[1]) * 100, 2
                        ),
                        "height": round(
                            ((y2 - y1) / image.shape[0]) * 100, 2
                        ),
                    },
                }
            )

    annotated = result.plot()
    ok, buffer = cv2.imencode(".jpg", annotated)
    if not ok:
        raise RuntimeError("Could not encode the annotated image.")

    image_base64 = base64.b64encode(buffer.tobytes()).decode("ascii")
    highest_confidence = max(
        (item["confidence"] for item in detections),
        default=0.0,
    )

    return {
        "num_detections": len(detections),
        "highest_confidence": round(highest_confidence, 4),
        "detections": detections,
        "inference_time_ms": round(elapsed_ms, 2),
        "annotated_image": f"data:image/jpeg;base64,{image_base64}",
    }


def scan_image(image_bytes, confidence=0.25):
    """
    Run YOLOv8 detection and VGG19 classification on the same image.

    YOLOv8 remains the primary detector. VGG19 is returned as a separate
    comparison result and does not override YOLO's detection verdict.
    """
    total_started = time.perf_counter()

    encoded = np.frombuffer(image_bytes, dtype=np.uint8)
    image = cv2.imdecode(encoded, cv2.IMREAD_COLOR)

    if image is None:
        raise ValueError("The uploaded file is not a valid image.")

    yolo_result = _predict_yolov8(image, confidence=confidence)
    vgg_result = _predict_vgg19(image)

    total_ms = (time.perf_counter() - total_started) * 1000.0
    detections = yolo_result["detections"]

    return {
        "success": True,
        "comparison_available": True,
        "image_width": int(image.shape[1]),
        "image_height": int(image.shape[0]),
        "pothole_detected": yolo_result["num_detections"] > 0,
        "detection_count": yolo_result["num_detections"],
        "detections": detections,
        "annotated_image": yolo_result["annotated_image"],
        "yolov8": yolo_result,
        "vgg19": vgg_result,
        "processing_time_ms": round(total_ms, 2),
        "processing_time_sec": round(total_ms / 1000.0, 3),
    }
