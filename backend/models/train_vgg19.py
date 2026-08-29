from pathlib import Path
import json
import time

import tensorflow as tf

from tensorflow.keras import layers, models, callbacks
from tensorflow.keras.applications import VGG19
from tensorflow.keras.applications.vgg19 import preprocess_input


# ============================================================
# PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent

DATA_DIR = BASE_DIR / "data" / "classification"

TRAIN_DIR = DATA_DIR / "train"
VAL_DIR = DATA_DIR / "val"
TEST_DIR = DATA_DIR / "test"

MODEL_DIR = BASE_DIR / "saved_models"
OUTPUT_DIR = BASE_DIR / "outputs"

MODEL_DIR.mkdir(
    parents=True,
    exist_ok=True
)

OUTPUT_DIR.mkdir(
    parents=True,
    exist_ok=True
)


# ============================================================
# CONFIGURATION
# ============================================================

IMAGE_SIZE = (224, 224)

BATCH_SIZE = 32

EPOCHS = 20

SEED = 42

LEARNING_RATE = 1e-4


# ============================================================
# VERIFY DATASET
# ============================================================

def verify_dataset():

    required_directories = [
        TRAIN_DIR / "pothole",
        TRAIN_DIR / "no_pothole",

        VAL_DIR / "pothole",
        VAL_DIR / "no_pothole",

        TEST_DIR / "pothole",
        TEST_DIR / "no_pothole",
    ]

    for directory in required_directories:

        if not directory.exists():

            raise FileNotFoundError(
                f"Missing dataset directory:\n"
                f"{directory}"
            )

    print("Dataset structure verified.")


# ============================================================
# LOAD DATASET
# ============================================================

def load_dataset(
    directory,
    shuffle
):

    return tf.keras.utils.image_dataset_from_directory(

        directory,

        labels="inferred",

        label_mode="binary",

        class_names=[
            "no_pothole",
            "pothole"
        ],

        image_size=IMAGE_SIZE,

        batch_size=BATCH_SIZE,

        shuffle=shuffle,

        seed=SEED
    )


# ============================================================
# BUILD MODEL
# ============================================================

def build_model():

    print()
    print("=" * 60)
    print("BUILDING VGG19")
    print("=" * 60)

    base_model = VGG19(

        weights="imagenet",

        include_top=False,

        input_shape=(
            224,
            224,
            3
        )
    )

    # Freeze pretrained layers
    base_model.trainable = False

    inputs = layers.Input(
        shape=(
            224,
            224,
            3
        )
    )

    # VGG19 ImageNet preprocessing
    x = preprocess_input(inputs)

    x = base_model(
        x,
        training=False
    )

    x = layers.GlobalAveragePooling2D()(x)

    x = layers.Dense(
        256,
        activation="relu"
    )(x)

    x = layers.Dropout(
        0.5
    )(x)

    outputs = layers.Dense(
        1,
        activation="sigmoid"
    )(x)

    model = models.Model(
        inputs,
        outputs
    )

    model.compile(

        optimizer=tf.keras.optimizers.Adam(
            learning_rate=LEARNING_RATE
        ),

        loss="binary_crossentropy",

        metrics=[
            "accuracy",
            tf.keras.metrics.Precision(
                name="precision"
            ),
            tf.keras.metrics.Recall(
                name="recall"
            )
        ]
    )

    return model


# ============================================================
# CALLBACKS
# ============================================================

def create_callbacks():

    best_model = (
        MODEL_DIR
        / "vgg19_best.keras"
    )

    return [

        callbacks.ModelCheckpoint(

            filepath=str(
                best_model
            ),

            monitor="val_accuracy",

            save_best_only=True,

            mode="max",

            verbose=1
        ),

        callbacks.EarlyStopping(

            monitor="val_loss",

            patience=5,

            restore_best_weights=True,

            verbose=1
        ),

        callbacks.ReduceLROnPlateau(

            monitor="val_loss",

            factor=0.2,

            patience=2,

            min_lr=1e-7,

            verbose=1
        )
    ]


# ============================================================
# SAVE HISTORY
# ============================================================

def save_history(history):

    history_path = (
        OUTPUT_DIR
        / "vgg19_history.json"
    )

    history_data = {}

    for key, values in history.history.items():

        history_data[key] = [
            float(value)
            for value in values
        ]

    with open(
        history_path,
        "w"
    ) as file:

        json.dump(
            history_data,
            file,
            indent=4
        )

    print(
        f"History saved to:\n"
        f"{history_path}"
    )


# ============================================================
# MAIN
# ============================================================

def main():

    start_time = time.time()

    print()
    print("=" * 70)
    print("ROADGUARD-AI — VGG19 TRAINING")
    print("=" * 70)

    verify_dataset()

    print()
    print("Loading datasets...")

    train_ds = load_dataset(
        TRAIN_DIR,
        shuffle=True
    )

    val_ds = load_dataset(
        VAL_DIR,
        shuffle=False
    )

    test_ds = load_dataset(
        TEST_DIR,
        shuffle=False
    )

    train_ds = train_ds.prefetch(
        tf.data.AUTOTUNE
    )

    val_ds = val_ds.prefetch(
        tf.data.AUTOTUNE
    )

    test_ds = test_ds.prefetch(
        tf.data.AUTOTUNE
    )

    print()
    print("Creating model...")

    model = build_model()

    model.summary()

    print()
    print("=" * 70)
    print("STARTING TRAINING")
    print("=" * 70)

    history = model.fit(

        train_ds,

        validation_data=val_ds,

        epochs=EPOCHS,

        callbacks=create_callbacks()
    )

    # --------------------------------------------------------
    # Save final model
    # --------------------------------------------------------

    final_model = (
        MODEL_DIR
        / "vgg19_pothole.keras"
    )

    model.save(
        final_model
    )

    print(
        f"\nFinal model saved:\n"
        f"{final_model}"
    )

    # --------------------------------------------------------
    # Save history
    # --------------------------------------------------------

    save_history(
        history
    )

    # --------------------------------------------------------
    # Evaluate
    # --------------------------------------------------------

    print()
    print("=" * 70)
    print("TEST EVALUATION")
    print("=" * 70)

    results = model.evaluate(
        test_ds,
        verbose=1
    )

    for name, value in zip(
        model.metrics_names,
        results
    ):

        print(
            f"{name}: {value:.4f}"
        )

    elapsed = (
        time.time()
        - start_time
    )

    print()
    print("=" * 70)
    print("VGG19 TRAINING COMPLETE")
    print("=" * 70)

    print(
        f"Training time: "
        f"{elapsed / 60:.2f} minutes"
    )


if __name__ == "__main__":

    main()