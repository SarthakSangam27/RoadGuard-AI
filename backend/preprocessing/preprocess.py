from pathlib import Path
import shutil


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_DIR = (
    BASE_DIR
    / "data"
    / "split"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "processed"
)


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}


# ============================================================
# CREATE DIRECTORIES
# ============================================================

def create_directories():

    for split in [
        "train",
        "val",
        "test",
    ]:

        for class_name in [
            "pothole",
            "no_pothole",
        ]:

            (
                OUTPUT_DIR
                / split
                / class_name
            ).mkdir(
                parents=True,
                exist_ok=True
            )


# ============================================================
# VALIDATE IMAGE
# ============================================================

def is_valid_image(path):

    return (
        path.is_file()
        and path.suffix.lower()
        in IMAGE_EXTENSIONS
    )


# ============================================================
# COPY DATASET
# ============================================================

def process_split(split):

    source_split = (
        SOURCE_DIR / split
    )

    output_split = (
        OUTPUT_DIR / split
    )

    if not source_split.exists():

        raise FileNotFoundError(
            f"Missing split directory:\n"
            f"{source_split}"
        )

    total = 0

    for class_name in [
        "pothole",
        "no_pothole",
    ]:

        source_class = (
            source_split
            / class_name
        )

        output_class = (
            output_split
            / class_name
        )

        if not source_class.exists():

            raise FileNotFoundError(
                f"Missing class directory:\n"
                f"{source_class}"
            )

        for image in source_class.iterdir():

            if not is_valid_image(
                image
            ):
                continue

            destination = (
                output_class
                / image.name
            )

            shutil.copy2(
                image,
                destination
            )

            total += 1

    return total


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("ROADGUARD-AI — VGG19 PREPROCESSING")
    print("=" * 60)

    create_directories()

    total_images = 0

    for split in [
        "train",
        "val",
        "test",
    ]:

        count = process_split(
            split
        )

        total_images += count

        print(
            f"{split.upper():5} : "
            f"{count} images"
        )

    print()
    print(
        f"TOTAL : {total_images} images"
    )

    print()
    print(
        f"Processed dataset:\n"
        f"{OUTPUT_DIR}"
    )

    print()
    print(
        "Preprocessing completed."
    )


if __name__ == "__main__":
    main()