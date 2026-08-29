import time


def run_mock_inference(image_path):
    """
    Temporary inference function.

    This is used during Phase 2 while the
    real VGG19 and YOLOv8 models are being
    integrated.

    The function returns the same response
    structure that the real models will use.
    """

    start_time = time.perf_counter()

    # --------------------------------------------------------
    # TEMPORARY MOCK RESULT
    # --------------------------------------------------------

    pothole_detected = True

    vgg19_result = {
        "label": "pothole",
        "confidence": 0.94,
    }

    yolov8_result = {
        "num_detections": 2,

        "detections": [
            {
                "class": "pothole",
                "confidence": 0.92,

                "bboxPct": {
                    "x": 0.43,
                    "y": 0.58,
                    "w": 0.25,
                    "h": 0.20,
                },
            },
            {
                "class": "pothole",
                "confidence": 0.81,

                "bboxPct": {
                    "x": 0.70,
                    "y": 0.66,
                    "w": 0.15,
                    "h": 0.14,
                },
            },
        ],
    }

    processing_time = (
        time.perf_counter() - start_time
    )

    return {
        "pothole_detected": pothole_detected,

        "vgg19": vgg19_result,

        "yolov8": yolov8_result,

        "processing_time_sec": round(
            processing_time,
            3
        ),
    }