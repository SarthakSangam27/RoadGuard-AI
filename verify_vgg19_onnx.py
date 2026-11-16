
import numpy as np
import keras
import onnxruntime as ort
from pathlib import Path

ROOT = Path("runs/vgg19/roadguard_vgg19")

keras_model = keras.models.load_model(
    ROOT / "best_vgg19_finetuned.keras"
)

onnx_session = ort.InferenceSession(
    str(ROOT / "vgg19_roadguard.onnx"),
    providers=["CPUExecutionProvider"]
)

dataset = keras.utils.image_dataset_from_directory(
    "data/vgg19_classification/test",
    image_size=(224, 224),
    batch_size=1,
    shuffle=False
)

input_name = onnx_session.get_inputs()[0].name
output_name = onnx_session.get_outputs()[0].name

max_difference = 0.0

print("\nComparing Keras and ONNX predictions...")

for images, labels in dataset.take(10):
    x = images.numpy().astype(np.float32)

    keras_prediction = keras_model.predict(
        x, verbose=0
    )

    onnx_prediction = onnx_session.run(
        [output_name],
        {input_name: x}
    )[0]

    difference = float(
        np.max(np.abs(keras_prediction - onnx_prediction))
    )

    max_difference = max(max_difference, difference)

    print(
        f"Actual: {labels.numpy()[0]} | "
        f"Keras: {keras_prediction[0][0]:.6f} | "
        f"ONNX: {onnx_prediction[0][0]:.6f} | "
        f"Diff: {difference:.8f}"
    )

print("\nMaximum prediction difference:", max_difference)

if max_difference < 1e-4:
    print("PASS: ONNX predictions match Keras.")
else:
    print("CHECK: Numerical difference needs investigation.")
