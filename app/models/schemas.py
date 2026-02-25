from pydantic import BaseModel
from typing import Optional
from datetime import datetime


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
    confidence: float          # 0.0 – 1.0
    is_confident: bool         # False = low confidence, user should verify
    sources: list[SourceClause]
    latency_ms: int


# ── Risk Analysis ─────────────────────────────────────────
class RiskFinding(BaseModel):
    clause_text: str
    page: int
    risk_type: str             # e.g. "unlimited_liability", "auto_renewal"
    severity: str              # low | medium | high | critical
    explanation: str
    recommendation: str


class RiskAnalysisResponse(BaseModel):
    document_id: str
    status: str
    overall_risk_score: Optional[float]   # 0-10
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
