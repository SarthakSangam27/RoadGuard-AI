from pathlib import Path
from PIL import Image, ImageDraw

base = Path.home() / "Downloads" / "YOLOv8 dataset"
stem = "img-104_jpg.rf.687b8858a9a79e92ea4b11024eafee62"

image_path = base / "valid" / "images" / f"{stem}.jpg"
label_path = base / "valid" / "labels" / f"{stem}.txt"

if not image_path.exists():
    raise FileNotFoundError(f"Image not found: {image_path}")
if not label_path.exists():
    raise FileNotFoundError(f"Label not found: {label_path}")

image = Image.open(image_path).convert("RGB")
draw = ImageDraw.Draw(image, "RGBA")
w, h = image.size

for line in label_path.read_text().splitlines():
    vals = line.split()
    if not vals:
        continue
    coords = [float(v) for v in vals[1:]]
    if len(coords) < 6 or len(coords) % 2:
        print("Skipping invalid polygon:", line)
        continue
    points = [(coords[i] * w, coords[i + 1] * h)
              for i in range(0, len(coords), 2)]
    draw.polygon(points, fill=(255, 0, 0, 75),
                 outline=(255, 0, 0, 255), width=3)

output = Path.cwd() / "validation_ground_truth.jpg"
image.save(output, quality=95)
print("Image size:", image.size)
print("Label contents:")
print(label_path.read_text())
print("Saved overlay:", output)
