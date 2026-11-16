from ultralytics import YOLO
import torch

print("PyTorch:", torch.__version__)
print("CPU mode:", not torch.cuda.is_available())

model = YOLO("yolo11n-seg.pt")
print("Segmentation model loaded successfully.")
print("Model task:", model.task)
