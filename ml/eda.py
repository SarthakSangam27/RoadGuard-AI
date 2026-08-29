from pathlib import Path
from collections import Counter
from PIL import Image
import json


# ============================================================
# ROADGUARD-AI DATASET EDA
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLASSIFICATION_DIR = PROJECT_ROOT / "ml" / "data" / "raw" / "classification"
DETECTION_DIR = PROJECT_ROOT / "ml" / "data" / "raw" / "detection"

OUTPUT_DIR = PROJECT_ROOT / "ml" / "outputs" / "evaluation"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# Utility
# ============================================================

def get_images(directory):
    """Return all supported image files recursively."""

    if not directory.exists():
        return []

    return [
        path
        for path in directory.rglob("*")
        if path.is_file() and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def inspect_image(image_path):
    """Check whether an image can be opened correctly."""

    try:
        with Image.open(image_path) as image:
            image.verify()

        with Image.open(image_path) as image:
            width, height = image.size
            mode = image.mode

        return {
            "valid": True,
            "width": width,
            "height": height,
            "mode": mode
        }

    except Exception as error:
        return {
            "valid": False,
            "error": str(error)
        }


# ============================================================
# Classification Dataset
# ============================================================

def analyze_classification_dataset():

    print("\n" + "=" * 60)
    print("CLASSIFICATION DATASET ANALYSIS")
    print("=" * 60)

    if not CLASSIFICATION_DIR.exists():
        print(f"ERROR: Dataset directory not found:")
        print(CLASSIFICATION_DIR)
        return {}

    images = get_images(CLASSIFICATION_DIR)

    print(f"\nDataset location:")
    print(CLASSIFICATION_DIR)

    print(f"\nTotal images: {len(images)}")

    # --------------------------------------------------------
    # Detect classes from directory structure
    # --------------------------------------------------------

    class_counter = Counter()

    for image_path in images:

        try:
            relative_path = image_path.relative_to(CLASSIFICATION_DIR)

            if len(relative_path.parts) >= 2:
                class_name = relative_path.parts[0]
            else:
                class_name = "unknown"

            class_counter[class_name] += 1

        except Exception:
            class_counter["unknown"] += 1

    print("\nClass distribution:")

    for class_name, count in class_counter.items():
        print(f"  {class_name}: {count}")

    # --------------------------------------------------------
    # Image analysis
    # --------------------------------------------------------

    width_counter = Counter()
    height_counter = Counter()
    mode_counter = Counter()

    valid_images = 0
    corrupted_images = []

    for index, image_path in enumerate(images, start=1):

        result = inspect_image(image_path)

        if result["valid"]:

            valid_images += 1

            width_counter[result["width"]] += 1
            height_counter[result["height"]] += 1
            mode_counter[result["mode"]] += 1

        else:

            corrupted_images.append({
                "file": str(image_path),
                "error": result["error"]
            })

        if index % 500 == 0:
            print(f"Checked {index}/{len(images)} images...")

    print("\nImage validation:")
    print(f"  Valid images: {valid_images}")
    print(f"  Corrupted images: {len(corrupted_images)}")

    print("\nMost common image widths:")

    for width, count in width_counter.most_common(10):
        print(f"  {width}: {count}")

    print("\nMost common image heights:")

    for height, count in height_counter.most_common(10):
        print(f"  {height}: {count}")

    print("\nImage modes:")

    for mode, count in mode_counter.items():
        print(f"  {mode}: {count}")

    return {
        "dataset": "classification",
        "total_images": len(images),
        "valid_images": valid_images,
        "corrupted_images": len(corrupted_images),
        "classes": dict(class_counter),
        "widths": dict(width_counter),
        "heights": dict(height_counter),
        "modes": dict(mode_counter),
        "corrupted_files": corrupted_images
    }


# ============================================================
# YOLO Dataset
# ============================================================

def analyze_yolo_dataset():

    print("\n" + "=" * 60)
    print("YOLO DETECTION DATASET ANALYSIS")
    print("=" * 60)

    if not DETECTION_DIR.exists():
        print(f"ERROR: Dataset directory not found:")
        print(DETECTION_DIR)
        return {}

    images = get_images(DETECTION_DIR)

    print(f"\nDataset location:")
    print(DETECTION_DIR)

    print(f"\nTotal images: {len(images)}")

    # --------------------------------------------------------
    # Find labels
    # --------------------------------------------------------

    labels = list(DETECTION_DIR.rglob("*.txt"))

    print(f"Total label files: {len(labels)}")

    image_paths = {
        image_path.stem: image_path
        for image_path in images
    }

    label_paths = {
        label_path.stem: label_path
        for label_path in labels
    }

    missing_labels = []
    empty_labels = []
    invalid_labels = []

    class_counter = Counter()

    # --------------------------------------------------------
    # Check labels
    # --------------------------------------------------------

    for image_path in images:

        label_path = label_paths.get(image_path.stem)

        if label_path is None:
            missing_labels.append(str(image_path))
            continue

        try:

            content = label_path.read_text(
                encoding="utf-8"
            ).strip()

            if not content:
                empty_labels.append(str(label_path))
                continue

            lines = content.splitlines()

            for line_number, line in enumerate(lines, start=1):

                values = line.split()

                # OBB format:
                # class x1 y1 x2 y2 x3 y3 x4 y4
                if len(values) != 9:

                    invalid_labels.append({
                        "file": str(label_path),
                        "line": line_number,
                        "reason": (
                            f"Expected 9 values for OBB, "
                            f"found {len(values)}"
                        )
                    })

                    continue

                try:

                    class_id = int(values[0])

                    coordinates = [
                        float(value)
                        for value in values[1:]
                    ]

                    # Coordinates should normally be normalized.
                    if any(
                        coordinate < 0 or coordinate > 1
                        for coordinate in coordinates
                    ):
                        invalid_labels.append({
                            "file": str(label_path),
                            "line": line_number,
                            "reason": "Coordinate outside [0, 1]"
                        })

                    class_counter[class_id] += 1

                except ValueError:

                    invalid_labels.append({
                        "file": str(label_path),
                        "line": line_number,
                        "reason": "Non-numeric label values"
                    })

        except Exception as error:

            invalid_labels.append({
                "file": str(label_path),
                "reason": str(error)
            })

    # --------------------------------------------------------
    # Print results
    # --------------------------------------------------------

    print("\nYOLO validation:")

    print(f"  Images: {len(images)}")
    print(f"  Labels: {len(labels)}")
    print(f"  Missing labels: {len(missing_labels)}")
    print(f"  Empty labels: {len(empty_labels)}")
    print(f"  Invalid labels: {len(invalid_labels)}")

    print("\nYOLO class distribution:")

    for class_id, count in sorted(class_counter.items()):
        print(f"  Class {class_id}: {count} annotations")

    return {
        "dataset": "detection",
        "total_images": len(images),
        "total_labels": len(labels),
        "missing_labels": len(missing_labels),
        "empty_labels": len(empty_labels),
        "invalid_labels": len(invalid_labels),
        "classes": dict(class_counter),
        "missing_label_files": missing_labels,
        "empty_label_files": empty_labels,
        "invalid_label_details": invalid_labels
    }


# ============================================================
# Main
# ============================================================

def main():

    print("\n")
    print("=" * 60)
    print("        ROADGUARD-AI DATASET EDA")
    print("=" * 60)

    classification_results = analyze_classification_dataset()

    detection_results = analyze_yolo_dataset()

    results = {
        "classification": classification_results,
        "detection": detection_results
    }

    output_file = OUTPUT_DIR / "dataset_eda.json"

    with open(
        output_file,
        "w",
        encoding="utf-8"
    ) as file:

        json.dump(
            results,
            file,
            indent=4
        )

    print("\n" + "=" * 60)
    print("EDA COMPLETE")
    print("=" * 60)

    print(f"\nReport saved to:")
    print(output_file)


if __name__ == "__main__":
    main()