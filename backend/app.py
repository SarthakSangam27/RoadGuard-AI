from flask import Flask, request, jsonify
from flask_cors import CORS

from pathlib import Path
from PIL import Image
import numpy as np
import time
import uuid

import tensorflow as tf
from ultralytics import YOLO


# ============================================================
# APP
# ============================================================

app = Flask(__name__)

CORS(app)

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# PATHS
# ============================================================

VGG19_PATH = (
    BASE_DIR
    / "saved_models"
    / "vgg19_best.keras"
)

YOLO_PATH = (
    BASE_DIR
    / "runs"
    / "detect"
    / "runs"
    / "detect"
    / "roadguard_yolov8-5"
    / "weights"
    / "best.pt"
)

UPLOAD_DIR = (
    BASE_DIR
    / "uploads"
)

UPLOAD_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# LAZY MODEL LOADING
# ============================================================

# Models are intentionally NOT loaded when the Flask application starts.
# This allows Gunicorn/Render to open the HTTP port quickly.
# The models are loaded only when /api/scan actually needs them.

vgg19_model = None
yolo_model = None


def get_vgg19_model():

    global vgg19_model

    if vgg19_model is None:

        print()
        print("Loading VGG19...")
        print(f"Model path: {VGG19_PATH}")

        vgg19_model = tf.keras.models.load_model(
            VGG19_PATH
        )

        print("VGG19 loaded successfully.")

    return vgg19_model


def get_yolo_model():

    global yolo_model

    if yolo_model is None:

        print()
        print("Loading YOLOv8...")
        print(f"Model path: {YOLO_PATH}")

        yolo_model = YOLO(
            str(YOLO_PATH)
        )

        print("YOLOv8 loaded successfully.")

    return yolo_model


# ============================================================
# HEALTH CHECK
# ============================================================

@app.route(
    "/api/health",
    methods=["GET"]
)
def health():

    return jsonify({
        "status": "ok",
        "vgg19": vgg19_model is not None,
        "yolov8": yolo_model is not None
    })


# ============================================================
# VGG19 PREDICTION
# ============================================================

def predict_vgg19(image):

    image = image.convert(
        "RGB"
    )

    image = image.resize(
        (224, 224)
    )

    image_array = np.array(
        image,
        dtype=np.float32
    )

    image_array = np.expand_dims(
        image_array,
        axis=0
    )

    # VGG19 ImageNet preprocessing
    image_array = tf.keras.applications.vgg19.preprocess_input(
        image_array
    )

    model = get_vgg19_model()

    prediction = model.predict(
        image_array,
        verbose=0
    )

    confidence = float(
        prediction[0][0]
    )

    if confidence >= 0.5:

        label = "pothole"

        pothole_confidence = confidence

    else:

        label = "no_pothole"

        pothole_confidence = (
            1.0 - confidence
        )

    return {
        "label": label,
        "confidence": float(
            pothole_confidence
        )
    }


# ============================================================
# YOLOv8 PREDICTION
# ============================================================

def predict_yolov8(
    image_path
):

    model = get_yolo_model()

    results = model.predict(
        source=str(image_path),
        conf=0.50,
        iou=0.50,
        verbose=False
    )

    detections = []

    if not results:

        return detections

    result = results[0]

    if result.boxes is None:

        return detections

    image_width = (
        result.orig_shape[1]
    )

    image_height = (
        result.orig_shape[0]
    )

    for box in result.boxes:

        confidence = float(
            box.conf[0]
        )

        class_id = int(
            box.cls[0]
        )

        # Only pothole class
        if class_id != 0:
            continue

        x1, y1, x2, y2 = (
            box.xyxy[0]
            .cpu()
            .numpy()
        )

        width = (
            x2 - x1
        )

        height = (
            y2 - y1
        )

        detections.append({

            "confidence": confidence,

            "class_id": class_id,

            "bboxPct": {

                "x": float(
                    x1 / image_width
                ),

                "y": float(
                    y1 / image_height
                ),

                "w": float(
                    width / image_width
                ),

                "h": float(
                    height / image_height
                )
            }
        })

    return detections


# ============================================================
# SCAN API
# ============================================================

@app.route(
    "/api/scan",
    methods=["POST"]
)
def scan():

    start_time = time.time()

    try:

        # ----------------------------------------------------
        # Check file
        # ----------------------------------------------------

        if "image" not in request.files:

            return jsonify({
                "error": "No image was provided."
            }), 400

        uploaded_file = (
            request.files["image"]
        )

        if not uploaded_file.filename:

            return jsonify({
                "error": "Invalid image filename."
            }), 400


        # ----------------------------------------------------
        # Save temporary image
        # ----------------------------------------------------

        extension = (
            Path(
                uploaded_file.filename
            ).suffix.lower()
        )

        if extension not in [
            ".jpg",
            ".jpeg",
            ".png",
            ".webp",
            ".bmp"
        ]:

            return jsonify({
                "error":
                    "Unsupported image format."
            }), 400


        filename = (
            f"{uuid.uuid4().hex}"
            f"{extension}"
        )

        image_path = (
            UPLOAD_DIR
            / filename
        )

        uploaded_file.save(
            image_path
        )


        # ----------------------------------------------------
        # Open image
        # ----------------------------------------------------

        image = Image.open(
            image_path
        )


        # ----------------------------------------------------
        # VGG19
        # ----------------------------------------------------

        vgg_result = (
            predict_vgg19(
                image
            )
        )


        # ----------------------------------------------------
        # YOLOv8
        # ----------------------------------------------------

        yolo_detections = (
            predict_yolov8(
                image_path
            )
        )


        # ----------------------------------------------------
        # Final verdict
        # ----------------------------------------------------

        pothole_detected = (

            vgg_result["label"]
            == "pothole"

            or

            len(yolo_detections) > 0
        )


        # ----------------------------------------------------
        # Highest YOLO confidence
        # ----------------------------------------------------

        if yolo_detections:

            highest_yolo_confidence = max(
                item["confidence"]
                for item in yolo_detections
            )

        else:

            highest_yolo_confidence = 0.0


        # ----------------------------------------------------
        # Processing time
        # ----------------------------------------------------

        processing_time = (
            time.time()
            - start_time
        )


        # ----------------------------------------------------
        # Response
        # ----------------------------------------------------

        response = {

            "success": True,

            "pothole_detected":
                pothole_detected,

            "vgg19": {

                "label":
                    vgg_result["label"],

                "confidence":
                    vgg_result["confidence"]
            },

            "yolov8": {

                "num_detections":
                    len(yolo_detections),

                "highest_confidence":
                    highest_yolo_confidence,

                "detections":
                    yolo_detections
            },

            "processing_time_sec":
                round(
                    processing_time,
                    2
                )
        }


        # ----------------------------------------------------
        # Delete temporary file
        # ----------------------------------------------------

        try:

            image_path.unlink()

        except Exception:

            pass


        return jsonify(
            response
        )


    except Exception as error:

        print(
            "\nDetection error:"
        )

        print(error)

        return jsonify({

            "success": False,

            "error":
                str(error)

        }), 500


# ============================================================
# ROOT
# ============================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({

        "application":
            "RoadGuard-AI",

        "status":
            "running",

        "message":
            "Pothole detection API is running."
    })


# ============================================================
# RUN
# ============================================================

if __name__ == "__main__":

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=True
    )