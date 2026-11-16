import csv
import json
import time
from pathlib import Path

import cv2
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (
    accuracy_score, auc, classification_report, confusion_matrix,
    f1_score, precision_recall_curve, precision_score, recall_score,
    roc_auc_score, roc_curve,
)
from ultralytics import YOLO

ROOT = Path(__file__).resolve().parents[1]
YOLO_WEIGHTS = ROOT / "backend" / "models" / "pothole_best.pt"
VGG_WEIGHTS = ROOT / "runs" / "vgg19" / "roadguard_vgg19" / "best_vgg19_finetuned.keras"
DATA_YAML = ROOT / "data" / "roadguard_detection" / "data.yaml"
TEST_IMAGES = ROOT / "data" / "roadguard_detection" / "test" / "images"
TEST_LABELS = ROOT / "data" / "roadguard_detection" / "test" / "labels"
OUT = ROOT / "runs" / "model_evaluation"
PLOTS = OUT / "plots"
YOLO_PLOTS, VGG_PLOTS, COMPARE_PLOTS = PLOTS / "yolov8", PLOTS / "vgg19", PLOTS / "comparison"
IMAGE_SIZE = (224, 224)
YOLO_SIZE = 320
THRESHOLD = 0.5
YOLO_DISPLAY_CONF = 0.25
EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

for folder in (OUT, YOLO_PLOTS, VGG_PLOTS, COMPARE_PLOTS):
    folder.mkdir(parents=True, exist_ok=True)

required = {
    "YOLO weights": YOLO_WEIGHTS, "VGG19 weights": VGG_WEIGHTS,
    "YOLO data.yaml": DATA_YAML, "test images": TEST_IMAGES,
    "test labels": TEST_LABELS,
}
missing = [f"{k}: {v}" for k, v in required.items() if not v.exists()]
if missing:
    raise FileNotFoundError(
        "Missing evaluation input(s):\n  " + "\n  ".join(missing) +
        "\nEdit the path constants at the top of this script."
    )

images = sorted(p for p in TEST_IMAGES.iterdir() if p.is_file() and p.suffix.lower() in EXTS)
if not images:
    raise RuntimeError(f"No images found in {TEST_IMAGES}")


def image_label(image_path):
    label_file = TEST_LABELS / f"{image_path.stem}.txt"
    if not label_file.exists():
        raise FileNotFoundError(f"Missing YOLO label: {label_file}")
    for line in label_file.read_text(encoding="utf-8").splitlines():
        fields = line.split()
        if fields and int(float(fields[0])) == 0:
            return 1
    return 0


def save_cm(cm, title, path):
    fig, ax = plt.subplots(figsize=(6, 5))
    im = ax.imshow(cm)
    ax.set(title=title, xlabel="Predicted", ylabel="Actual")
    ax.set_xticks([0, 1], ["Background", "Pothole"])
    ax.set_yticks([0, 1], ["Background", "Pothole"])
    fig.colorbar(im, ax=ax)
    for r in range(2):
        for c in range(2):
            ax.text(c, r, str(cm[r, c]), ha="center", va="center")
    fig.tight_layout()
    fig.savefig(path, dpi=180)
    plt.close(fig)


print("Loading YOLOv8:", YOLO_WEIGHTS)
yolo = YOLO(str(YOLO_WEIGHTS))
print("Loading VGG19:", VGG_WEIGHTS)
vgg = tf.keras.models.load_model(str(VGG_WEIGHTS), compile=False)
if isinstance(vgg.output_shape, list) or vgg.output_shape[-1] != 1:
    raise ValueError(f"Expected single sigmoid output (None, 1), got {vgg.output_shape}")


print("Running Ultralytics test-set validation...")
val_start = time.perf_counter()
val = yolo.val(
    data=str(DATA_YAML), split="test", imgsz=YOLO_SIZE, device="cpu",
    plots=True, project=str(OUT / "ultralytics"), name="yolov8_test",
    exist_ok=True, verbose=True,
)
val_seconds = time.perf_counter() - val_start
try:
    detection_metrics = {
        "precision": float(val.box.mp), "recall": float(val.box.mr),
        "map50": float(val.box.map50), "map50_95": float(val.box.map),
    }
except Exception as exc:
    print("Could not extract Ultralytics metrics:", exc)
    detection_metrics = {}

if detection_metrics:
    labels = ["Precision", "Recall", "mAP@50", "mAP@50-95"]
    vals = [detection_metrics[k] for k in ("precision", "recall", "map50", "map50_95")]
    fig, ax = plt.subplots(figsize=(8, 5))
    bars = ax.bar(labels, vals)
    ax.set_ylim(0, 1)
    ax.set_ylabel("Score")
    ax.set_title("YOLOv8 Detection Metrics – Test Set")
    ax.grid(axis="y", alpha=0.25)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width()/2, v + 0.02, f"{v:.3f}", ha="center")
    fig.tight_layout()
    fig.savefig(YOLO_PLOTS / "detection_metrics.png", dpi=180)
    plt.close(fig)


