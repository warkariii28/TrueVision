import os
import time
import traceback
from threading import Lock

import cv2
import numpy as np
import torch
import torch.nn as nn
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

from gradcam_explainer import get_gradcam_explanation

os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["GLOG_minloglevel"] = "3"

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
STATIC_DIR = os.path.join(BASE_DIR, "static")
UPLOADS_DIR = os.path.join(STATIC_DIR, "uploads")
GRADCAM_DIR = os.path.join(STATIC_DIR, "gradcam")

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

activations = None
grads = None
_model = None
_model_lock = Lock()


def save_activations(module, _input, output):
    global activations
    activations = output.detach()


def save_gradients(module, _grad_input, grad_output):
    global grads
    grads = grad_output[0].detach()


class CustomViT(nn.Module):
    def __init__(self):
        super().__init__()

        model_name = "microsoft/swin-base-patch4-window7-224"

        self.feature_extractor = AutoImageProcessor.from_pretrained(
            model_name,
            use_fast=False,
            local_files_only=True,
        )

        self.model = AutoModelForImageClassification.from_pretrained(
            model_name,
            local_files_only=True,
        )

        self.model.classifier = nn.Sequential(
            nn.Linear(self.model.classifier.in_features, 2)
        )

        model_path = os.path.join(BASE_DIR, "best_Swin_stage2.pth")
        state_dict = torch.load(model_path, map_location=device)
        self.model.load_state_dict(state_dict, strict=False)

        target_block = self.model.swin.encoder.layers[-1].blocks[-1].output.dense
        target_block.register_forward_hook(save_activations)
        target_block.register_full_backward_hook(save_gradients)

    def forward(self, x):
        outputs = self.model(x)
        return outputs.logits

    def predict(self, image):
        self.eval()
        inputs = self.feature_extractor(images=image, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(device)

        with torch.no_grad():
            outputs = self.forward(pixel_values)

        return outputs


def get_model():
    global _model

    if _model is not None:
        return _model

    with _model_lock:
        if _model is None:
            loaded_model = CustomViT().to(device)
            loaded_model.eval()
            _model = loaded_model

    return _model


def preload_model():
    """Warm the model into memory during startup when explicitly enabled."""
    try:
        get_model()
        return True
    except Exception:
        traceback.print_exc()
        return False


def predict_image(filepath):
    model = get_model()
    start_time = time.time()

    try:
        image = Image.open(filepath).convert("RGB")
        image = Image.fromarray(np.array(image))

        outputs = model.predict(image)
        probs = torch.softmax(outputs, dim=1)
        confidence, predicted_class = torch.max(probs, dim=1)

        label_map = {0: "Fake", 1: "Real"}
        prediction = label_map.get(predicted_class.item(), "Unknown")

        gradcam_path, cam_array = generate_gradcam(
            filepath,
            prediction,
            confidence.item(),
        )

        if gradcam_path is None or cam_array is None:
            return {"error": "Failed to generate Grad-CAM output."}

        gradcam_explanation = get_gradcam_explanation(
            cam_array,
            image.size,
            confidence.item(),
            is_fake=(prediction == "Fake"),
        )

        filename = os.path.basename(filepath)
        image_rel_path = os.path.join("uploads", filename).replace("\\", "/")
        gradcam_rel_path = os.path.join(
            "gradcam",
            os.path.basename(gradcam_path),
        ).replace("\\", "/")

        return {
            "prediction": prediction,
            "confidence": round(confidence.item() * 100, 4),
            "image_path": image_rel_path,
            "gradcam_path": gradcam_rel_path,
            "explanation": gradcam_explanation["explanation"],
            "recommendation": gradcam_explanation["recommendation"],
            "inference_time": round(time.time() - start_time, 3),
        }

    except Exception as exc:
        traceback.print_exc()
        return {"error": f"Error during prediction: {exc}"}


def generate_gradcam(image_path, prediction, confidence):
    global activations, grads

    activations = None
    grads = None
    model = get_model()

    try:
        image = Image.open(image_path).convert("RGB")
        inputs = model.feature_extractor(images=image, return_tensors="pt")
        pixel_values = inputs["pixel_values"].to(device)
        pixel_values.requires_grad = True

        outputs = model.model(pixel_values).logits
        pred_class = outputs.argmax(dim=1)

        one_hot = torch.zeros_like(outputs)
        one_hot[0, pred_class] = 1
        outputs.backward(gradient=one_hot)

        if activations is None or grads is None:
            raise ValueError("Grad-CAM hooks did not capture data properly.")

        pooled_grads = grads.mean(dim=1)
        weights = pooled_grads[0]
        cam = torch.matmul(activations[0], weights)
        cam = cam.reshape(7, 7).cpu().numpy()

        is_fake = prediction == "Fake"

        if is_fake:
            if confidence > 0.95:
                percentile_value = np.percentile(cam, 60)
                power_factor = 2.0
            elif confidence > 0.85:
                percentile_value = np.percentile(cam, 70)
                power_factor = 1.8
            else:
                percentile_value = np.percentile(cam, 75)
                power_factor = 1.5
        else:
            uncertainty = 1 - confidence
            if uncertainty > 0.3:
                percentile_value = np.percentile(cam, 65)
                power_factor = 1.8
            elif uncertainty > 0.15:
                percentile_value = np.percentile(cam, 75)
                power_factor = 1.6
            else:
                percentile_value = np.percentile(cam, 85)
                power_factor = 1.4

        cam = np.maximum(cam - percentile_value, 0)
        cam = np.power(cam, power_factor)

        if cam.max() > 0:
            cam = cam / cam.max()

        cam_array = cam.copy()
        cam = cv2.resize(cam, image.size)

        colormap = cv2.COLORMAP_HOT if is_fake else cv2.COLORMAP_COOL
        heatmap = cv2.applyColorMap(np.uint8(255 * cam), colormap)

        image_np = np.array(image)
        image_np = cv2.cvtColor(image_np, cv2.COLOR_RGB2BGR)

        if is_fake and confidence > 0.9:
            overlay = cv2.addWeighted(image_np, 0.5, heatmap, 0.5, 0)
        elif is_fake:
            overlay = cv2.addWeighted(image_np, 0.6, heatmap, 0.4, 0)
        else:
            overlay = cv2.addWeighted(image_np, 0.7, heatmap, 0.3, 0)

        overlay = cv2.cvtColor(overlay, cv2.COLOR_BGR2RGB)
        overlay_img = Image.fromarray(overlay)
        base_name = os.path.splitext(image_path)[0]

        os.makedirs(GRADCAM_DIR, exist_ok=True)

        overlay_path = os.path.join(
            GRADCAM_DIR,
            os.path.basename(base_name) + "_gradcam.jpg",
        )
        overlay_img.save(overlay_path)

        return overlay_path, cam_array

    except Exception:
        traceback.print_exc()
        return None, None
