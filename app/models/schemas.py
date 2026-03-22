from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime


# ── Auth ──────────────────────────────────────────────────
class RegisterRequest(BaseModel):
    email: EmailStr
    full_name: str
    password: str


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user_id: str
    full_name: str
    email: str


class ForgotPasswordRequest(BaseModel):
    email: EmailStr

class ResetPasswordRequest(BaseModel):
    token: str
    new_password: str


# ── Document ──────────────────────────────────────────────
class DocumentUploadResponse(BaseModel):
    document_id: str
    filename: str
    page_count: int
    chunk_count: int
    status: str
    message: str


class DocumentStatusResponse(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: int
    page_count: int
    file_size_bytes: int
    created_at: datetime


class DocumentListItem(BaseModel):
    document_id: str
    filename: str
    status: str
    chunk_count: int
    page_count: int
    file_size_bytes: int
    created_at: datetime


# ── Query ─────────────────────────────────────────────────
class QueryRequest(BaseModel):
    query: str
    top_k: Optional[int] = 6


class SourceClause(BaseModel):
    text: str
    page: int
    clause_number: Optional[str]
    similarity_score: float


class QueryResponse(BaseModel):
    answer: str
    confidence: float
    is_confident: bool
    sources: list[SourceClause]
    latency_ms: int


# ── Risk Analysis ─────────────────────────────────────────
class RiskFinding(BaseModel):
    clause_text: str
    page: int
    risk_type: str
    severity: str              # low | medium | high | critical
    explanation: str
    recommendation: str


class RiskAnalysisResponse(BaseModel):
    document_id: str
    status: str
    overall_risk_score: Optional[float]
    risk_count: int
    risks: list[RiskFinding]


# ── Comparison ────────────────────────────────────────────
class ClauseDiff(BaseModel):
    section: str
    original_text: str
    revised_text: str
    change_type: str           # added | removed | modified
    significance: str          # low | medium | high
    explanation: str


class ComparisonResponse(BaseModel):
    total_changes: int
    high_significance_count: int
    diffs: list[ClauseDiff]
