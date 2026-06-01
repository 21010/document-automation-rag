import asyncio
import os
import sys
import time
import uuid
from typing import Any, cast

# Ensure src module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.api.dependencies import get_doc_service, get_rag_service
from src.core.constants import DocumentStatus
from src.core.llm.openai_service import OpenAIService
from tests.evaluation.eval_utils import get_evaluation_dataset

# Define a set of standard queries to evaluate
TEST_QUERIES = [
    "Czy na dokumencie występuje podatek?",
    "Który dokument ma najwyższą kwotę?",
    "Kto jest sprzedawcą?",
    "Kto jest nabywcą?",
    "Jaki jest numer faktury?",
    "Jaka jest kwota netto?",
    "Jaka jest kwota brutto?",
    "Jaka jest stawka VAT?",
    "Jaka data występuje w dokumencie?",
]


async def load_dataset_samples(num_samples: int = 5) -> list[str]:
    samples = get_evaluation_dataset(num_samples=num_samples)

    doc_service = get_doc_service()
    rag_service = get_rag_service()

    doc_ids = []
    print(f"Injecting ground truth into Vector Database for {num_samples} documents...")

    for i, item in enumerate(samples):
        row = cast(dict[str, Any], item)
        ground_truth_str = row["ground_truth"]

        # 1. Create a placeholder document
        filename = f"eval_dataset_sample_{i}.json"
        doc_id = str(uuid.uuid4())
        await doc_service.create_pending_document(doc_id, filename)

        # 2. Update to completed with the raw text payload (using the stringified JSON ground truth)
        await doc_service.update_document(
            doc_id,
            {
                "status": DocumentStatus.COMPLETED,
                "text": ground_truth_str,
            },
        )

        # 3. Index it into the Vector Database
        await rag_service.index_document(doc_id, ground_truth_str)
        doc_ids.append(doc_id)

    print(f"Successfully injected and indexed {len(doc_ids)} documents.\n")
    return doc_ids


async def evaluate_retrieval():
    doc_ids = []
    doc_service = get_doc_service()
    try:
        # Load the test dataset into the DB
        doc_ids = await load_dataset_samples(5)

        print("Initializing RAG Engine and LLM Judge...")
        rag_service = get_rag_service()

        # Configure the judge LLM using specific environment variables if provided,
        # otherwise it falls back to the default OpenAI settings in the config.
        judge_llm = OpenAIService(
            base_url=os.getenv("JUDGE_LLM_BASE_URL"),
            api_key=os.getenv("JUDGE_LLM_API_KEY"),
            gen_model=os.getenv("JUDGE_LLM_MODEL"),
        )

        print(f"Using Judge LLM Model: {judge_llm.gen_model}")

        total = len(TEST_QUERIES)
        print(f"\nStarting evaluation of {total} queries...\n")

        passed = 0
        failed = 0
        start_time = time.time()

        for i, query in enumerate(TEST_QUERIES):
            print(f"--- Query {i + 1}: {query} ---")

            try:
                # 1. Ask the RAG system
                answer_payload = await rag_service.answer(query)

                # The answer payload looks like {"answer": "...", "sources": [...], "route": "...", "reasoning": "..."}
                system_answer = answer_payload.get("answer", "")
                route = answer_payload.get("route", "")
                sources = answer_payload.get("sources", [])

                # 2. Reconstruct context from sources
                print(f"Route taken: {route}")
                print(f"Sources used: {len(sources)}")
                print(f"System Answer: {system_answer}\n")

                # 3. LLM-as-a-judge Grading
                judge_prompt = f"""
                You are an impartial evaluator.
                Assess if the following 'System Answer' provides a direct and meaningful response to the 'Query'.
                If the System Answer says it doesn't know or cannot find the information, score it as 0.
                If it provides a definitive answer, score it as 1.
                
                Query: {query}
                System Answer: {system_answer}
                
                Output your grade exactly as:
                GRADE: 1
                or
                GRADE: 0
                
                Followed by a brief 1-sentence reasoning.
                """

                content, _ = await judge_llm._call_generate(judge_prompt)
                content = content.strip()
                print(f"LLM Judge Evaluation:\n{content}\n")
                
                if "GRADE: 1" in content:
                    passed += 1
                else:
                    failed += 1

            except Exception as e:
                print(f"Error evaluating query '{query}': {e}\n")
                failed += 1
                
        duration = time.time() - start_time
        success_rate = (passed / total) * 100 if total > 0 else 0
        
        print("==========================================")
        print("EVALUATION SUMMARY")
        print("==========================================")
        print(f"Total Queries Evaluated : {total}")
        print(f"Passed (Grade 1)        : {passed}")
        print(f"Failed (Grade 0/Error)  : {failed}")
        print(f"Success Rate            : {success_rate:.1f}%")
        print(f"Total Duration          : {duration:.2f}s")
        print(f"Average Duration/Query  : {(duration/total):.2f}s" if total > 0 else "")
        print("==========================================")
        
    finally:
        # Clean up all the injected documents
        if doc_ids:
            print(f"\nCleaning up {len(doc_ids)} injected documents from the database...")
            for doc_id in doc_ids:
                try:
                    await doc_service.delete_document(doc_id)
                except Exception as e:
                    print(f"Failed to clean up doc_id {doc_id}: {e}")
            print("Cleanup complete.")


if __name__ == "__main__":
    asyncio.run(evaluate_retrieval())
