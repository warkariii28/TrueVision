from app import db
from test_models import Performance


def test_performance_returns_404_when_no_data(client):
    response = client.get("/api/performance")

    assert response.status_code == 404
    data = response.get_json()
    assert data["error"] == "No performance data available."
    assert data["models"] == []


def test_performance_returns_best_model_and_all_models(client):
    with client.application.app_context():
        db.session.add_all([
            Performance(
                model_name="ResNet50",
                accuracy=0.8196,
                precision=0.7952,
                recall=0.8135,
                f1_score=0.8042,
                fpr=0.1755,
                fnr=0.1865,
                tnr=0.8245,
                tp=3708,
                tn=4487,
                fp=955,
                fn=850,
                auc_roc=0.9015,
                pr_auc=0.8749,
                confusion_matrix="[[4487,955],[850,3708]]",
            ),
            Performance(
                model_name="Swin",
                accuracy=0.8688,
                precision=0.8272,
                recall=0.8999,
                f1_score=0.8620,
                fpr=0.1575,
                fnr=0.1000,
                tnr=0.8425,
                tp=4102,
                tn=4585,
                fp=857,
                fn=456,
                auc_roc=0.9410,
                pr_auc=0.9189,
                confusion_matrix="[[4585,857],[456,4102]]",
            ),
        ])
        db.session.commit()

    response = client.get("/api/performance")

    assert response.status_code == 200
    data = response.get_json()

    assert "bestModel" in data
    assert "models" in data
    assert len(data["models"]) == 2

    best = data["bestModel"]
    assert best["modelName"] == "Swin"
    assert best["accuracy"] == 0.8688
    assert best["precision"] == 0.8272
    assert best["recall"] == 0.8999
    assert best["f1Score"] == 0.862
    assert best["aucRoc"] == 0.941
    assert best["prAuc"] == 0.9189
    assert best["tp"] == 4102
    assert best["tn"] == 4585
    assert best["fp"] == 857
    assert best["fn"] == 456


def test_performance_models_include_confusion_fields(client):
    with client.application.app_context():
        db.session.add(
            Performance(
                model_name="EfficientB3",
                accuracy=0.8165,
                precision=0.7801,
                recall=0.8316,
                f1_score=0.8050,
                fpr=0.1961,
                fnr=0.1684,
                tnr=0.8039,
                tp=3787,
                tn=4378,
                fp=1068,
                fn=767,
                auc_roc=0.8988,
                pr_auc=0.8688,
                confusion_matrix="[[4378,1068],[767,3787]]",
            )
        )
        db.session.commit()

    response = client.get("/api/performance")

    assert response.status_code == 200
    data = response.get_json()

    assert len(data["models"]) == 1
    row = data["models"][0]

    assert row["modelName"] == "EfficientB3"
    assert row["tp"] == 3787
    assert row["tn"] == 4378
    assert row["fp"] == 1068
    assert row["fn"] == 767
    assert row["fpr"] == 0.1961
    assert row["fnr"] == 0.1684
    assert row["tnr"] == 0.8039
    assert row["confusionMatrix"] == "[[4378,1068],[767,3787]]"
