from pathlib import Path
import shutil
import argparse
import json


PROJECT_ROOT = Path(__file__).resolve().parents[2]

RAW_DIR = PROJECT_ROOT / "ml" / "data" / "raw" / "classification"
BINARY_DIR = RAW_DIR / "_binary"

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


# ============================================================
# EDIT THIS ONLY AFTER INSPECTING YOUR DATASET
# ============================================================

MANUAL_MAPPING = {
    "pothole": [],
    "no_pothole": []
}


POTHOLE_KEYWORDS = [
    "pothole",
    "potholes",
    "damage",
    "damaged",
    "defect",
    "defects"
]

NO_POTHOLE_KEYWORDS = [
    "normal",
    "clean",
    "clear",
    "good",
    "no_pothole",
    "nopothole"
]


def get_image_count(directory):
    return sum(
        1
        for file in directory.rglob("*")
        if file.is_file()
        and file.suffix.lower() in IMAGE_EXTENSIONS
    )


def scan_dataset():

    if not RAW_DIR.exists():
        raise FileNotFoundError(
            f"Classification dataset not found:\n{RAW_DIR}"
        )

    folders = []

    for directory in RAW_DIR.rglob("*"):

        if not directory.is_dir():
            continue

        if directory == BINARY_DIR:
            continue

        count = get_image_count(directory)

        if count > 0:
            folders.append(
                (directory, count)
            )

    return folders


def guess_class(folder_name):

    name = folder_name.lower()

    if any(
        keyword in name
        for keyword in POTHOLE_KEYWORDS
    ):
        return "pothole"

    if any(
        keyword in name
        for keyword in NO_POTHOLE_KEYWORDS
    ):
        return "no_pothole"

    return "UNCLEAR"


def show_dataset():

    folders = scan_dataset()

    print("\n" + "=" * 70)
    print("ROADGUARD-AI CLASSIFICATION DATASET")
    print("=" * 70)

    if not folders:
        print("No image folders found.")
        return

    for directory, count in folders:

        relative = directory.relative_to(RAW_DIR)

        guess = guess_class(directory.name)

        print(
            f"\nFolder : {relative}"
            f"\nImages : {count}"
            f"\nGuess  : {guess}"
        )

    print("\n" + "=" * 70)
    print("MANUAL MAPPING")
    print("=" * 70)

    print(json.dumps(
        MANUAL_MAPPING,
        indent=4
    ))


def get_manual_mapping():

    mapping = {}

    for class_name, folders in MANUAL_MAPPING.items():

        for folder in folders:

            mapping[folder] = class_name

    return mapping


def copy_images(mapping):

    BINARY_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    copied = {
        "pothole": 0,
        "no_pothole": 0
    }

    for source_folder, target_class in mapping.items():

        source_path = RAW_DIR / source_folder

        if not source_path.exists():

            print(
                f"WARNING: Folder does not exist:"
                f" {source_path}"
            )

            continue

        destination = (
            BINARY_DIR
            / target_class
        )

        destination.mkdir(
            parents=True,
            exist_ok=True
        )

        for image_path in source_path.rglob("*"):

            if not image_path.is_file():
                continue

            if image_path.suffix.lower() not in IMAGE_EXTENSIONS:
                continue

            # Prevent duplicate filenames.
            new_name = (
                f"{source_folder.replace('/', '_').replace(chr(92), '_')}"
                f"_{image_path.name}"
            )

            destination_path = (
                destination
                / new_name
            )

            shutil.copy2(
                image_path,
                destination_path
            )

            copied[target_class] += 1

    print("\n" + "=" * 70)
    print("REMAPPING COMPLETE")
    print("=" * 70)

    print(
        f"Pothole images    : {copied['pothole']}"
    )

    print(
        f"No-pothole images : {copied['no_pothole']}"
    )

    print(
        f"\nOutput:"
        f"\n{BINARY_DIR}"
    )


def main():

    parser = argparse.ArgumentParser()

    parser.add_argument(
        "--scan",
        action="store_true",
        help="Only scan and display dataset structure"
    )

    parser.add_argument(
        "--remap",
        action="store_true",
        help="Create binary classification dataset"
    )

    args = parser.parse_args()

    if not args.scan and not args.remap:

        print(
            "Use one of:"
            "\n"
            "  python ml/preprocessing/remap_classification.py --scan"
            "\n"
            "  python ml/preprocessing/remap_classification.py --remap"
        )

        return

    if args.scan:

        show_dataset()

    if args.remap:

        mapping = get_manual_mapping()

        if not mapping:

            print(
                "\nMANUAL_MAPPING is empty."
                "\nEdit the mapping before using --remap."
            )

            return

        copy_images(mapping)


if __name__ == "__main__":
    main()