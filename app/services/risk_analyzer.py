"""
Risk Analyzer — runs as a Celery background task after document upload.

Scans every clause against known risky legal patterns and scores them
using the LLM. Results are stored in PostgreSQL and returned via API.
"""
import asyncio
import json
from openai import OpenAI
from app.core.celery_app import celery_app
from app.core.config import settings

llm_client = OpenAI(api_key="ollama", base_url=settings.llm_base_url)

RISK_CATEGORIES = {
    "unlimited_liability": "Clauses that expose a party to unlimited or uncapped financial liability",
    "auto_renewal": "Clauses that auto-renew the contract without explicit notice requirements",
    "unilateral_modification": "Clauses that allow one party to change terms without consent",
    "broad_ip_assignment": "Clauses that assign IP rights too broadly, including pre-existing IP",
    "one_sided_termination": "Clauses that give only one party termination rights",
    "punitive_penalty": "Clauses with disproportionate penalties or liquidated damages",
    "jurisdiction_unfavorable": "Clauses that impose unfavorable jurisdiction or governing law",
    "non_compete_broad": "Non-compete clauses that are overly broad in scope, geography, or duration",
    "indemnification_broad": "Broad indemnification clauses that could expose to third-party claims",
    "data_privacy_risk": "Clauses allowing excessive data collection, sharing, or unclear data rights",
}

RISK_ANALYSIS_PROMPT = """You are a legal risk analyst reviewing contract clauses.

For the given clause, determine if it contains any of these risk types:
{risk_categories}

Respond with a JSON object:
{{
  "has_risk": true/false,
  "risk_type": "category_key or null",
  "severity": "low|medium|high|critical or null",
  "explanation": "brief explanation of the risk in plain English",
  "recommendation": "what to negotiate or change"
}}

Only flag genuine risks. If the clause is standard and fair, set has_risk to false.
"""


@celery_app.task(name="analyze_document_risks", bind=True, max_retries=3)
def analyze_document_risks(self, document_id: str):
    """
    Background task: analyze all clauses in a document for legal risks.
    Triggered automatically after successful document indexing.
    """
    try:
        # Import here to avoid circular imports at module level
        from app.services.vector_store import get_all_clauses
        from app.models.db import RiskAnalysis
        # Use sync DB session for Celery
        from sqlalchemy import create_engine
        from sqlalchemy.orm import Session

        sync_db_url = settings.database_url.replace("+asyncpg", "+psycopg2")
        engine = create_engine(sync_db_url)

        # Get all clauses from Qdrant
        clauses = asyncio.run(get_all_clauses(document_id))

        if not clauses:
            _update_risk_status(engine, document_id, "failed", [], 0.0)
            return

        risk_findings = []
        risk_categories_text = "\n".join(
            f"- {k}: {v}" for k, v in RISK_CATEGORIES.items()
        )

        for clause in clauses:
            clause_text = clause.get("text", "")
            if len(clause_text.strip()) < 50:
                continue  # Skip very short clauses

            finding = _analyze_clause(clause, risk_categories_text)
            if finding:
                risk_findings.append(finding)

        # Score 0-10 based on severity distribution
        overall_score = _calculate_risk_score(risk_findings)

        _update_risk_status(engine, document_id, "done", risk_findings, overall_score)

    except Exception as exc:
        raise self.retry(exc=exc, countdown=30)


def _analyze_clause(clause: dict, risk_categories_text: str) -> dict | None:
    """Analyze a single clause for risks. Returns finding dict or None."""
    try:
        prompt = RISK_ANALYSIS_PROMPT.format(risk_categories=risk_categories_text)
        prompt += f"\n\nClause to analyze:\n{clause['text'][:1500]}"

        response = llm_client.chat.completions.create(
            model=settings.ollama_model,
            messages=[{"role": "user", "content": prompt}],
            temperature=0,
            max_tokens=300,
        )

        result = json.loads(response.choices[0].message.content)

        if result.get("has_risk") and result.get("risk_type"):
            return {
                "clause_text": clause["text"][:500],
                "page": clause.get("page", 0),
                "risk_type": result["risk_type"],
                "severity": result.get("severity", "medium"),
                "explanation": result.get("explanation", ""),
                "recommendation": result.get("recommendation", ""),
            }
    except Exception:
        pass  # Skip clauses that fail analysis

    return None


def _calculate_risk_score(findings: list[dict]) -> float:
    """Calculate overall risk score 0-10."""
    if not findings:
        return 0.0

    severity_weights = {"low": 1, "medium": 3, "high": 6, "critical": 10}
    total = sum(severity_weights.get(f["severity"], 2) for f in findings)
    # Normalize: 10+ weighted points = score of 10
    return min(10.0, round(total / max(len(findings), 1), 1))


def _update_risk_status(engine, document_id: str, status: str, risks: list, score: float):
    from sqlalchemy.orm import Session
    from app.models.db import RiskAnalysis

    with Session(engine) as session:
        analysis = session.query(RiskAnalysis).filter_by(document_id=document_id).first()
        if analysis:
            analysis.status = status
            analysis.risks = risks
            analysis.overall_risk_score = score
            session.commit()
