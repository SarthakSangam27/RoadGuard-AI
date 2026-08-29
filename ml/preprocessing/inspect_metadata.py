from pathlib import Path
import pandas as pd


PROJECT_ROOT = Path(__file__).resolve().parents[2]

DATASET_DIR = (
    PROJECT_ROOT
    / "ml"
    / "data"
    / "raw"
    / "classification"
)


SUPPORTED_FILES = {
    ".csv",
    ".xlsx",
    ".xls"
}


def find_metadata_files():

    files = []

    for file in DATASET_DIR.rglob("*"):

        if (
            file.is_file()
            and file.suffix.lower() in SUPPORTED_FILES
        ):
            files.append(file)

    return files


def inspect_file(file_path):

    print("\n" + "=" * 80)
    print("FILE")
    print("=" * 80)

    print(file_path.relative_to(DATASET_DIR))

    try:

        if file_path.suffix.lower() == ".csv":

            df = pd.read_csv(
                file_path,
                nrows=5
            )

        else:

            df = pd.read_excel(
                file_path,
                nrows=5
            )

        print("\nColumns:")

        for column in df.columns:
            print(f"  - {column}")

        print("\nFirst rows:")

        print(
            df.to_string(
                index=False
            )
        )

        print("\nTotal columns:", len(df.columns))

    except Exception as error:

        print(
            "\nCould not read file:"
        )

        print(error)


def main():

    print("\n" + "=" * 80)
    print("ROADGUARD-AI IIT GOA METADATA INSPECTOR")
    print("=" * 80)

    print(
        "\nSearching:"
    )

    print(DATASET_DIR)

    files = find_metadata_files()

    print(
        f"\nMetadata files found: {len(files)}"
    )

    if not files:

        print(
            "\nNo CSV/XLS/XLSX files were found."
        )

        return

    for file in files:

        inspect_file(file)

    print("\n" + "=" * 80)
    print("INSPECTION COMPLETE")
    print("=" * 80)


if __name__ == "__main__":
    main()