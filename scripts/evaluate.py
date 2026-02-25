"""
RAGAS Evaluation Script

Evaluates RAG pipeline quality across 3 key metrics:
- Faithfulness: Is the answer grounded in the retrieved context?
- Answer Relevancy: Does the answer address the question?
- Context Precision: Are the retrieved chunks actually relevant?

Run this after building a test dataset to benchmark your pipeline.
Usage: python scripts/evaluate.py
"""
import asyncio
import httpx
from datasets import Dataset
from ragas import evaluate
from ragas.metrics import faithfulness, answer_relevancy, context_precision

API_BASE = "http://localhost:8000"

# Test cases — build these from real contract questions
# For each: the question, expected answer theme, document_id to query
TEST_CASES = [
    {
        "question": "What are the payment terms in this contract?",
        "document_id": "your-doc-id-here",
    },
    {
        "question": "What happens if either party wants to terminate early?",
        "document_id": "your-doc-id-here",
    },
    {
        "question": "Does this contract have a non-compete clause? What are its terms?",
        "document_id": "your-doc-id-here",
    },
    {
        "question": "Who owns the intellectual property created during this engagement?",
        "document_id": "your-doc-id-here",
    },
    {
        "question": "What is the liability cap?",
        "document_id": "your-doc-id-here",
    },
]


async def collect_rag_outputs():
    """Query the API and collect inputs/outputs for RAGAS evaluation."""
    results = []

    async with httpx.AsyncClient(timeout=60.0) as client:
        for case in TEST_CASES:
            response = await client.post(
                f"{API_BASE}/documents/{case['document_id']}/query",
                json={"query": case["question"], "top_k": 6},
            )
            data = response.json()

            results.append({
                "question": case["question"],
                "answer": data["answer"],
                "contexts": [s["text"] for s in data["sources"]],
                "confidence": data["confidence"],
                "is_confident": data["is_confident"],
            })
            print(f"✓ Collected: {case['question'][:60]}...")

    return results


def run_ragas_evaluation(results: list[dict]):
    """Run RAGAS metrics on collected results."""
    dataset = Dataset.from_dict({
        "question": [r["question"] for r in results],
        "answer": [r["answer"] for r in results],
        "contexts": [r["contexts"] for r in results],
    })

    scores = evaluate(
        dataset=dataset,
        metrics=[faithfulness, answer_relevancy, context_precision],
    )

    return scores


def print_report(scores, results):
    print("\n" + "="*60)
    print("LEGALDOC AI — RAGAS EVALUATION REPORT")
    print("="*60)
    print(f"\n{'Metric':<25} {'Score':<10} {'Interpretation'}")
    print("-"*60)

    interpretations = {
        "faithfulness": ("Is the answer grounded in the document?", 0.8),
        "answer_relevancy": ("Does the answer address the question?", 0.75),
        "context_precision": ("Are retrieved chunks actually relevant?", 0.7),
    }

    for metric, (description, threshold) in interpretations.items():
        score = scores.get(metric, 0)
        status = "✅ Good" if score >= threshold else "⚠️ Needs work"
        print(f"{metric:<25} {score:<10.3f} {status}")

    print("\n" + "-"*60)
    avg_confidence = sum(r["confidence"] for r in results) / len(results)
    low_confidence_count = sum(1 for r in results if not r["is_confident"])
    print(f"Average retrieval confidence: {avg_confidence:.3f}")
    print(f"Low confidence responses: {low_confidence_count}/{len(results)}")
    print("="*60)

    # Recommendations
    print("\n📊 Recommendations:")
    if scores.get("faithfulness", 1) < 0.8:
        print("  → Faithfulness low: Reduce temperature, tighten system prompt")
    if scores.get("context_precision", 1) < 0.7:
        print("  → Context precision low: Adjust chunk size or improve clause parsing")
    if scores.get("answer_relevancy", 1) < 0.75:
        print("  → Answer relevancy low: Improve retrieval top_k or query rewriting")


async def main():
    print("Collecting RAG outputs from API...")
    results = await collect_rag_outputs()

    print("\nRunning RAGAS evaluation...")
    scores = run_ragas_evaluation(results)

    print_report(scores, results)


if __name__ == "__main__":
    asyncio.run(main())
