# DatasetPassport ML training upgrade

## Apply this upgrade to your existing local project

1. Stop the frontend and backend servers with `Ctrl+C` in their terminals.
2. Make a backup copy of `backend/app/main.py` and `frontend/src/App.jsx`.
3. Extract this upgrade ZIP into the existing project root, the folder that contains `backend` and `frontend`. Allow the replacement of `backend/app/main.py` and `frontend/src/App.jsx`.
4. Confirm the new file `backend/app/ml_training.py` and test `backend/tests/test_ml_training.py` were added. No new Python package is required; the existing requirements already include pandas and scikit-learn.
5. Start the backend from `backend` with `python -m uvicorn app.main:app --reload` (or `..\.venv\Scripts\python.exe -m uvicorn app.main:app --reload` if running from the project root and your environment is at `backend\.venv`).
6. Start the frontend from `frontend` with `npm.cmd run dev`.
7. Sign in, open **Train a model**, select a CSV and target column, choose Logistic Regression or Decision Tree, and click **Train, evaluate and save run**.
8. From a backend terminal, run `..\.venv\Scripts\python.exe -m pytest -v` from the backend directory (or activate your venv and run `python -m pytest -v`).

The new endpoint uses a stratified held-out test split and fits preprocessing only on the training split. It saves the measured metrics and run configuration to the existing experiment table, so no database schema migration is required.

## Limitations to explain in a demo

- Classification only; no regression or time-series split yet.
- Tiny datasets produce unstable metrics; the 12-row included sample is only a smoke test.
- A held-out split is not a substitute for cross-validation or external validation on larger projects.
- Do not include identifiers or post-outcome columns as features; those can cause data leakage.
- Training results are diagnostic, not proof of real-world model quality.
