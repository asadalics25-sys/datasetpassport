import json
from datetime import datetime, timezone
from fastapi import FastAPI, Depends, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from .database import Base, engine, get_db
from .models import User, Experiment
from .schemas import RegisterRequest, LoginRequest, TokenResponse, ExperimentCreate, CompareRequest
from .security import hash_password, verify_password, create_access_token, current_user
from .audit import audit_csv
from .ml_training import train_classifier
from .config import FRONTEND_ORIGIN, MAX_UPLOAD_BYTES

Base.metadata.create_all(bind=engine)

app = FastAPI(title="DatasetPassport API", version="0.1.0",
              description="Dataset auditing and ML experiment reproducibility starter project.")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_ORIGIN, "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type"],
)

@app.get("/api/health")
def health():
    return {"status": "ok", "service": "DatasetPassport API"}

@app.post("/api/auth/register", status_code=201)
def register(payload: RegisterRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    user = User(email=email, password_hash=hash_password(payload.password))
    db.add(user)
    try:
        db.commit()
        db.refresh(user)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=409, detail="An account with this email already exists")
    return {"id": user.id, "email": user.email}

@app.post("/api/auth/login", response_model=TokenResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)):
    email = payload.email.lower().strip()
    user = db.query(User).filter(User.email == email).first()
    if not user or not verify_password(payload.password, user.password_hash):
        raise HTTPException(status_code=401, detail="Incorrect email or password")
    return {"access_token": create_access_token(user.id), "token_type": "bearer"}

@app.get("/api/me")
def me(user: User = Depends(current_user)):
    return {"id": user.id, "email": user.email}

@app.post("/api/datasets/audit")
async def dataset_audit(
    file: UploadFile = File(...),
    target_column: str | None = Form(default=None),
    user: User = Depends(current_user),
):
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only .csv files are supported")
    if file.content_type not in ("text/csv", "application/vnd.ms-excel", "application/octet-stream", None):
        raise HTTPException(status_code=415, detail="Unexpected content type for CSV upload")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit")
    if not raw:
        raise HTTPException(status_code=400, detail="Uploaded file is empty")
    try:
        result = audit_csv(raw, target_column.strip() if target_column and target_column.strip() else None)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    result["filename"] = file.filename[:180]
    result["note"] = "CSV processed in memory; raw upload is not stored by this endpoint."
    return result

