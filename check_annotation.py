from pathlib import Path
from PIL import Image, ImageDraw

base = Path.home() / "Downloads" / "YOLOv8 dataset"
image_dir = base / "train" / "images"
label_dir = base / "train" / "labels"

image_path = next(
    image_dir.glob("img-100_jpg.rf.233751cac3399aa80b5e58a2afbb753a.jpg"),
    None
)
label_path = label_dir / "img-100_jpg.rf.233751cac3399aa80b5e58a2afbb753a.txt"

if image_path is None:
    raise FileNotFoundError("Could not find the sample image.")
if not label_path.exists():
    raise FileNotFoundError("Could not find the matching label.")

image = Image.open(image_path).convert("RGB")
draw = ImageDraw.Draw(image, "RGBA")
width, height = image.size

for line in label_path.read_text().splitlines():
    values = line.split()
    if not values:
        continue

    class_id = int(values[0])
    coords = [float(v) for v in values[1:]]

    if len(coords) < 6 or len(coords) % 2:
        print("Skipping an invalid polygon line:", line)
        continue

    points = [
        (coords[i] * width, coords[i + 1] * height)
        for i in range(0, len(coords), 2)
    ]

    draw.polygon(points, fill=(255, 40, 40, 80),
                 outline=(255, 40, 40, 255), width=4)

output = Path.cwd() / "pothole_annotation_overlay.jpg"
image.save(output, quality=95)
print("Image size:", image.size)
print("Saved overlay to:", output)
