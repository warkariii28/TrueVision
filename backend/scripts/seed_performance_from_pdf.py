"""Create database tables and seed model performance metrics from TrueVision.pdf.

The PDF gives metric ratios but does not expose TP/TN/FP/FN as selectable text.
Counts below are derived from the paper's dataset size: 375,000 images with a
20% test split and 55.28:44.72 fake:real class balance. Fake is treated as the
positive class for precision/recall.
"""
from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
import sys

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app import create_app, db
from models import Performance

TEST_SIZE = 75_000
POSITIVE_RATIO = 0.5528
POSITIVE_COUNT = round(TEST_SIZE * POSITIVE_RATIO)
NEGATIVE_COUNT = TEST_SIZE - POSITIVE_COUNT


@dataclass(frozen=True)
class MetricRow:
    model_name: str
    accuracy: float
    precision: float
    recall: float
    f1_score: float
    auc_roc: float
    pr_auc: float


PDF_METRICS = [
    # Table 1. Stage-1 Training Results (Classifier Only)
    MetricRow("Stage-1 ResNet50", 0.8108, 0.7540, 0.8675, 0.8068, 0.8974, 0.8701),
    MetricRow("Stage-1 XceptionNet", 0.7889, 0.7744, 0.7568, 0.7655, 0.8712, 0.8376),
    MetricRow("Stage-1 EfficientB3", 0.7973, 0.7613, 0.8084, 0.7842, 0.8804, 0.8429),
    MetricRow("Stage-1 InceptionNetV3", 0.7440, 0.7281, 0.6988, 0.7132, 0.8286, 0.7908),
    MetricRow("Stage-1 DenseNet121", 0.7858, 0.7413, 0.8137, 0.7758, 0.8682, 0.8266),
    MetricRow("Stage-1 ViT", 0.7883, 0.7385, 0.8286, 0.7810, 0.8718, 0.8278),
    MetricRow("Stage-1 Swin", 0.8641, 0.8224, 0.8947, 0.8570, 0.9375, 0.9152),
    # Table 2. Stage-2 Training Results (Classifier + Task-Specific Layer)
    MetricRow("Stage-2 ResNet50", 0.8196, 0.7952, 0.8135, 0.8042, 0.9015, 0.8749),
    MetricRow("Stage-2 XceptionNet", 0.7863, 0.7769, 0.7445, 0.7604, 0.8707, 0.8342),
    MetricRow("Stage-2 EfficientB3", 0.8165, 0.7801, 0.8316, 0.8050, 0.8988, 0.8688),
    MetricRow("Stage-2 ViT", 0.8018, 0.7495, 0.8481, 0.7958, 0.8843, 0.8425),
    MetricRow("Stage-2 Swin", 0.8688, 0.8272, 0.8999, 0.8620, 0.9410, 0.9189),
]


def confusion_counts(row: MetricRow) -> tuple[int, int, int, int, float, float]:
    tp = round(row.recall * POSITIVE_COUNT)
    fn = POSITIVE_COUNT - tp
    fp = round(tp * ((1 / row.precision) - 1)) if row.precision else 0
    tn = max(NEGATIVE_COUNT - fp, 0)
    fpr = fp / NEGATIVE_COUNT if NEGATIVE_COUNT else 0
    fnr = fn / POSITIVE_COUNT if POSITIVE_COUNT else 0
    return tp, tn, fp, fn, fpr, fnr


def upsert_performance(row: MetricRow) -> None:
    tp, tn, fp, fn, fpr, fnr = confusion_counts(row)
    record = Performance.query.filter_by(model_name=row.model_name).first()

    if record is None:
        record = Performance(model_name=row.model_name)
        db.session.add(record)

    record.accuracy = row.accuracy
    record.precision = row.precision
    record.recall = row.recall
    record.f1_score = row.f1_score
    record.fpr = fpr
    record.fnr = fnr
    record.tnr = 1 - fpr
    record.tp = tp
    record.tn = tn
    record.fp = fp
    record.fn = fn
    record.auc_roc = row.auc_roc
    record.pr_auc = row.pr_auc
    record.confusion_matrix = f"[[TN={tn}, FP={fp}], [FN={fn}, TP={tp}]]"


def main() -> None:
    app = create_app()
    with app.app_context():
        db.create_all()
        for row in PDF_METRICS:
            upsert_performance(row)
        db.session.commit()

        print(f"Seeded {len(PDF_METRICS)} performance rows.")
        print(f"Derived counts use test_size={TEST_SIZE}, positives={POSITIVE_COUNT}, negatives={NEGATIVE_COUNT}.")
        best = Performance.query.order_by(Performance.accuracy.desc()).first()
        if best:
            print(f"Best model: {best.model_name} ({best.accuracy:.4f} accuracy)")


if __name__ == "__main__":
    main()