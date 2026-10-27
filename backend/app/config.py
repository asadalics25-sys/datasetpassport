import os
from dotenv import load_dotenv

load_dotenv()

JWT_SECRET = os.getenv("JWT_SECRET", "dev-only-change-me")
JWT_ALGORITHM = os.getenv("JWT_ALGORITHM", "HS256")
ACCESS_TOKEN_MINUTES = int(os.getenv("ACCESS_TOKEN_MINUTES", "60"))
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./datasetpassport.db")
FRONTEND_ORIGIN = os.getenv("FRONTEND_ORIGIN", "http://localhost:5173")
MAX_UPLOAD_BYTES = int(os.getenv("MAX_UPLOAD_BYTES", str(10 * 1024 * 1024)))

if JWT_SECRET == "dev-only-change-me":
    # Convenient for local development; production deployments must configure a secret.
    print("WARNING: using development JWT secret. Set JWT_SECRET in .env before deployment.")