@app.post("/api/ml/train", status_code=201)
async def train_ml_model(
    file: UploadFile = File(...),
    target_column: str = Form(...),
    model_type: str = Form("logistic_regression"),
    experiment_name: str = Form("Trained classification run"),
    random_seed: int = Form(42),
    db: Session = Depends(get_db),
    user: User = Depends(current_user),
):
    """Train a real classifier and persist only its metadata and held-out metrics."""
    if not file.filename or not file.filename.lower().endswith(".csv"):
        raise HTTPException(status_code=415, detail="Only .csv files are supported")
    if random_seed < 0 or random_seed > 2147483647:
        raise HTTPException(status_code=400, detail="Random seed must be between 0 and 2147483647")
    if not experiment_name.strip() or len(experiment_name.strip()) > 120:
        raise HTTPException(status_code=400, detail="Experiment name must be 1–120 characters")
    raw = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(raw) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail=f"File exceeds {MAX_UPLOAD_BYTES // (1024*1024)} MB limit")
    try:
        result = train_classifier(raw, file.filename, target_column.strip(), model_type, random_seed)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    experiment = Experiment(
        user_id=user.id,
        name=experiment_name.strip(),
        model_name=result["model_name"],
        dataset_name=result["dataset_name"],
        dataset_fingerprint=result["dataset_fingerprint"],
        target_column=result["target_column"],
        random_seed=result["random_seed"],
        preprocessing=result["preprocessing"],
        configuration_json=json.dumps(result["configuration"], allow_nan=False),
        metrics_json=json.dumps(result["metrics"], allow_nan=False),
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return serialize_experiment(experiment)


@app.post("/api/experiments", status_code=201)
def create_experiment(payload: ExperimentCreate, db: Session = Depends(get_db), user: User = Depends(current_user)):
    experiment = Experiment(
        user_id=user.id,
        name=payload.name.strip(),
        model_name=payload.model_name.strip(),
        dataset_name=payload.dataset_name.strip(),
        dataset_fingerprint=payload.dataset_fingerprint.lower(),
        target_column=payload.target_column,
        random_seed=payload.random_seed,
        preprocessing=payload.preprocessing,
        configuration_json=json.dumps(payload.configuration, allow_nan=False),
        metrics_json=json.dumps(payload.metrics, allow_nan=False),
    )
    db.add(experiment)
    db.commit()
    db.refresh(experiment)
    return serialize_experiment(experiment)

@app.get("/api/experiments")
def list_experiments(db: Session = Depends(get_db), user: User = Depends(current_user)):
    items = db.query(Experiment).filter(Experiment.user_id == user.id).order_by(Experiment.created_at.desc()).limit(100).all()
    return [serialize_experiment(item) for item in items]

@app.get("/api/experiments/{experiment_id}")
def get_experiment(experiment_id: int, db: Session = Depends(get_db), user: User = Depends(current_user)):
    item = owned_experiment(db, experiment_id, user.id)
    return serialize_experiment(item)

@app.post("/api/experiments/compare")
def compare_experiments(payload: CompareRequest, db: Session = Depends(get_db), user: User = Depends(current_user)):
    a = owned_experiment(db, payload.experiment_a_id, user.id)
    b = owned_experiment(db, payload.experiment_b_id, user.id)
    ma, mb = json.loads(a.metrics_json), json.loads(b.metrics_json)
    metric_deltas = {}
    for key in sorted(set(ma) & set(mb)):
        if isinstance(ma[key], (int, float)) and isinstance(mb[key], (int, float)):
            metric_deltas[key] = round(float(mb[key]) - float(ma[key]), 6)
    hints = []
    if a.dataset_fingerprint != b.dataset_fingerprint:
        hints.append("Dataset fingerprints differ. Check whether the data version, row order, encoding or file contents changed.")
    if a.random_seed != b.random_seed:
        hints.append("Random seeds differ or are missing; stochastic training may not be directly comparable.")
    if a.preprocessing != b.preprocessing:
        hints.append("Preprocessing notes differ. Compare cleaning, scaling, feature selection and split strategy.")
    ca, cb = json.loads(a.configuration_json), json.loads(b.configuration_json)
    changed_keys = sorted(k for k in set(ca) | set(cb) if ca.get(k) != cb.get(k))
    if changed_keys:
        hints.append("Configuration differs for: " + ", ".join(changed_keys[:20]) + ".")
    if a.target_column != b.target_column:
        hints.append("Target columns differ; verify that the metrics measure the same prediction task.")
    if not hints:
        hints.append("No differences were found in the tracked metadata. Unrecorded factors may still explain metric changes.")
    return {
        "experiment_a": serialize_experiment(a),
        "experiment_b": serialize_experiment(b),
        "metric_deltas_b_minus_a": metric_deltas,
        "changed_configuration_keys": changed_keys,
        "diagnostic_hints": hints,
        "interpretation_note": "These are diagnostic clues, not proof of causation. Metric deltas depend on the metric definition and evaluation data.",
    }

def owned_experiment(db: Session, experiment_id: int, user_id: int):
    item = db.query(Experiment).filter(Experiment.id == experiment_id, Experiment.user_id == user_id).first()
    if not item:
        # Do not reveal whether another user's ID exists.
        raise HTTPException(status_code=404, detail="Experiment not found")
    return item

def serialize_experiment(item: Experiment):
    return {
        "id": item.id,
        "name": item.name,
        "model_name": item.model_name,
        "dataset_name": item.dataset_name,
        "dataset_fingerprint": item.dataset_fingerprint,
        "target_column": item.target_column,
        "random_seed": item.random_seed,
        "preprocessing": item.preprocessing,
        "configuration": json.loads(item.configuration_json),
        "metrics": json.loads(item.metrics_json),
        "created_at": item.created_at.isoformat() if item.created_at else None,
    }
