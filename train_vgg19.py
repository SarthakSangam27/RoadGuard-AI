
import os
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "2"

import csv
import json
import time
from pathlib import Path

import numpy as np
import tensorflow as tf
import keras
import matplotlib.pyplot as plt

from keras import layers
from sklearn.utils.class_weight import compute_class_weight
from sklearn.metrics import (
    confusion_matrix,
    classification_report,
    accuracy_score,
    precision_score,
    recall_score,
    f1_score
)

# --------------------------------------------------
# 1. CONFIGURATION
# --------------------------------------------------

SEED = 42
IMAGE_SIZE = (224, 224)
BATCH_SIZE = 4

INITIAL_EPOCHS = 5
FINE_TUNE_EPOCHS = 3

DATA_DIR = Path("data/vgg19_classification")
OUTPUT_DIR = Path("runs/vgg19/roadguard_vgg19")

MODEL_PATH = OUTPUT_DIR / "best_vgg19.keras"

tf.keras.utils.set_random_seed(SEED)

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

print("TensorFlow:", tf.__version__)
print("Keras:", keras.__version__)
print("Devices:", tf.config.list_physical_devices())


# --------------------------------------------------
# 2. LOAD DATASET
# --------------------------------------------------

print("\nLoading datasets...")

train_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "train",
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=True,
    seed=SEED
)

val_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "valid",
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=False
)

test_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "test",
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=False
)

class_names = train_ds.class_names

print("\nClasses:", class_names)

if class_names != ["background", "pothole"]:
    raise ValueError(
        "Unexpected class order. Expected ['background', 'pothole'], "
        f"got {class_names}"
    )

if len(class_names) != 2:
    raise ValueError("This script requires exactly two classes.")

# Avoid caching all images in RAM on the 8 GB laptop.
AUTOTUNE = tf.data.AUTOTUNE

train_ds = train_ds.prefetch(1)
val_ds = val_ds.prefetch(1)
test_ds = test_ds.prefetch(1)


# --------------------------------------------------
# 3. CLASS WEIGHTS
# --------------------------------------------------

train_counts = np.array([
    len(list((DATA_DIR / "train" / name).glob("*.jpg")))
    for name in class_names
])

if np.any(train_counts == 0):
    raise ValueError("One or more training classes contain no JPG images.")

weights = compute_class_weight(
    class_weight="balanced",
    classes=np.array([0, 1]),
    y=np.concatenate([
        np.full(train_counts[0], 0),
        np.full(train_counts[1], 1)
    ])
)

class_weights = {
    0: float(weights[0]),
    1: float(weights[1])
}

print("\nTraining image counts:", train_counts)
print("Class weights:", class_weights)


# --------------------------------------------------
# 4. DATA AUGMENTATION
# --------------------------------------------------

augmentation = keras.Sequential([
    layers.RandomFlip("horizontal"),
    layers.RandomRotation(0.05),
    layers.RandomZoom(0.10)
], name="augmentation")


# --------------------------------------------------
# 5. BUILD VGG19
# --------------------------------------------------

print("\nLoading pretrained VGG19...")

base_model = keras.applications.VGG19(
    weights="imagenet",
    include_top=False,
    input_shape=(224, 224, 3)
)

base_model.trainable = False

inputs = keras.Input(shape=(224, 224, 3))

x = augmentation(inputs)

x = keras.applications.vgg19.preprocess_input(x)

x = base_model(x, training=False)

x = layers.GlobalAveragePooling2D()(x)

x = layers.Dense(
    128,
    activation="relu"
)(x)

x = layers.Dropout(0.4)(x)

outputs = layers.Dense(
    1,
    activation="sigmoid"
)(x)

model = keras.Model(inputs, outputs)

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.0001),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        keras.metrics.Precision(name="precision"),
        keras.metrics.Recall(name="recall"),
        keras.metrics.AUC(name="auc")
    ]
)

print("\nModel summary:")
model.summary()


# --------------------------------------------------
# 6. CALLBACKS
# --------------------------------------------------

callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_PATH),
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),

    keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=3,
        restore_best_weights=True,
        verbose=1
    ),

    keras.callbacks.CSVLogger(
        str(OUTPUT_DIR / "training_log.csv"),
        append=False
    )
]


# --------------------------------------------------
# 7. INITIAL TRAINING
# --------------------------------------------------

print("\nStarting frozen VGG19 training...")

start_time = time.perf_counter()

history_initial = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=INITIAL_EPOCHS,
    class_weight=class_weights,
    callbacks=callbacks
)

initial_training_time = time.perf_counter() - start_time

# Restore best checkpoint before fine-tuning.
model = keras.models.load_model(MODEL_PATH)


# --------------------------------------------------
# 8. FINE-TUNING BLOCK 5
# --------------------------------------------------

print("\nStarting VGG19 fine-tuning...")

base_model = model.get_layer("vgg19")

base_model.trainable = True

for layer in base_model.layers:
    layer.trainable = layer.name.startswith("block5_")

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=0.00001),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        keras.metrics.Precision(name="precision"),
        keras.metrics.Recall(name="recall"),
        keras.metrics.AUC(name="auc")
    ]
)

fine_tune_callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath=str(MODEL_PATH),
        monitor="val_loss",
        save_best_only=True,
        verbose=1
    ),

    keras.callbacks.EarlyStopping(
        monitor="val_loss",
        patience=2,
        restore_best_weights=True,
        verbose=1
    ),

    keras.callbacks.CSVLogger(
        str(OUTPUT_DIR / "fine_tuning_log.csv")
    )
]

