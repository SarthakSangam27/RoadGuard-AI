
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

from pathlib import Path
import tensorflow as tf
import tf2onnx
import onnx
import onnxruntime as ort

MODEL_PATH = Path(
    "runs/vgg19/roadguard_vgg19/best_vgg19_finetuned.keras"
)

OUTPUT_PATH = Path(
    "runs/vgg19/roadguard_vgg19/vgg19_roadguard.onnx"
)

if not MODEL_PATH.exists():
    raise FileNotFoundError(MODEL_PATH)

print("Loading fine-tuned VGG19...")
model = tf.keras.models.load_model(MODEL_PATH)

signature = (
    tf.TensorSpec(
        (None, 224, 224, 3),
        tf.float32,
        name="input"
    ),
)

print("Converting Keras to ONNX...")

model_proto, _ = tf2onnx.convert.from_keras(
    model,
    input_signature=signature,
    opset=17,
    output_path=str(OUTPUT_PATH)
)

print("Checking ONNX model...")
onnx.checker.check_model(model_proto)

print("Testing ONNX Runtime...")
session = ort.InferenceSession(
    str(OUTPUT_PATH),
    providers=["CPUExecutionProvider"]
)

print("Input:", session.get_inputs()[0].shape)
print("Output:", session.get_outputs()[0].shape)

size_mb = OUTPUT_PATH.stat().st_size / (1024 * 1024)

print(f"\nONNX model size: {size_mb:.2f} MB")
print("VGG19 ONNX conversion successful!")
