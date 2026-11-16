from pathlib import Path
import shutil

source = Path.home() / "Downloads" / "YOLOv8 dataset"
destination = Path.cwd() / "data" / "roadguard_detection"

image_extensions = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}
total_images = 0
total_boxes = 0
errors = []

for split in ("train", "valid", "test"):
    source_images = source / split / "images"
    source_labels = source / split / "labels"
    target_images = destination / split / "images"
    target_labels = destination / split / "labels"

    target_images.mkdir(parents=True, exist_ok=True)
    target_labels.mkdir(parents=True, exist_ok=True)

    images_by_stem = {
        p.stem: p for p in source_images.iterdir()
        if p.is_file() and p.suffix.lower() in image_extensions
    }

    for label_file in sorted(source_labels.glob("*.txt")):
        image_file = images_by_stem.get(label_file.stem)

        if image_file is None:
            errors.append(f"Missing image: {split}/{label_file.stem}")
            continue

        boxes = []

        for line_number, line in enumerate(
            label_file.read_text(encoding="utf-8-sig").splitlines(), start=1
        ):
            if not line.strip():
                continue

            try:
                values = [float(x) for x in line.split()]
            except ValueError:
                errors.append(f"Non-numeric label: {label_file.name}:{line_number}")
                continue

            if len(values) < 7 or (len(values) - 1) % 2 != 0:
                errors.append(f"Invalid polygon: {label_file.name}:{line_number}")
                continue

            class_value = values[0]
            coords = values[1:]

            if class_value != 0 or any(x < 0 or x > 1 for x in coords):
                errors.append(f"Invalid class/coordinates: {label_file.name}:{line_number}")
                continue

            xs = coords[0::2]
            ys = coords[1::2]

            xmin, xmax = min(xs), max(xs)
            ymin, ymax = min(ys), max(ys)

            width = xmax - xmin
            height = ymax - ymin

            if width <= 0 or height <= 0:
                errors.append(f"Zero-area box: {label_file.name}:{line_number}")
                continue

            center_x = (xmin + xmax) / 2
            center_y = (ymin + ymax) / 2

            boxes.append(
                f"0 {center_x:.8f} {center_y:.8f} "
                f"{width:.8f} {height:.8f}"
            )

        shutil.copy2(
            image_file,
            target_images / image_file.name
        )

        (target_labels / label_file.name).write_text(
            "\n".join(boxes) + ("\n" if boxes else ""),
            encoding="utf-8"
        )

        total_images += 1
        total_boxes += len(boxes)

    print(
        f"{split}: "
        f"{len(list(target_images.iterdir()))} images copied"
    )

yaml_path = destination / "data.yaml"
yaml_path.write_text(
    f"path: {destination.as_posix()}\n"
    "train: train/images\n"
    "val: valid/images\n"
    "test: test/images\n\n"
    "names:\n"
    "  0: pothole\n",
    encoding="utf-8"
)

print("\nConversion finished.")
print("Images processed:", total_images)
print("Bounding boxes generated:", total_boxes)
print("Issues found:", len(errors))
print("Dataset configuration:", yaml_path)

for error in errors[:20]:
    print("ISSUE:", error)

if errors:
    print("Review the issues before training.")
