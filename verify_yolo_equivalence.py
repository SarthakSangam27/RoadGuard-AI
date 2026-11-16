
from ultralytics import YOLO
from pathlib import Path
import numpy as np

PT_PATH = "runs/detect/runs/roadguard_detection/pothole_finetune_10/weights/best.pt"
ONNX_PATH = "runs/detect/runs/roadguard_detection/pothole_finetune_10/weights/best.onnx"

TEST_DIR = Path("data/roadguard_detection/test/images")

pt_model = YOLO(PT_PATH)
onnx_model = YOLO(ONNX_PATH)

images = sorted(TEST_DIR.glob("*"))[:10]

def box_iou(a, b):
    x1 = max(a[0], b[0])
    y1 = max(a[1], b[1])
    x2 = min(a[2], b[2])
    y2 = min(a[3], b[3])

    intersection = max(0, x2-x1) * max(0, y2-y1)
    area_a = max(0, a[2]-a[0]) * max(0, a[3]-a[1])
    area_b = max(0, b[2]-b[0]) * max(0, b[3]-b[1])

    union = area_a + area_b - intersection
    return intersection / union if union else 0

for image in images:
    a = pt_model.predict(str(image), imgsz=640, conf=0.25, verbose=False)[0]
    b = onnx_model.predict(str(image), imgsz=640, conf=0.25, verbose=False)[0]

    boxes_a = a.boxes.xyxy.cpu().numpy()
    boxes_b = b.boxes.xyxy.cpu().numpy()

    scores_a = a.boxes.conf.cpu().numpy()
    scores_b = b.boxes.conf.cpu().numpy()

    if len(boxes_a) != len(boxes_b):
        print(image.name, "COUNT MISMATCH")
        continue

    if len(boxes_a) == 0:
        print(image.name, "PASS - no detections")
        continue

    ious = []
    confidence_diffs = []

    for i in range(len(boxes_a)):
        iou = box_iou(boxes_a[i], boxes_b[i])
        ious.append(iou)
        confidence_diffs.append(abs(scores_a[i] - scores_b[i]))

    print(
        image.name,
        "| detections:", len(boxes_a),
        "| minimum IoU:", round(min(ious), 6),
        "| max confidence difference:", round(max(confidence_diffs), 6)
    )

print("\nVerification completed.")
