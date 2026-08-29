from pathlib import Path
import random

import matplotlib.pyplot as plt
from PIL import Image


PROJECT_ROOT = Path(__file__).resolve().parent.parent

CLASSIFICATION_DIR = (
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

    if not CLASSIFICATION_DIR.exists():
        raise FileNotFoundError(
            f"Dataset not found: {CLASSIFICATION_DIR}"
        )

    return [
        path
        for path in CLASSIFICATION_DIR.rglob("*")
        if path.is_file()
        and path.suffix.lower() in IMAGE_EXTENSIONS
    ]


def main():

    images = get_images()

    if not images:
        print("No images found.")
        return

    sample_size = min(12, len(images))

    selected_images = random.sample(
        images,
        sample_size
    )

    rows = 3
    columns = 4

    fig, axes = plt.subplots(
        rows,
        columns,
        figsize=(14, 10)
    )

    axes = axes.flatten()

    for ax, image_path in zip(
        axes,
        selected_images
    ):

        try:

            image = Image.open(image_path)

            ax.imshow(image)

            relative_path = image_path.relative_to(
                CLASSIFICATION_DIR
            )

            ax.set_title(
                str(relative_path),
                fontsize=8
            )

        except Exception:

            ax.set_title(
                "Invalid image"
            )

        ax.axis("off")

    # Hide unused axes
    for ax in axes[sample_size:]:
        ax.axis("off")

    plt.tight_layout()

    output_dir = (
        PROJECT_ROOT
        / "ml"
        / "outputs"
        / "classification"
    )

    output_dir.mkdir(
        parents=True,
        exist_ok=True
    )

    output_path = (
        output_dir
        / "classification_samples.png"
    )

    plt.savefig(
        output_path,
        dpi=150,
        bbox_inches="tight"
    )

    plt.show()

    print(f"\nSaved visualization to:")
    print(output_path)


if __name__ == "__main__":
    main()