truth, yolo_scores, vgg_scores = [], [], []
yolo_times, vgg_times, rows = [], [], []
print(f"Running image-level comparison on {len(images)} common test images...")
for i, path in enumerate(images, 1):
    bgr = cv2.imread(str(path))
    if bgr is None:
        print("Skipping unreadable:", path.name)
        continue
    target = image_label(path)

    start = time.perf_counter()
    pred = yolo.predict(
        source=bgr, imgsz=YOLO_SIZE, conf=0.001, device="cpu", verbose=False
    )[0]
    yolo_ms = (time.perf_counter() - start) * 1000
    if pred.boxes is not None and len(pred.boxes):
        confs = pred.boxes.conf.detach().cpu().numpy()
        yolo_score = float(np.max(confs))
        detection_count = int(np.sum(confs >= YOLO_DISPLAY_CONF))
    else:
        yolo_score, detection_count = 0.0, 0



    resized = cv2.resize(bgr, IMAGE_SIZE)
    rgb = cv2.cvtColor(resized, cv2.COLOR_BGR2RGB).astype(np.float32)[None, ...]
    start = time.perf_counter()
    vgg_score = float(vgg.predict(rgb, verbose=0).reshape(-1)[0])
    vgg_ms = (time.perf_counter() - start) * 1000

    truth.append(target)
    yolo_scores.append(yolo_score)
    vgg_scores.append(vgg_score)
    yolo_times.append(yolo_ms)
    vgg_times.append(vgg_ms)
    rows.append({
        "image": path.name, "ground_truth": target,
        "ground_truth_label": "pothole" if target else "background",
        "yolov8_pothole_score": yolo_score,
        "yolov8_predicted_label": "pothole" if yolo_score >= THRESHOLD else "background",
        "yolov8_detections_at_conf_0_25": detection_count,
        "yolov8_inference_ms": yolo_ms,
        "vgg19_pothole_probability": vgg_score,
        "vgg19_predicted_label": "pothole" if vgg_score >= THRESHOLD else "background",
        "vgg19_inference_ms": vgg_ms,
    })
    print(f"[{i}/{len(images)}] {path.name}")

truth = np.asarray(truth, dtype=int)
yolo_scores, vgg_scores = np.asarray(yolo_scores), np.asarray(vgg_scores)
if len(truth) == 0:
    raise RuntimeError("No valid test images were processed. Check the test images and matching YOLO label files.")
if len(np.unique(truth)) < 2:
    print("WARNING: Only one ground-truth class is present in the shared test set.")
    print("ROC-AUC and ROC/PR curves will be skipped; confusion matrices and other metrics will still be saved.")


def metrics(scores):
    pred = (scores >= THRESHOLD).astype(int)
    cm = confusion_matrix(truth, pred, labels=[0, 1])
    return {
        "accuracy": float(accuracy_score(truth, pred)),
        "precision": float(precision_score(truth, pred, zero_division=0)),
        "recall": float(recall_score(truth, pred, zero_division=0)),
        "f1_score": float(f1_score(truth, pred, zero_division=0)),
        "roc_auc": float(roc_auc_score(truth, scores)) if len(np.unique(truth)) == 2 else None,
        "confusion_matrix": cm.tolist(),
        "classification_report": classification_report(
            truth, pred, labels=[0, 1],
            target_names=["background", "pothole"],
            output_dict=True, zero_division=0,
        ),
    }


ym, vm = metrics(yolo_scores), metrics(vgg_scores)
save_cm(np.array(ym["confusion_matrix"]), "YOLOv8 Image-level Confusion Matrix", YOLO_PLOTS / "image_level_confusion_matrix.png")
save_cm(np.array(vm["confusion_matrix"]), "VGG19 Image-level Confusion Matrix", VGG_PLOTS / "image_level_confusion_matrix.png")


if len(np.unique(truth)) == 2:
    fig, ax = plt.subplots(figsize=(7, 6))
    for name, scores in (("YOLOv8", yolo_scores), ("VGG19", vgg_scores)):
        fpr, tpr, _ = roc_curve(truth, scores)
        ax.plot(fpr, tpr, label=f"{name} AUC={auc(fpr, tpr):.3f}")
    ax.plot([0, 1], [0, 1], "--", label="Random baseline")
    ax.set(xlabel="False Positive Rate", ylabel="True Positive Rate", title="ROC – Same Original Test Images")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(COMPARE_PLOTS / "roc_comparison.png", dpi=180)
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(7, 6))
    for name, scores in (("YOLOv8", yolo_scores), ("VGG19", vgg_scores)):
        p, r, _ = precision_recall_curve(truth, scores)
        ax.plot(r, p, label=f"{name} PR-AUC={auc(r, p):.3f}")
    ax.set(xlabel="Recall", ylabel="Precision", title="Precision–Recall – Same Original Test Images")
    ax.legend()
    ax.grid(alpha=0.25)
    fig.tight_layout()
    fig.savefig(COMPARE_PLOTS / "precision_recall_comparison.png", dpi=180)
    plt.close(fig)
