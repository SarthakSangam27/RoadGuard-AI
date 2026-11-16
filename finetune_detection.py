from pathlib import Path
from ultralytics import YOLO

weights = Path(
    "runs/detect/runs/roadguard_detection/pothole_baseline/weights/best.pt"
).resolve()
data = Path("data/roadguard_detection/data.yaml").resolve()

if not weights.exists():
    raise FileNotFoundError(f"Checkpoint not found: {weights}")

model = YOLO(str(weights))

model.train(
    data=str(data),
    epochs=10,
    imgsz=320,
    batch=2,
    device="cpu",
    workers=0,
    project="runs/roadguard_detection",
    name="pothole_finetune_10",
    exist_ok=True,
    plots=True
)
