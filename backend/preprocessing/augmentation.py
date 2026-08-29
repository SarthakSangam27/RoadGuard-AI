from pathlib import Path

import cv2
import numpy as np


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

SOURCE_DIR = (
    BASE_DIR
    / "data"
    / "processed"
    / "train"
)

OUTPUT_DIR = (
    BASE_DIR
    / "data"
    / "augmented"
    / "train"
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
# AUGMENTATION FUNCTIONS
# ============================================================

def horizontal_flip(image):

    return cv2.flip(
        image,
        1
    )


def brightness_change(image):

    factor = np.random.uniform(
        0.8,
        1.2
    )

    result = (
        image.astype(
            np.float32
        )
        * factor
    )

    return np.clip(
        result,
        0,
        255
    ).astype(
        np.uint8
    )


def rotation(image):

    height, width = (
        image.shape[:2]
    )

    angle = np.random.uniform(
        -10,
        10
    )

    center = (
        width / 2,
        height / 2
    )

    matrix = cv2.getRotationMatrix2D(
        center,
        angle,
        1.0
    )

    return cv2.warpAffine(
        image,
        matrix,
        (width, height),
        borderMode=cv2.BORDER_REFLECT
    )


# ============================================================
# PROCESS CLASS
# ============================================================

def augment_class(
    class_name
):

    source_dir = (
        SOURCE_DIR
        / class_name
    )

    output_dir = (
        OUTPUT_DIR
        / class_name
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    if not source_dir.exists():

        raise FileNotFoundError(
            f"Missing directory:\n"
            f"{source_dir}"
        )

    images = [
        image
        for image in source_dir.iterdir()
        if (
            image.is_file()
            and image.suffix.lower()
            in IMAGE_EXTENSIONS
        )
    ]

    total = 0

    for image_path in images:

        image = cv2.imread(
            str(image_path)
        )

        if image is None:

            print(
                f"Skipping invalid image: "
                f"{image_path}"
            )

            continue

        stem = image_path.stem

        extension = (
            image_path.suffix
        )

        # ----------------------------------------------------
        # Original
        # ----------------------------------------------------

        cv2.imwrite(
            str(
                output_dir
                / f"{stem}_original{extension}"
            ),
            image
        )

        # ----------------------------------------------------
        # Horizontal flip
        # ----------------------------------------------------

        flipped = (
            horizontal_flip(
                image
            )
        )

        cv2.imwrite(
            str(
                output_dir
                / f"{stem}_flip{extension}"
            ),
            flipped
        )

        # ----------------------------------------------------
        # Brightness
        # ----------------------------------------------------

        bright = (
            brightness_change(
                image
            )
        )

        cv2.imwrite(
            str(
                output_dir
                / f"{stem}_bright{extension}"
            ),
            bright
        )

        # ----------------------------------------------------
        # Rotation
        # ----------------------------------------------------

        rotated = (
            rotation(
                image
            )
        )

        cv2.imwrite(
            str(
                output_dir
                / f"{stem}_rotate{extension}"
            ),
            rotated
        )

        total += 4

    return total


# ============================================================
# MAIN
# ============================================================

def main():

    print()
    print("=" * 60)
    print("ROADGUARD-AI — TRAINING AUGMENTATION")
    print("=" * 60)

    total = 0

    for class_name in [
        "pothole",
        "no_pothole",
    ]:

        count = augment_class(
            class_name
        )

        print(
            f"{class_name:12} : "
            f"{count} images"
        )

        total += count

    print()
    print(
        f"Total augmented training "
        f"images: {total}"
    )

    print()
    print(
        f"Output:\n{OUTPUT_DIR}"
    )


if __name__ == "__main__":

    main()