import hashlib
import io
import pandas as pd
import numpy as np
from sklearn.ensemble import IsolationForest

MAX_ROWS = 200_000
MAX_COLUMNS = 300

def audit_csv(raw: bytes, target_column: str | None = None) -> dict:
    # Fingerprint the original bytes, not the parsed dataframe.
    fingerprint = hashlib.sha256(raw).hexdigest()
    try:
        df = pd.read_csv(io.BytesIO(raw), low_memory=False)
    except Exception as exc:
        raise ValueError("Could not parse CSV. Check the delimiter, encoding and header row.") from exc

    if df.empty:
        raise ValueError("The CSV contains no data rows.")
    if len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ValueError(f"Dataset is too large to audit in this MVP (max {MAX_ROWS} rows and {MAX_COLUMNS} columns).")
    if any(str(c).startswith("Unnamed:") for c in df.columns):
        unnamed = [str(c) for c in df.columns if str(c).startswith("Unnamed:")]
    else:
        unnamed = []

    missing = df.isna().sum()
    duplicate_rows = int(df.duplicated().sum())
    columns = []
    for col in df.columns:
        series = df[col]
        item = {
            "name": str(col),
            "dtype": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percent": round(float(series.isna().mean() * 100), 2),
            "unique_count": int(series.nunique(dropna=True)),
        }
        if pd.api.types.is_numeric_dtype(series):
            clean = series.dropna()
            if len(clean):
                item["numeric_summary"] = {
                    "min": finite_or_none(clean.min()),
                    "max": finite_or_none(clean.max()),
                    "mean": finite_or_none(clean.mean()),
                    "std": finite_or_none(clean.std()),
                }
        columns.append(item)

    class_balance = None
    if target_column:
        if target_column not in df.columns:
            raise ValueError("Target column was not found in the CSV.")
        counts = df[target_column].fillna("<MISSING>").astype(str).value_counts().head(30)
        class_balance = [{"label": str(label)[:120], "count": int(count)} for label, count in counts.items()]

    outlier_summary = []
    numeric = df.select_dtypes(include=[np.number]).replace([np.inf, -np.inf], np.nan)
    for col in numeric.columns[:30]:
        values = numeric[col].dropna()
        if len(values) >= 20 and values.nunique() > 1:
            sample = values.to_numpy().reshape(-1, 1)
            # Keep computation bounded for the web request.
            if len(sample) > 5000:
                sample = sample[np.linspace(0, len(sample)-1, 5000).astype(int)]
            try:
                model = IsolationForest(contamination="auto", random_state=42, n_estimators=50)
                labels = model.fit_predict(sample)
                outlier_summary.append({
                    "column": str(col),
                    "sample_size": int(len(sample)),
                    "flagged_count": int((labels == -1).sum()),
                    "flagged_percent": round(float((labels == -1).mean() * 100), 2),
                })
            except Exception:
                continue

    warnings = []
    if duplicate_rows:
        warnings.append({"level": "warning", "code": "DUPLICATE_ROWS", "message": f"{duplicate_rows} exact duplicate rows found. Review whether duplicates are expected."})
    if int(missing.sum()):
        warnings.append({"level": "warning", "code": "MISSING_VALUES", "message": f"{int(missing.sum())} missing cells found across the dataset."})
    if unnamed:
        warnings.append({"level": "info", "code": "UNNAMED_COLUMNS", "message": f"Possible exported index columns detected: {', '.join(unnamed[:5])}."})
    if target_column and class_balance and len(class_balance) > 1:
        counts = [x["count"] for x in class_balance]
        if min(counts) > 0 and max(counts) / min(counts) >= 5:
            warnings.append({"level": "warning", "code": "CLASS_IMBALANCE", "message": "The most common target class is at least 5 times as frequent as the least common class."})
    warnings.append({"level": "info", "code": "LEAKAGE_LIMITATION", "message": "This audit does not prove train/test leakage is absent. Compare split IDs and check for target-derived features separately."})

    return {
        "dataset_fingerprint": fingerprint,
        "file_bytes": len(raw),
        "rows": int(df.shape[0]),
        "columns_count": int(df.shape[1]),
        "duplicate_rows": duplicate_rows,
        "missing_cells": int(missing.sum()),
        "columns": columns,
        "class_balance": class_balance,
        "outlier_summary": outlier_summary,
        "warnings": warnings,
    }

def finite_or_none(value):
    try:
        value = float(value)
        return value if np.isfinite(value) else None
    except (TypeError, ValueError):
        return None
