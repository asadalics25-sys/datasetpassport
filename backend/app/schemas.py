from pydantic import BaseModel, EmailStr, Field, ConfigDict
from typing import Any

class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=10, max_length=128)

class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1, max_length=128)

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"

class ExperimentCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    model_name: str = Field(min_length=1, max_length=120)
    dataset_name: str = Field(min_length=1, max_length=180)
    dataset_fingerprint: str = Field(pattern=r"^[a-fA-F0-9]{64}$")
    target_column: str | None = Field(default=None, max_length=180)
    random_seed: int | None = Field(default=None, ge=0, le=2147483647)
    preprocessing: str = Field(default="", max_length=5000)
    configuration: dict[str, Any] = Field(default_factory=dict)
    metrics: dict[str, float] = Field(default_factory=dict)

class ExperimentOut(BaseModel):
    id: int
    name: str
    model_name: str
    dataset_name: str
    dataset_fingerprint: str
    target_column: str | None
    random_seed: int | None
    preprocessing: str
    configuration: dict[str, Any]
    metrics: dict[str, float]
    created_at: str

class CompareRequest(BaseModel):
    experiment_a_id: int
    experiment_b_id: int
