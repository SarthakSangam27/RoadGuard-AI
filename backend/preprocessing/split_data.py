from pathlib import Path
import random
import shutil


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_DIR = BASE_DIR / "data" / "split"

OUTPUT_DIR = BASE_DIR / "data" / "classification"

# ============================================================
# CONFIGURATION
# ============================================================

TRAIN_RATIO = 0.70
VAL_RATIO = 0.15
TEST_RATIO = 0.15

SEED = 42

IMAGE_EXTENSIONS = {
    ".jpg",
    ".jpeg",
    ".png",
    ".webp",
    ".bmp",
}


# ============================================================
# VALIDATE RATIOS
# ============================================================

if abs(
    TRAIN_RATIO
    + VAL_RATIO
    + TEST_RATIO
    - 1.0
) > 0.001:

    raise ValueError(
        "Train/Val/Test ratios must add up to 1.0"
    )


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

            directory = (
                OUTPUT_DIR
                / split
                / class_name
            )

            directory.mkdir(
                parents=True,
                exist_ok=True
            )


# ============================================================
# GET IMAGES
# ============================================================

def get_images(class_name):

    directory = (
        SOURCE_DIR
        / class_name
    )

    if not directory.exists():

        raise FileNotFoundError(
            f"Class directory not found:\n"
            f"{directory}"
        )

    images = [
        image
        for image in directory.iterdir()
        if (
            image.is_file()
            and image.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    ]

    return images


# ============================================================
# SPLIT IMAGES
# ============================================================

def split_images(images):

    random.shuffle(
        images
    )

    total = len(images)

    train_count = int(
        total * TRAIN_RATIO
    )

    val_count = int(
        total * VAL_RATIO
    )

    train = images[
        :train_count
    ]

    val = images[
        train_count:
        train_count + val_count
    ]

    test = images[
        train_count + val_count:
    ]

    return (
        train,
        val,
        test,
    )


# ============================================================
# COPY IMAGES
# ============================================================

def copy_images(
    images,
    split,
    class_name
):

    destination = (
        OUTPUT_DIR
        / split
        / class_name
    )

    for image in images:

        shutil.copy2(
            image,
            destination
            / image.name
        )


# ============================================================
# PROCESS CLASS
# ============================================================

def process_class(class_name):

    images = get_images(
        class_name
    )

    print()
    print(
        f"{class_name}: "
        f"{len(images)} images"
    )

    (
        train,
        val,
        test,
    ) = split_images(
        images
    )

    copy_images(
        train,
        "train",
        class_name
    )

    copy_images(
        val,
        "val",
        class_name
    )

    copy_images(
        test,
        "test",
        class_name
    )

    print(
        f"  Train : {len(train)}"
    )

    print(
        f"  Val   : {len(val)}"
    )

    print(
        f"  Test  : {len(test)}"
    )

    return (
        len(train),
        len(val),
        len(test),
    )


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 70)
    print("ROADGUARD-AI — VGG19 TRAIN/VAL/TEST SPLIT")
    print("=" * 70)

    random.seed(
        SEED
    )

    create_directories()

    results = {}

    for class_name in [
        "pothole",
        "no_pothole",
    ]:

        results[class_name] = (
            process_class(
                class_name
            )
        )

    # --------------------------------------------------------
    # Overall summary
    # --------------------------------------------------------

    train_total = sum(
        results[class_name][0]
        for class_name in results
    )

    val_total = sum(
        results[class_name][1]
        for class_name in results
    )

    test_total = sum(
        results[class_name][2]
        for class_name in results
    )

    print()
    print("=" * 70)
    print("FINAL SUMMARY")
    print("=" * 70)

    print(
        f"TRAIN : {train_total}"
    )

    print(
        f"VAL   : {val_total}"
    )

    print(
        f"TEST  : {test_total}"
    )

    print(
        f"TOTAL : "
        f"{train_total + val_total + test_total}"
    )

    print()
    print(
        f"Output directory:\n"
        f"{OUTPUT_DIR}"
    )

    print()
    print(
        "VGG19 dataset split completed."
    )


if __name__ == "__main__":

    main()