else:
    print("WARNING: Shared test images contain only one ground-truth class.")
    print("ROC-AUC and ROC/PR curves are skipped. Add background-only images to the YOLO test split to calculate them.")
    fig, ax = plt.subplots(figsize=(7, 5))
    ax.text(0.5, 0.5, "ROC/PR curves unavailable\\nTest set must contain background and pothole images", ha="center", va="center", wrap=True)
    ax.set_axis_off()
    fig.tight_layout()
    fig.savefig(COMPARE_PLOTS / "roc_pr_unavailable.png", dpi=180)
    plt.close(fig)


metric_keys = ["accuracy", "precision", "recall", "f1_score"]
metric_labels = ["Accuracy", "Precision", "Recall", "F1-score"]
if len(np.unique(truth)) == 2:
    metric_keys.append("roc_auc")
    metric_labels.append("ROC-AUC")
x, width = np.arange(len(metric_keys)), 0.36
fig, ax = plt.subplots(figsize=(10, 6))
b1 = ax.bar(x-width/2, [ym[k] for k in metric_keys], width, label="YOLOv8")
b2 = ax.bar(x+width/2, [vm[k] for k in metric_keys], width, label="VGG19")
ax.set_xticks(x, metric_labels)
ax.set_ylim(0, 1.08)
ax.set_ylabel("Score")
ax.set_title("Image-level Classification Comparison – Same Test Images")
ax.legend()
ax.grid(axis="y", alpha=0.25)
for bars in (b1, b2):
    for b in bars:
        ax.text(b.get_x()+b.get_width()/2, b.get_height()+0.015, f"{b.get_height():.2f}", ha="center", fontsize=8)
fig.tight_layout()
fig.savefig(COMPARE_PLOTS / "classification_metrics_comparison.png", dpi=180)
plt.close(fig)


means = [float(np.mean(yolo_times)), float(np.mean(vgg_times))]
fig, ax = plt.subplots(figsize=(7, 5))
bars = ax.bar(["YOLOv8", "VGG19"], means)
ax.set_ylabel("Mean inference time (ms)")
ax.set_title("Mean Per-image Inference Time – Same Test Images")
ax.grid(axis="y", alpha=0.25)
for b, v in zip(bars, means):
    ax.text(b.get_x()+b.get_width()/2, v, f"{v:.1f} ms", ha="center", va="bottom")
fig.tight_layout()
fig.savefig(COMPARE_PLOTS / "inference_latency_comparison.png", dpi=180)
plt.close(fig)


with (OUT / "per_image_predictions.csv").open("w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
    writer.writeheader()
    writer.writerows(rows)

report = {
    "project": "RoadGuard-AI",
    "common_image_level_test": {
        "source": str(TEST_IMAGES.relative_to(ROOT)),
        "images": int(len(truth)),
        "background_images": int(np.sum(truth == 0)),
        "pothole_images": int(np.sum(truth == 1)),
        "threshold": THRESHOLD,
        "roc_pr_available": bool(len(np.unique(truth)) == 2),
        "yolov8": ym,
        "vgg19": vm,
        "interpretation_warning": (
            "Both models were evaluated on the same original YOLO test images. "
            "However, VGG19 training used cropped classification images, so "
            "full-image VGG19 evaluation has a crop/full-image domain shift. "
            "Report this limitation; do not treat this as a definitive model ranking."
        ),
    },
    "yolov8_object_detection": {
        **detection_metrics,
        "validation_seconds": val_seconds,
        "note": "Ultralytics box metrics use YOLO test bounding-box labels.",
    },
    "mean_inference_ms_one_pass": {"yolov8": means[0], "vgg19": means[1]},
    "output_directory": str(OUT.relative_to(ROOT)),
}
(OUT / "evaluation_report.json").write_text(json.dumps(report, indent=2), encoding="utf-8")
with (OUT / "summary_metrics.csv").open("w", newline="", encoding="utf-8") as f:
    w = csv.writer(f)
    w.writerow(["evaluation_type", "model", "metric", "value"])
    for name, result in (("YOLOv8", ym), ("VGG19", vm)):
        for key in metric_keys:
            w.writerow(["shared_image_level", name, key, result[key]])
    for key, value in detection_metrics.items():
        w.writerow(["object_detection", "YOLOv8", key, value])

print("\nEvaluation completed.")
print("YOLOv8 image-level:", {k: ym[k] for k in metric_keys})
print("VGG19 image-level:", {k: vm[k] for k in metric_keys})
print("YOLOv8 detection:", detection_metrics)
print("Saved charts and reports to:", OUT)



