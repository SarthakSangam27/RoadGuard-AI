from pathlib import Path

base = Path("data/roadguard_detection")
checked = 0
issues = []

for split in ("train", "valid", "test"):
    images = list((base / split / "images").glob("*"))
    labels = list((base / split / "labels").glob("*.txt"))

    print(f"{split}: {len(images)} images, {len(labels)} label files")

    for file in labels:
        for line_no, line in enumerate(file.read_text().splitlines(), 1):
            if not line.strip():
                continue

            values = line.split()
            try:
                nums = [float(v) for v in values]
            except ValueError:
                issues.append(f"{file}:{line_no}: non-numeric")
                continue

            checked += 1

            if len(nums) != 5:
                issues.append(f"{file}:{line_no}: expected 5 values")
            elif nums[0] != 0 or any(v < 0 or v > 1 for v in nums[1:]):
                issues.append(f"{file}:{line_no}: invalid class or coordinates")
            elif nums[3] <= 0 or nums[4] <= 0:
                issues.append(f"{file}:{line_no}: invalid box size")

print("\nBounding-box lines checked:", checked)
print("Issues found:", len(issues))
for issue in issues[:10]:
    print(issue)
