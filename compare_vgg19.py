
import numpy as np
import keras
from pathlib import Path
from sklearn.metrics import accuracy_score, precision_score, recall_score, f1_score, roc_auc_score

DATA_DIR = Path("data/vgg19_classification")
OUTPUT_DIR = Path("runs/vgg19/roadguard_vgg19")

models = {
    "Original VGG19": OUTPUT_DIR / "best_vgg19.keras",
    "Fine-tuned VGG19": OUTPUT_DIR / "best_vgg19_finetuned.keras"
}

val_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "valid",
    image_size=(224, 224),
    batch_size=4,
    label_mode="int",
    shuffle=False
)

y_true = np.concatenate([y.numpy() for _, y in val_ds])

print("\nValidation dataset classes:", val_ds.class_names)
print("\n========== MODEL COMPARISON ==========")

for name, path in models.items():
    if not path.exists():
        print(f"\nMissing model: {path}")
        continue

    print(f"\nEvaluating {name}...")
    model = keras.models.load_model(path)

    probabilities = model.predict(val_ds, verbose=0).reshape(-1)
    predictions = (probabilities >= 0.5).astype(int)

    print("Accuracy :", round(accuracy_score(y_true, predictions), 4))
    print("Precision:", round(precision_score(y_true, predictions, zero_division=0), 4))
    print("Recall   :", round(recall_score(y_true, predictions, zero_division=0), 4))
    print("F1-score :", round(f1_score(y_true, predictions, zero_division=0), 4))
    print("AUC      :", round(roc_auc_score(y_true, probabilities), 4))

    del model
    keras.backend.clear_session()

print("\nComparison completed!")
