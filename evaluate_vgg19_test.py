
import json
import numpy as np
import keras
from pathlib import Path
from sklearn.metrics import (
    classification_report,
    confusion_matrix,
    roc_auc_score
)

DATA_DIR = Path("data/vgg19_classification")
MODEL_PATH = Path(
    "runs/vgg19/roadguard_vgg19/best_vgg19_finetuned.keras"
)
OUTPUT_DIR = Path("runs/vgg19/roadguard_vgg19")

test_ds = keras.utils.image_dataset_from_directory(
    DATA_DIR / "test",
    image_size=(224, 224),
    batch_size=4,
    label_mode="int",
    shuffle=False
)

model = keras.models.load_model(MODEL_PATH)

y_true = np.concatenate([
    labels.numpy() for _, labels in test_ds
])

y_prob = model.predict(test_ds, verbose=1).reshape(-1)
y_pred = (y_prob >= 0.5).astype(int)

report = classification_report(
    y_true,
    y_pred,
    target_names=test_ds.class_names,
    output_dict=True,
    zero_division=0
)

cm = confusion_matrix(y_true, y_pred).tolist()
auc = float(roc_auc_score(y_true, y_prob))

results = {
    "model": "VGG19 Fine-tuned",
    "test_accuracy": float(report["accuracy"]),
    "test_precision": float(report["pothole"]["precision"]),
    "test_recall": float(report["pothole"]["recall"]),
    "test_f1": float(report["pothole"]["f1-score"]),
    "test_auc": auc,
    "confusion_matrix": cm
}

with open(OUTPUT_DIR / "final_test_results.json", "w") as f:
    json.dump(results, f, indent=4)

print("\nFINAL TEST RESULTS")
print(classification_report(
    y_true, y_pred,
    target_names=test_ds.class_names,
    zero_division=0
))
print("AUC:", auc)
print("Confusion Matrix:", cm)
print("\nSaved final_test_results.json")
