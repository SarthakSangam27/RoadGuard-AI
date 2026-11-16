from pathlib import Path
from ultralytics import YOLO

base = Path.home() / "Downloads" / "YOLOv8 dataset"
image_path = next((base / "test" / "images").glob("*.jpg"), None)

if image_path is None:
    raise FileNotFoundError("No JPG image found in the test images folder.")

model = YOLO("yolo11n-seg.pt")
results = model.predict(
    source=str(image_path),
    device="cpu",
    imgsz=416,
    save=True,
    verbose=False
)

result = results[0]
print("Input image:", image_path.name)
print("Inference completed.")
print("Detected objects:", len(result.boxes))
print("Output folder:", result.save_dir)