fine_start = time.perf_counter()

history_fine = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=FINE_TUNE_EPOCHS,
    class_weight=class_weights,
    callbacks=fine_tune_callbacks
)

fine_tuning_time = time.perf_counter() - fine_start


# --------------------------------------------------
# 9. FINAL TEST EVALUATION
# --------------------------------------------------

print("\nLoading best VGG19 checkpoint...")

model = keras.models.load_model(MODEL_PATH)

print("\nEvaluating on untouched test dataset...")

test_loss, test_accuracy, test_precision, test_recall, test_auc = (
    model.evaluate(test_ds, verbose=1)
)

y_true = []
y_prob = []

for images, labels in test_ds:
    probabilities = model.predict(images, verbose=0).reshape(-1)

    y_true.extend(labels.numpy().astype(int))
    y_prob.extend(probabilities)

y_true = np.array(y_true)
y_prob = np.array(y_prob)

y_pred = (y_prob >= 0.5).astype(int)

final_accuracy = accuracy_score(y_true, y_pred)
final_precision = precision_score(
    y_true, y_pred, zero_division=0
)
final_recall = recall_score(
    y_true, y_pred, zero_division=0
)
final_f1 = f1_score(
    y_true, y_pred, zero_division=0
)

cm = confusion_matrix(y_true, y_pred, labels=[0, 1])

print("\nClassification report:")
print(classification_report(
    y_true,
    y_pred,
    target_names=class_names,
    zero_division=0
))

print("\nConfusion matrix:")
print(cm)


# --------------------------------------------------
# 10. SAVE CONFUSION MATRIX
# --------------------------------------------------

fig, ax = plt.subplots(figsize=(6, 5))

ax.imshow(cm)

ax.set_title("VGG19 Confusion Matrix")
ax.set_xlabel("Predicted")
ax.set_ylabel("Actual")

ax.set_xticks([0, 1])
ax.set_yticks([0, 1])
ax.set_xticklabels(class_names)
ax.set_yticklabels(class_names)

for i in range(2):
    for j in range(2):
        ax.text(j, i, str(cm[i, j]), ha="center", va="center")

plt.tight_layout()

plt.savefig(
    OUTPUT_DIR / "confusion_matrix.png",
    dpi=150
)

plt.close()


# --------------------------------------------------
# 11. SAVE TRAINING CURVES
# --------------------------------------------------

def save_history_plot(history, filename, title):

    fig, ax = plt.subplots(figsize=(8, 5))

    ax.plot(history.history["loss"], label="Training loss")
    ax.plot(history.history["val_loss"], label="Validation loss")

    ax.set_title(title)
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Loss")
    ax.legend()

    plt.tight_layout()
    plt.savefig(OUTPUT_DIR / filename, dpi=150)
    plt.close()


save_history_plot(
    history_initial,
    "initial_training_loss.png",
    "VGG19 Initial Training"
)

save_history_plot(
    history_fine,
    "fine_tuning_loss.png",
    "VGG19 Fine-tuning"
)


# --------------------------------------------------
# 12. MODEL SIZE AND INFERENCE BENCHMARK
# --------------------------------------------------

model_size_mb = MODEL_PATH.stat().st_size / (1024 * 1024)

sample_batch, _ = next(iter(test_ds))
sample_image = sample_batch[:1]

# Warm-up
for _ in range(5):
    model.predict(sample_image, verbose=0)

latencies = []

for _ in range(30):
    start = time.perf_counter()
    model.predict(sample_image, verbose=0)
    latencies.append(
        (time.perf_counter() - start) * 1000
    )

mean_latency_ms = float(np.mean(latencies))
inference_fps = 1000 / mean_latency_ms

# --------------------------------------------------
# 13. SAVE EXPERIMENT RESULTS
# --------------------------------------------------

results = {
    "architecture": "VGG19",
    "tensorflow_version": tf.__version__,
    "keras_version": keras.__version__,
    "image_size": list(IMAGE_SIZE),
    "batch_size": BATCH_SIZE,
    "class_names": class_names,
    "class_weights": class_weights,
    "test_loss": float(test_loss),
    "accuracy": float(final_accuracy),
    "precision": float(final_precision),
    "recall": float(final_recall),
    "f1_score": float(final_f1),
    "auc": float(test_auc),
    "initial_training_seconds": initial_training_time,
    "fine_tuning_seconds": fine_tuning_time,
    "total_training_seconds": initial_training_time + fine_tuning_time,
    "model_size_mb": model_size_mb,
    "total_parameters": int(model.count_params()),
    "trainable_parameters": int(
        sum(
            np.prod(v.shape)
            for v in model.trainable_weights
        )
    ),
    "mean_inference_latency_ms": mean_latency_ms,
    "batch_size_for_latency": 1,
    "inference_fps_single_image": inference_fps,
    "confusion_matrix": cm.tolist()
}

with open(
    OUTPUT_DIR / "evaluation_results.json",
    "w",
    encoding="utf-8"
) as file:
    json.dump(results, file, indent=4)

print("\n========== FINAL VGG19 RESULTS ==========")

for key, value in results.items():
    print(f"{key}: {value}")

print("\nSaved model:", MODEL_PATH)
print("Results folder:", OUTPUT_DIR)
print("\nVGG19 training and evaluation completed!")
