from pathlib import Path
from collections import Counter

base = Path.home() / "Downloads" / "YOLOv8 dataset"
counts = Counter()
examples = {}

for split in ("train", "valid", "test"):
    for path in (base / split / "labels").glob("*.txt"):
        for line in path.read_text().splitlines():
            values = line.split()
            if not values:
                continue

            coordinate_count = len(values) - 1
            if coordinate_count == 8:
                counts["4-point polygon"] += 1
            elif coordinate_count >= 6 and coordinate_count % 2 == 0:
                counts["other polygon"] += 1
            else:
                counts["invalid format"] += 1

            examples.setdefault(counts.most_common(1)[0][0] if counts else "unknown", path.name)

print("Annotation geometry counts:")
for name, count in counts.items():
    print(f"{name}: {count}")
