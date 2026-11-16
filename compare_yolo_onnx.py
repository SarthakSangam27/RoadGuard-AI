
from ultralytics import YOLO
from pathlib import Path
import numpy as np
import time

PT_PATH = (
    "runs/detect/runs/roadguard_detection/"
    "pothole_finetune_10/weights/best.pt"
)

ONNX_PATH = (
    "runs/detect/runs/roadguard_detection/"
    "pothole_finetune_10/weights/best.onnx"
)

TEST_DIR = Path("data/roadguard_detection/test/images")

pt_model = YOLO(PT_PATH)
onnx_model = YOLO(ONNX_PATH)

images = sorted(TEST_DIR.glob("*"))[:10]

if not images:
    raise FileNotFoundError("No test images found!")

print("\nComparing PyTorch and ONNX predictions...")

for image_path in images:
    pt_result = pt_model.predict(
        str(image_path), imgsz=640, conf=0.25, verbose=False
    )[0]

    onnx_result = onnx_model.predict(
        str(image_path), imgsz=640, conf=0.25, verbose=False
    )[0]

    pt_boxes = pt_result.boxes.xyxy.cpu().numpy()
    onnx_boxes = onnx_result.boxes.xyxy.cpu().numpy()

    print(f"\nImage: {image_path.name}")
    print("PyTorch detections:", len(pt_boxes))
    print("ONNX detections:", len(onnx_boxes))

    if len(pt_boxes) and len(onnx_boxes):
        print("PyTorch first box:", np.round(pt_boxes[0], 2))
        print("ONNX first box:", np.round(onnx_boxes[0], 2))

print("\nComparison completed!")
