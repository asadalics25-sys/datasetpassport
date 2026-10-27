import io
from app.audit import audit_csv

def test_fingerprint_and_counts():
    raw = b"feature,label\n1,A\n2,B\n2,B\n, A\n"
    result = audit_csv(raw, "label")
    assert len(result["dataset_fingerprint"]) == 64
    assert result["rows"] == 4
    assert result["columns_count"] == 2
    assert result["duplicate_rows"] == 1
    assert result["missing_cells"] == 1
    assert result["class_balance"] is not None

def test_identical_bytes_same_fingerprint():
    raw = b"x,y\n1,0\n2,1\n"
    assert audit_csv(raw)["dataset_fingerprint"] == audit_csv(raw)["dataset_fingerprint"]
