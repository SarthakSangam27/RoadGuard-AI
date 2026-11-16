
from pathlib import Path
from ultralytics import YOLO
import json

MODEL_PATH = Path(
    "runs/detect/runs/roadguard_detection/"
    "pothole_finetune_10/weights/best.pt"
)

DATA_YAML = Path("data/roadguard_detection/data.yaml")

OUTPUT_DIR = Path("runs/detect/roadguard_yolo_test_eval")

if not MODEL_PATH.exists():
    raise FileNotFoundError(MODEL_PATH)

if not DATA_YAML.exists():
    raise FileNotFoundError(DATA_YAML)

print("Loading trained YOLOv8 model...")
model = YOLO(str(MODEL_PATH))

print("\nEvaluating on untouched TEST dataset...")

metrics = model.val(
    data=str(DATA_YAML),
    split="test",
    imgsz=640,
    batch=2,
    device="cpu",
    plots=True,
    project=str(OUTPUT_DIR.parent),
    name=OUTPUT_DIR.name,
    exist_ok=True
)

results = {
    "model": "YOLOv8 Fine-tuned",
    "evaluation_split": "test",
    "precision": float(metrics.box.mp),
    "recall": float(metrics.box.mr),
    "mAP50": float(metrics.box.map50),
    "mAP50_95": float(metrics.box.map),
    "F1": float(metrics.box.f1.mean())
}

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

with open(OUTPUT_DIR / "yolo_test_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("\n========== FINAL YOLOv8 TEST RESULTS ==========")

for key, value in results.items():
    if isinstance(value, float):
        print(f"{key}: {value:.4f}")
    else:
        print(f"{key}: {value}")

print("\nResults saved successfully!")
