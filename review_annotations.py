from pathlib import Path
from PIL import Image, ImageDraw
import math

base = Path.home() / "Downloads" / "YOLOv8 dataset"
image_dir = base / "train" / "images"
label_dir = base / "train" / "labels"

label_files = sorted(label_dir.glob("*.txt"))[:4]
tiles = []

for label_path in label_files:
    image_path = image_dir / (label_path.stem + ".jpg")
    if not image_path.exists():
        print("Image missing:", image_path.name)
        continue

    image = Image.open(image_path).convert("RGB")
    w, h = image.size
    draw = ImageDraw.Draw(image, "RGBA")

    for line in label_path.read_text().splitlines():
        vals = line.split()
        if len(vals) < 7 or (len(vals) - 1) % 2:
            continue

        coords = [float(x) for x in vals[1:]]
        points = [(coords[i] * w, coords[i + 1] * h)
                  for i in range(0, len(coords), 2)]
        draw.polygon(points, fill=(255, 0, 0, 70),
                     outline=(255, 30, 30, 255), width=3)

    image.thumbnail((480, 320))
    tile = Image.new("RGB", (500, 365), "white")
    tile.paste(image, ((500 - image.width) // 2, 30))
    ImageDraw.Draw(tile).text((10, 8), label_path.stem, fill="black")
    tiles.append(tile)

if not tiles:
    raise RuntimeError("No matching images found.")

sheet = Image.new("RGB", (1000, math.ceil(len(tiles) / 2) * 365), "#dddddd")
for i, tile in enumerate(tiles):
    sheet.paste(tile, ((i % 2) * 500, (i // 2) * 365))

output = Path.cwd() / "roadguard_annotation_review.jpg"
sheet.save(output, quality=92)
print("Saved:", output)
