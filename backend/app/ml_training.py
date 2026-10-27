"""Small, reproducible supervised-classification training pipeline."""
import hashlib
import io
import math

import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score, precision_score, recall_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler
from sklearn.tree import DecisionTreeClassifier

MAX_ROWS = 200_000
MAX_COLUMNS = 300


def train_classifier(raw: bytes, filename: str, target_column: str, model_type: str, random_seed: int):
    """Train/evaluate a classifier; fit preprocessing on training rows only."""
    if not raw:
        raise ValueError("Uploaded file is empty.")
    if model_type not in {"logistic_regression", "decision_tree"}:
        raise ValueError("Unsupported model. Choose logistic_regression or decision_tree.")
    try:
        df = pd.read_csv(io.BytesIO(raw), low_memory=False)
    except Exception as exc:
        raise ValueError("Could not parse the CSV. Check its encoding, delimiter and header.") from exc
    if df.empty:
        raise ValueError("The CSV contains no data rows.")
    if len(df) > MAX_ROWS or len(df.columns) > MAX_COLUMNS:
        raise ValueError(f"Dataset exceeds this MVP's limit of {MAX_ROWS} rows and {MAX_COLUMNS} columns.")
    if not target_column or target_column not in df.columns:
        raise ValueError("Select a target column that exists in the CSV header.")

    # Rows with unknown labels cannot be used for supervised training/evaluation.
    df = df.dropna(subset=[target_column]).copy()
    if len(df) < 10:
        raise ValueError("At least 10 rows with non-missing target values are required.")
    y = df[target_column]
    if y.nunique(dropna=True) < 2:
        raise ValueError("The target must contain at least two classes for classification.")
    class_counts = y.value_counts()
    if int(class_counts.min()) < 2:
        raise ValueError("Each target class needs at least two rows for a stratified train/test split.")

    X = df.drop(columns=[target_column])
    # Entirely empty feature columns carry no learnable information.
    X = X.loc[:, ~X.isna().all()]
    if X.shape[1] == 0:
        raise ValueError("No usable feature columns remain after removing the target and empty columns.")

    # Keep at least one test example per class, while targeting a 25% test set.
    n_classes = int(y.nunique())
    test_rows = max(math.ceil(len(df) * 0.25), n_classes)
    if len(df) - test_rows < n_classes or test_rows >= len(df):
        raise ValueError("Not enough rows to place every class in both train and test sets. Add more examples per class.")
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=test_rows, random_state=random_seed, stratify=y
    )

    numeric_columns = X.select_dtypes(include="number").columns.tolist()
    categorical_columns = [c for c in X.columns if c not in numeric_columns]
    transformers = []
    if numeric_columns:
        numeric_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ])
        transformers.append(("numeric", numeric_pipeline, numeric_columns))
    if categorical_columns:
        categorical_pipeline = Pipeline([
            ("imputer", SimpleImputer(strategy="most_frequent")),
            ("onehot", OneHotEncoder(handle_unknown="ignore")),
        ])
        transformers.append(("categorical", categorical_pipeline, categorical_columns))
    preprocess = ColumnTransformer(transformers=transformers, remainder="drop")

    if model_type == "logistic_regression":
        classifier = LogisticRegression(max_iter=1000, random_state=random_seed)
        display_name = "LogisticRegression"
    else:
        classifier = DecisionTreeClassifier(max_depth=5, random_state=random_seed)
        display_name = "DecisionTreeClassifier"

    # The entire preprocessing + model pipeline is fitted on training data only.
    pipeline = Pipeline([("preprocess", preprocess), ("model", classifier)])
    try:
        pipeline.fit(X_train, y_train)
        predictions = pipeline.predict(X_test)
    except Exception as exc:
        raise ValueError(f"Training failed. Check that the feature columns contain usable values. Details: {exc}") from exc

    metrics = {
        "accuracy": round(float(accuracy_score(y_test, predictions)), 6),
        "balanced_accuracy": round(float(balanced_accuracy_score(y_test, predictions)), 6),
        "precision_macro": round(float(precision_score(y_test, predictions, average="macro", zero_division=0)), 6),
        "recall_macro": round(float(recall_score(y_test, predictions, average="macro", zero_division=0)), 6),
        "f1_macro": round(float(f1_score(y_test, predictions, average="macro", zero_division=0)), 6),
    }
    fingerprint = hashlib.sha256(raw).hexdigest()
    configuration = {
        "task": "classification",
        "model_type": model_type,
        "random_seed": int(random_seed),
        "test_size_fraction_target": 0.25,
        "actual_test_rows": int(len(X_test)),
        "actual_train_rows": int(len(X_train)),
        "stratified_split": True,
        "feature_columns": [str(c) for c in X.columns],
        "target_classes": [str(v) for v in sorted(y.astype(str).unique())],
        "metrics_evaluated_on": "held-out test split",
    }
    preprocessing_note = (
        "Stratified train/test split; median imputation and scaling for numeric features; "
        "most-frequent imputation and one-hot encoding for categorical features. "
        "All preprocessing was fitted on training rows only."
    )
    return {
        "model_name": display_name,
        "dataset_name": (filename or "uploaded.csv")[:180],
        "dataset_fingerprint": fingerprint,
        "target_column": target_column,
        "random_seed": int(random_seed),
        "preprocessing": preprocessing_note,
        "configuration": configuration,
        "metrics": metrics,
    }
