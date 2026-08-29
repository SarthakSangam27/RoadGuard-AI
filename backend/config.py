from pathlib import Path
import os


# ============================================================
# ROADGUARD-AI BASE DIRECTORY
# ============================================================

BASE_DIR = Path(__file__).resolve().parent


# ============================================================
# DATA DIRECTORIES
# ============================================================

DATA_DIR = BASE_DIR / "data"

RAW_DATA_DIR = DATA_DIR / "raw"

PROCESSED_DATA_DIR = DATA_DIR / "processed"

AUGMENTED_DATA_DIR = DATA_DIR / "augmented"

SPLIT_DATA_DIR = DATA_DIR / "split"

TRAIN_DATA_DIR = SPLIT_DATA_DIR / "train"

VAL_DATA_DIR = SPLIT_DATA_DIR / "val"

TEST_DATA_DIR = SPLIT_DATA_DIR / "test"


# ============================================================
# MODEL DIRECTORIES
# ============================================================

MODEL_DIR = BASE_DIR / "saved_models"

VGG19_MODEL_PATH = (
    MODEL_DIR / "vgg19_pothole.keras"
)

YOLOV8_MODEL_PATH = (
    MODEL_DIR / "yolov8_pothole.pt"
)


# ============================================================
# STATIC / UPLOAD DIRECTORIES
# ============================================================

STATIC_DIR = BASE_DIR / "static"

UPLOAD_DIR = (
    STATIC_DIR / "uploads"
)

RESULT_DIR = (
    STATIC_DIR / "results"
)


# ============================================================
# OUTPUT DIRECTORY
# ============================================================

OUTPUT_DIR = (
    BASE_DIR / "outputs"
)


# ============================================================
# DATABASE
# ============================================================

DATABASE_PATH = (
    BASE_DIR / "roadguard.db"
)

DATABASE_URL = (
    f"sqlite:///{DATABASE_PATH}"
)


# ============================================================
# FLASK SERVER CONFIGURATION
# ============================================================

HOST = os.getenv(
    "ROADGUARD_HOST",
    "127.0.0.1"
)

PORT = int(
    os.getenv(
        "ROADGUARD_PORT",
        "5000"
    )
)

DEBUG = (
    os.getenv(
        "ROADGUARD_DEBUG",
        "true"
    ).lower()
    == "true"
)


# ============================================================
# CORS CONFIGURATION
# ============================================================

CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]


# ============================================================
# FILE UPLOAD CONFIGURATION
# ============================================================

MAX_FILE_SIZE_MB = 25

MAX_CONTENT_LENGTH = (
    MAX_FILE_SIZE_MB * 1024 * 1024
)


# Supported image formats
ALLOWED_EXTENSIONS = {
    "jpg",
    "jpeg",
    "png",
    "webp",
    "bmp",
}


# ============================================================
# IMAGE CONFIGURATION
# ============================================================

VGG19_IMAGE_WIDTH = 224

VGG19_IMAGE_HEIGHT = 224

VGG19_IMAGE_SIZE = (
    VGG19_IMAGE_WIDTH,
    VGG19_IMAGE_HEIGHT,
)


# ============================================================
# VGG19 CONFIGURATION
# ============================================================

VGG19_CLASS_NAMES = [
    "no_pothole",
    "pothole",
]

VGG19_CONFIDENCE_THRESHOLD = 0.50


# ============================================================
# YOLOv8 CONFIGURATION
# ============================================================

YOLO_CONFIDENCE_THRESHOLD = 0.35

YOLO_IOU_THRESHOLD = 0.45

YOLO_IMAGE_SIZE = 640

YOLO_DEVICE = os.getenv(
    "YOLO_DEVICE",
    "cpu"
)


# ============================================================
# MODEL SETTINGS
# ============================================================

MODEL_FRAMEWORKS = {
    "classifier": "TensorFlow",
    "detector": "Ultralytics YOLOv8",
}


# ============================================================
# API SETTINGS
# ============================================================

API_PREFIX = "/api"

PREDICT_ENDPOINT = (
    f"{API_PREFIX}/predict"
)

HISTORY_ENDPOINT = (
    f"{API_PREFIX}/history"
)


# ============================================================
# REQUIRED DIRECTORIES
# ============================================================

REQUIRED_DIRECTORIES = [
    DATA_DIR,
    RAW_DATA_DIR,
    PROCESSED_DATA_DIR,
    AUGMENTED_DATA_DIR,

    SPLIT_DATA_DIR,
    TRAIN_DATA_DIR,
    VAL_DATA_DIR,
    TEST_DATA_DIR,

    MODEL_DIR,

    STATIC_DIR,
    UPLOAD_DIR,
    RESULT_DIR,

    OUTPUT_DIR,
]


# ============================================================
# DIRECTORY INITIALIZATION
# ============================================================

def create_directories():
    """
    Create all directories required by
    the RoadGuard-AI backend.
    """

    for directory in REQUIRED_DIRECTORIES:

        directory.mkdir(
            parents=True,
            exist_ok=True
        )


# ============================================================
# CONFIGURATION SUMMARY
# ============================================================

def print_config():
    """
    Print the current RoadGuard-AI
    backend configuration.
    """

    print()
    print("=" * 60)
    print("ROADGUARD-AI CONFIGURATION")
    print("=" * 60)

    print(
        f"Base Directory : {BASE_DIR}"
    )

    print(
        f"Data Directory : {DATA_DIR}"
    )

    print(
        f"Model Directory: {MODEL_DIR}"
    )

    print(
        f"Upload Directory: {UPLOAD_DIR}"
    )

    print(
        f"Results Directory: {RESULT_DIR}"
    )

    print(
        f"Database       : {DATABASE_PATH}"
    )

    print(
        f"Server         : http://{HOST}:{PORT}"
    )

    print(
        f"Max Upload     : {MAX_FILE_SIZE_MB} MB"
    )

    print(
        f"YOLO Device    : {YOLO_DEVICE}"
    )

    print(
        f"YOLO Confidence: {YOLO_CONFIDENCE_THRESHOLD}"
    )

    print("=" * 60)
    print()


# ============================================================
# RUN DIRECTLY
# ============================================================

if __name__ == "__main__":

    create_directories()

    print_config()

    print(
        "RoadGuard-AI directories "
        "created successfully."
    )