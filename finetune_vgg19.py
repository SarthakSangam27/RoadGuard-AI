
import time
from pathlib import Path

import keras
import tensorflow as tf

MODEL_PATH = Path("runs/vgg19/roadguard_vgg19/best_vgg19.keras")
DATA_DIR = Path("data/vgg19_classification")
OUTPUT_DIR = Path("runs/vgg19/roadguard_vgg19")

IMAGE_SIZE = (224, 224)
BATCH_SIZE = 4
EPOCHS = 3

if not MODEL_PATH.exists():
    raise FileNotFoundError(f"Checkpoint not found: {MODEL_PATH}")

OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

train_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "train",
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=True,
    seed=42
)

val_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "valid",
    image_size=IMAGE_SIZE,
    batch_size=BATCH_SIZE,
    label_mode="int",
    shuffle=False
)

if train_ds.class_names != ["background", "pothole"]:
    raise ValueError(f"Unexpected classes: {train_ds.class_names}")

train_ds = train_ds.prefetch(1)
val_ds = val_ds.prefetch(1)

print("Loading existing best checkpoint...")
model = keras.models.load_model(MODEL_PATH)

base_model = model.get_layer("vgg19")
base_model.trainable = True

for layer in base_model.layers:
    layer.trainable = layer.name.startswith("block5_")

model.compile(
    optimizer=keras.optimizers.Adam(learning_rate=1e-5),
    loss="binary_crossentropy",
    metrics=[
        "accuracy",
        keras.metrics.Precision(name="precision"),
        keras.metrics.Recall(name="recall"),
        keras.metrics.AUC(name="auc")
    ]
)

print("\nTrainable VGG19 layers:")
for layer in base_model.layers:
    if layer.trainable:
        print(layer.name)

callbacks = [
    keras.callbacks.ModelCheckpoint(
        filepath=str(OUTPUT_DIR / "best_vgg19_finetuned.keras"),
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

print("\nStarting fine-tuning from saved checkpoint...")

start = time.perf_counter()

history = model.fit(
    train_ds,
    validation_data=val_ds,
    epochs=EPOCHS,
    callbacks=callbacks
)

print(f"\nFine-tuning time: {time.perf_counter() - start:.2f} seconds")
print("Best fine-tuned model:", OUTPUT_DIR / "best_vgg19_finetuned.keras")
print("Fine-tuning completed!")
