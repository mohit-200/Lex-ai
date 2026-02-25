import json
from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from openai import AsyncOpenAI

from app.models.schemas import RiskAnalysisResponse, RiskFinding, ComparisonResponse, ClauseDiff
from app.models.db import RiskAnalysis, Document
from app.services.parser import parse_pdf
from app.core.config import settings
from app.api.deps import get_db

router = APIRouter(tags=["Risk & Comparison"])
client = AsyncOpenAI(api_key=settings.openai_api_key)


@router.get("/documents/{document_id}/risks", response_model=RiskAnalysisResponse)
async def get_risk_analysis(document_id: str, db: AsyncSession = Depends(get_db)):
    """
    Get the automated risk analysis for a document.
    Risk analysis runs in the background after upload — check status first.
    """
    result = await db.execute(select(RiskAnalysis).where(RiskAnalysis.document_id == document_id))
    analysis = result.scalar_one_or_none()

    if not analysis:
        raise HTTPException(status_code=404, detail="Risk analysis not found for this document.")

    if analysis.status == "pending":
        return RiskAnalysisResponse(
            document_id=document_id,
            status="pending",
            overall_risk_score=None,
            risk_count=0,
            risks=[],
        )

    risks = [RiskFinding(**r) for r in (analysis.risks or [])]

    return RiskAnalysisResponse(
        document_id=document_id,
        status=analysis.status,
        overall_risk_score=analysis.overall_risk_score,
        risk_count=len(risks),
        risks=risks,
    )


@router.post("/compare", response_model=ComparisonResponse)
async def compare_documents(
    original: UploadFile = File(...),
    revised: UploadFile = File(...),
):
    """
    Compare two versions of a contract.
    Returns clause-level diffs with LLM-generated explanations of what changed and why it matters.
    """
    original_bytes = await original.read()
    revised_bytes = await revised.read()

    original_clauses = parse_pdf(original_bytes)
    revised_clauses = parse_pdf(revised_bytes)

    # Build text summaries for LLM comparison
    original_text = "\n\n".join(
        f"[{c.clause_number or 'Section'}] {c.text[:400]}" for c in original_clauses[:30]
    )
    revised_text = "\n\n".join(
        f"[{c.clause_number or 'Section'}] {c.text[:400]}" for c in revised_clauses[:30]
    )

    prompt = f"""You are a legal contract comparison expert.

Compare these two contract versions and identify meaningful changes (ignore whitespace/formatting).

ORIGINAL CONTRACT:
{original_text}

REVISED CONTRACT:
{revised_text}

Return a JSON object with this exact structure:
{{
  "diffs": [
    {{
      "section": "section name or number",
      "original_text": "original clause text (truncated)",
      "revised_text": "revised clause text (truncated)",
      "change_type": "added|removed|modified",
      "significance": "low|medium|high",
      "explanation": "plain English explanation of what changed and why it matters legally"
    }}
  ]
}}

Focus on substantive legal changes. Ignore minor wording tweaks.
Maximum 20 diffs. Order by significance (high first).
"""

    response = await client.chat.completions.create(
        model=settings.openai_model,
        messages=[{"role": "user", "content": prompt}],
        temperature=0,
        max_tokens=2000,
        response_format={"type": "json_object"},
    )

    result = json.loads(response.choices[0].message.content)
    diffs = [ClauseDiff(**d) for d in result.get("diffs", [])]
    high_count = sum(1 for d in diffs if d.significance == "high")

    return ComparisonResponse(
        total_changes=len(diffs),
        high_significance_count=high_count,
        diffs=diffs,
    )
