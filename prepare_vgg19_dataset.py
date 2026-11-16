
import csv
import random
from pathlib import Path

import yaml
from PIL import Image

# Project paths
SOURCE = Path("data/roadguard_detection")
OUTPUT = Path("data/vgg19_classification")

SPLITS = ["train", "valid", "test"]
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

random.seed(42)


def load_boxes(label_path, width, height):
    if not label_path.exists():
        raise FileNotFoundError(f"Missing label: {label_path}")

    boxes = []

    for line in label_path.read_text().splitlines():
        if not line.strip():
            continue

        parts = line.split()

        if len(parts) != 5:
            raise ValueError(f"Invalid YOLO annotation: {label_path}")

        class_id = int(float(parts[0]))
        xc, yc, bw, bh = map(float, parts[1:])

        x1 = max(0, int((xc - bw / 2) * width))
        y1 = max(0, int((yc - bh / 2) * height))
        x2 = min(width, int((xc + bw / 2) * width))
        y2 = min(height, int((yc + bh / 2) * height))

        if x2 > x1 and y2 > y1:
            boxes.append((class_id, x1, y1, x2, y2))

    return boxes


def overlaps(a, b):
    return not (
        a[2] <= b[0] or a[0] >= b[2]
        or a[3] <= b[1] or a[1] >= b[3]
    )


def create_background_crop(image, boxes):
    width, height = image.size

    side = min(width, height, max(64, int(min(width, height) * 0.35)))

    if side < 32:
        return None

    protected = []

    for _, x1, y1, x2, y2 in boxes:
        px = max(3, int((x2 - x1) * 0.10))
        py = max(3, int((y2 - y1) * 0.10))

        protected.append((
            max(0, x1 - px),
            max(0, y1 - py),
            min(width, x2 + px),
            min(height, y2 + py)
        ))

    for _ in range(120):
        x = random.randint(0, width - side)
        y = random.randint(0, height - side)

        candidate = (x, y, x + side, y + side)

        if not any(overlaps(candidate, box) for box in protected):
            return image.crop(candidate)

    return None


def main():

    if not (SOURCE / "data.yaml").exists():
        raise FileNotFoundError("YOLO data.yaml not found.")

    if OUTPUT.exists() and any(OUTPUT.iterdir()):
        raise FileExistsError(
            f"{OUTPUT} already contains data. "
            "Use a new output folder rather than overwriting it."
        )

    config = yaml.safe_load(
        (SOURCE / "data.yaml").read_text(encoding="utf-8")
    )

    names = config.get("names", {})

    if isinstance(names, list):
        names = {i: name for i, name in enumerate(names)}

    pothole_ids = {
        int(class_id)
        for class_id, name in names.items()
        if str(name).strip().lower() == "pothole"
    }

    if not pothole_ids:
        raise ValueError(f"Pothole class not found: {names}")

    OUTPUT.mkdir(parents=True, exist_ok=True)

    manifest = []

    totals = {
        split: {"pothole": 0, "background": 0, "skipped": 0}
        for split in SPLITS
    }

    for split in SPLITS:

        image_dir = SOURCE / split / "images"
        label_dir = SOURCE / split / "labels"

        if not image_dir.exists() or not label_dir.exists():
            raise FileNotFoundError(f"Missing folders for {split}")

        for category in ["pothole", "background"]:
            (OUTPUT / split / category).mkdir(
                parents=True, exist_ok=True
            )

        images = sorted(
            p for p in image_dir.iterdir()
            if p.suffix.lower() in IMAGE_EXTENSIONS
        )

        for image_path in images:

            label_path = label_dir / f"{image_path.stem}.txt"

            with Image.open(image_path) as img:
                image = img.convert("RGB")

            width, height = image.size

            boxes = load_boxes(label_path, width, height)

            pothole_boxes = [
                box for box in boxes
                if box[0] in pothole_ids
            ]

            # Positive pothole crops
            for index, box in enumerate(pothole_boxes):

                _, x1, y1, x2, y2 = box

                pad_x = max(2, int((x2 - x1) * 0.15))
                pad_y = max(2, int((y2 - y1) * 0.15))

                x1 = max(0, x1 - pad_x)
                y1 = max(0, y1 - pad_y)
                x2 = min(width, x2 + pad_x)
                y2 = min(height, y2 + pad_y)

                crop = image.crop((x1, y1, x2, y2))

                if crop.width < 8 or crop.height < 8:
                    continue

                filename = f"{image_path.stem}_pothole_{index}.jpg"

                crop.save(
                    OUTPUT / split / "pothole" / filename,
                    quality=95
                )

                totals[split]["pothole"] += 1

                manifest.append([
                    split, "pothole", str(image_path),
                    str(label_path), filename
                ])

            # One candidate background crop per source image
            background = create_background_crop(
                image, pothole_boxes
            )

            if background is not None:

                filename = f"{image_path.stem}_background.jpg"

                background.save(
                    OUTPUT / split / "background" / filename,
                    quality=95
                )

                totals[split]["background"] += 1

                manifest.append([
                    split, "background", str(image_path),
                    str(label_path), filename
                ])

            else:
                totals[split]["skipped"] += 1

    # Save crop provenance
    with open(
        OUTPUT / "manifest.csv",
        "w",
        newline="",
        encoding="utf-8"
    ) as file:

        writer = csv.writer(file)

        writer.writerow([
            "split", "class", "source_image",
            "source_label", "output_file"
        ])

        writer.writerows(manifest)

    print("\nVGG19 dataset preparation complete!")
    print("Original YOLO dataset was not modified.\n")

    for split in SPLITS:
        print(
            f"{split}: "
            f"Pothole={totals[split]['pothole']}, "
            f"Background={totals[split]['background']}, "
            f"Skipped={totals[split]['skipped']}"
        )

    print(f"\nOutput directory: {OUTPUT.resolve()}")
    print("Review background crops before training.")


if __name__ == "__main__":
    main()
