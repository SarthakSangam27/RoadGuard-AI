from ultralytics import YOLO
from pathlib import Path

data = Path("data/roadguard_detection/data.yaml").resolve()

model = YOLO("yolo11n.pt")

model.train(
    data=str(data),
    epochs=3,
    imgsz=320,
    batch=2,
    device="cpu",
    workers=0,
    project="runs/roadguard_detection",
    name="pothole_baseline",
    exist_ok=True,
    plots=True
)
