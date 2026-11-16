from pathlib import Path
from ultralytics import YOLO

weights = Path(
    "runs/detect/runs/roadguard_detection/pothole_finetune_10/weights/best.pt"
).resolve()
data = Path("data/roadguard_detection/data.yaml").resolve()

if not weights.exists():
    raise FileNotFoundError(f"Checkpoint not found: {weights}")

model = YOLO(str(weights))
model.val(
    data=str(data),
    split="test",
    imgsz=320,
    batch=1,
    device="cpu",
    workers=0,
    plots=True,
    project="runs/roadguard_detection_eval",
    name="finetuned_test",
    exist_ok=True
)
