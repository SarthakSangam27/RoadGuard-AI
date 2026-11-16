import json
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError
from uuid import uuid4

image_path = next(
    (Path.home() / "Downloads" / "YOLOv8 dataset" / "test" / "images").glob("*.jpg"),
    None
)

if image_path is None:
    raise FileNotFoundError("No test JPG image was found.")

boundary = "----RoadGuardAI" + uuid4().hex
image_bytes = image_path.read_bytes()

body = (
    f"--{boundary}\r\n"
    f'Content-Disposition: form-data; name="image"; filename="{image_path.name}"\r\n'
    "Content-Type: image/jpeg\r\n\r\n"
).encode() + image_bytes + f"\r\n--{boundary}--\r\n".encode()

request = Request(
    "http://127.0.0.1:5000/api/scan",
    data=body,
    headers={"Content-Type": f"multipart/form-data; boundary={boundary}"},
    method="POST"
)

try:
    with urlopen(request, timeout=120) as response:
        result = json.loads(response.read().decode())
except HTTPError as error:
    print("HTTP status:", error.code)
    print(error.read().decode())
    raise

print("Input image:", image_path.name)
print("Image dimensions:", result.get("image_width"), "x", result.get("image_height"))
print("Detection count:", result.get("detection_count"))

for detection in result.get("detections", []):
    print(detection)

annotated = result.get("annotated_image", "")
if annotated.startswith("data:image/jpeg;base64,"):
    import base64
    output = Path.cwd() / "api_scan_result.jpg"
    output.write_bytes(base64.b64decode(annotated.split(",", 1)[1]))
    print("Annotated image saved to:", output)
else:
    print("No annotated image returned.")
