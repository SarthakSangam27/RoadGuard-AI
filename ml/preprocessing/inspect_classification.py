from pathlib import Path
from collections import Counter
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "classification"
)

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".bmp",
    ".webp"
}


def get_images():

    return [
        path
        for path in DATASET_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def main():

    print("\n" + "=" * 70)
    print("ROADGUARD-AI CLASSIFICATION DATASET INSPECTOR")
    print("=" * 70)

    if not DATASET_DIR.exists():
        print("\nDataset not found:")
        print(DATASET_DIR)
        return

    images = get_images()

    print(f"\nTotal unique image files found: {len(images)}")

    if not images:
        print("\nNo images found.")
        return

    # --------------------------------------------------------
    # Find the deepest directory containing images
    # --------------------------------------------------------

    directory_counts = Counter(
        image.parent
        for image in images
    )

    print("\nDirectories containing images:")
    print("-" * 70)

    for directory, count in directory_counts.most_common():

        relative = directory.relative_to(
            DATASET_DIR
        )

        print(
            f"{relative}  -->  {count} images"
        )

    # --------------------------------------------------------
    # Filename analysis
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("SAMPLE FILENAMES")
    print("=" * 70)

    for image in images[:30]:

        print(
            image.relative_to(DATASET_DIR)
        )

    # --------------------------------------------------------
    # File extensions
    # --------------------------------------------------------

    extensions = Counter(
        image.suffix.lower()
        for image in images
    )

    print("\n" + "=" * 70)
    print("IMAGE EXTENSIONS")
    print("=" * 70)

    for extension, count in extensions.items():

        print(
            f"{extension}: {count}"
        )

    # --------------------------------------------------------
    # Image dimensions
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("IMAGE DIMENSIONS")
    print("=" * 70)

    dimensions = Counter()

    corrupted = []

    for image_path in images:

        try:

            with Image.open(image_path) as image:

                dimensions[image.size] += 1

        except Exception as error:

            corrupted.append(
                {
                    "file": str(image_path),
                    "error": str(error)
                }
            )

    for dimension, count in dimensions.most_common(20):

        print(
            f"{dimension}: {count}"
        )

    print(
        f"\nCorrupted images: {len(corrupted)}"
    )

    # --------------------------------------------------------
    # Look for possible label/metadata files
    # --------------------------------------------------------

    print("\n" + "=" * 70)
    print("POSSIBLE LABEL / METADATA FILES")
    print("=" * 70)

    metadata_extensions = {
        ".csv",
        ".json",
        ".txt",
        ".xml",
        ".yaml",
        ".yml"
    }

    metadata_files = [
        file
        for file in DATASET_DIR.rglob("*")
        if file.is_file()
        and file.suffix.lower() in metadata_extensions
    ]

    if metadata_files:

        for file in metadata_files:

            print(
                file.relative_to(DATASET_DIR)
            )

    else:

        print(
            "No CSV/JSON/TXT/XML/YAML files found."
        )

    print("\n" + "=" * 70)
    print("INSPECTION COMPLETE")
    print("=" * 70)


if __name__ == "__main__":
    main()