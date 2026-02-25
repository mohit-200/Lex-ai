"""
Tests for LegalDoc AI core services.
Run with: pytest tests/ -v
"""
import pytest
from app.services.parser import parse_pdf, _merge_short_clauses, Clause


# ── Parser Tests ────────────────────────────────────────────────────────────

class TestClauseParser:

    def test_merge_short_clauses(self):
        clauses = [
            Clause(text="Short", page=1, clause_number="1", section_title=None, char_start=0, char_end=5),
            Clause(text="A" * 200, page=1, clause_number="2", section_title=None, char_start=5, char_end=205),
        ]
        merged = _merge_short_clauses(clauses, min_length=100)
        # Short clause should be merged with next
        assert len(merged) == 1
        assert "Short" in merged[0].text
        assert "A" * 200 in merged[0].text

    def test_empty_pdf_bytes_raises(self):
        with pytest.raises(Exception):
            parse_pdf(b"not a real pdf")

    def test_clause_number_preserved(self):
        clauses = [
            Clause(text="A" * 150, page=1, clause_number="3.2", section_title="Payment Terms", char_start=0, char_end=150),
        ]
        merged = _merge_short_clauses(clauses)
        assert merged[0].clause_number == "3.2"
        assert merged[0].section_title == "Payment Terms"


# ── Schema Tests ────────────────────────────────────────────────────────────

class TestSchemas:

    def test_query_response_confidence_range(self):
        from app.models.schemas import QueryResponse, SourceClause
        response = QueryResponse(
            answer="Test answer",
            confidence=0.85,
            is_confident=True,
            sources=[],
            latency_ms=250,
        )
        assert 0.0 <= response.confidence <= 1.0
        assert response.is_confident is True

    def test_risk_finding_severity_values(self):
        from app.models.schemas import RiskFinding
        finding = RiskFinding(
            clause_text="Test clause",
            page=3,
            risk_type="unlimited_liability",
            severity="high",
            explanation="This clause has no liability cap",
            recommendation="Negotiate a cap of 2x contract value",
        )
        assert finding.severity in ["low", "medium", "high", "critical"]


# ── Integration Tests (require running services) ────────────────────────────

@pytest.mark.integration
@pytest.mark.asyncio
async def test_upload_and_query_flow():
    """
    End-to-end test: upload a PDF, query it, check response structure.
    Requires: docker-compose up
    """
    import httpx

    async with httpx.AsyncClient(base_url="http://localhost:8000") as client:
        # Upload a test PDF
        with open("tests/fixtures/sample_contract.pdf", "rb") as f:
            upload_response = await client.post(
                "/documents/upload",
                files={"file": ("test.pdf", f, "application/pdf")},
            )

        assert upload_response.status_code == 200
        doc_id = upload_response.json()["document_id"]
        assert upload_response.json()["chunk_count"] > 0

        # Query the document
        query_response = await client.post(
            f"/documents/{doc_id}/query",
            json={"query": "What are the payment terms?"},
        )

        assert query_response.status_code == 200
        data = query_response.json()
        assert "answer" in data
        assert "confidence" in data
        assert "sources" in data
        assert isinstance(data["is_confident"], bool)
        assert len(data["sources"]) > 0

        # Cleanup
        await client.delete(f"/documents/{doc_id}")
