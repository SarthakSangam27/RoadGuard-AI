from pathlib import Path
from ultralytics import YOLO

data = Path("data/roadguard_detection/data.yaml").resolve()
weights = Path(
    "runs/detect/runs/roadguard_detection/pothole_baseline/weights/best.pt"
)

if not weights.exists():
    # Locate the actual saved weights if Ultralytics used another run folder.
    matches = list(Path("runs").rglob("best.pt"))
    matches = [
        p for p in matches
        if "roadguard_detection" in str(p).lower()
        and "pothole_baseline" in str(p).lower()
    ]
    if not matches:
        raise FileNotFoundError("Could not find detection best.pt")
    weights = matches[0]

print("Using weights:", weights)

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
    name="test_metrics",
    exist_ok=True
)
