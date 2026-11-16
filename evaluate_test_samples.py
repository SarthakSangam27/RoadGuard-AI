from pathlib import Path
from ultralytics import YOLO

root = Path.cwd()
weights = root / "runs" / "segment" / "runs" / "roadguard" / "pothole_baseline" / "weights" / "best.pt"
test_dir = Path.home() / "Downloads" / "YOLOv8 dataset" / "test" / "images"

if not weights.exists():
    raise FileNotFoundError(f"Model not found: {weights}")

images = sorted(test_dir.glob("*.jpg"))[:8]
if not images:
    raise FileNotFoundError(f"No JPG test images found: {test_dir}")

model = YOLO(str(weights))
results = model.predict(
    source=[str(p) for p in images],
    imgsz=320,
    batch=1,
    device="cpu",
    conf=0.25,
    save=True,
    project=str(root / "runs" / "roadguard_eval"),
    name="test_samples",
    exist_ok=True,
    verbose=False
)

for path, result in zip(images, results):
    print(f"{path.name}: {len(result.boxes)} detection(s)")

print("Predictions saved to:", results[0].save_dir)
