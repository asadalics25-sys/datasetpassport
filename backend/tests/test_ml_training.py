import pytest
from app.ml_training import train_classifier

CSV = b"""hours,category,label
1,A,fail
2,A,fail
3,B,fail
4,B,pass
5,A,pass
6,B,pass
2,C,fail
7,C,pass
3,A,fail
8,B,pass
4,C,pass
9,A,pass
"""

def test_training_uses_held_out_rows_and_returns_metrics():
    result = train_classifier(CSV, "tiny.csv", "label", "logistic_regression", 42)
    assert len(result["dataset_fingerprint"]) == 64
    assert result["configuration"]["actual_train_rows"] + result["configuration"]["actual_test_rows"] == 12
    assert result["configuration"]["metrics_evaluated_on"] == "held-out test split"
    assert set(result["metrics"]) == {"accuracy", "balanced_accuracy", "precision_macro", "recall_macro", "f1_macro"}
    assert all(0.0 <= score <= 1.0 for score in result["metrics"].values())

def test_training_rejects_unknown_target():
    with pytest.raises(ValueError, match="target column"):
        train_classifier(CSV, "tiny.csv", "not_a_column", "logistic_regression", 42)

def test_training_rejects_single_class_target():
    raw = b"x,label\n1,A\n2,A\n3,A\n4,A\n5,A\n6,A\n7,A\n8,A\n9,A\n10,A\n"
    with pytest.raises(ValueError, match="at least two classes"):
        train_classifier(raw, "single.csv", "label", "decision_tree", 42)
