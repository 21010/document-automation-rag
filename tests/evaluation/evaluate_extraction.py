import asyncio
import json
import os
import sys
from typing import Any, cast

# Ensure src module can be imported
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.processors.vlm import VLMProcessor
from tests.evaluation.eval_utils import get_evaluation_dataset, normalize_amount


async def evaluate_extraction():
    # We take 5 samples for evaluation to prevent long execution times
    samples = get_evaluation_dataset(num_samples=5)

    processor = VLMProcessor()

    total = len(samples)
    print(f"\nStarting evaluation of {total} invoice samples...")

    # Summary metrics
    total_vlm_duration = 0.0
    total_tokens = 0
    exact_matches_amount = 0
    successful_samples = 0

    for i, item in enumerate(samples):
        # Type hint for the IDE since HuggingFace dataset types are inferred incorrectly
        row = cast(dict[str, Any], item)

        # The dataset contains 'image' (PIL Image) and 'ground_truth' (JSON string)
        image = row["image"]
        ground_truth_str = row["ground_truth"]

        # Save image to a temporary file for the VLMProcessor
        temp_img_path = f"temp_eval_{i}.jpg"
        if image.mode != "RGB":
            image = image.convert("RGB")
        image.save(temp_img_path)

        try:
            ground_truth = json.loads(ground_truth_str)
            gt_data = ground_truth.get("gt_parse", {})

            print(f"\n--- Sample {i + 1} ---")

            # Run extraction
            result = await processor.process(temp_img_path)
            structured_data = result.structured_data.model_dump()

            print("Extracted Data (Our Pipeline):")
            print(json.dumps(structured_data, indent=2, ensure_ascii=False))

            print("\nGround Truth Data (Dataset):")
            print(json.dumps(gt_data, indent=2, ensure_ascii=False))

            duration = result.raw_data.get("vlm_duration", 0)
            tokens = result.raw_data.get("usage", {}).get("total_tokens", 0)

            print(f"VLM Duration: {duration:.2f}s")
            print(f"Tokens Used: {tokens}")

            total_vlm_duration += duration
            total_tokens += int(tokens)
            successful_samples += 1

            # Exact match logic for Total Amount
            extracted_total = structured_data.get("kwota_koncowa")
            if extracted_total is None:
                extracted_total = 0.0

            gt_total_str = gt_data.get("summary", {}).get("total_gross_worth", "")
            gt_total = normalize_amount(gt_total_str)

            if abs(extracted_total - gt_total) < 0.01:
                exact_matches_amount += 1
                print("-> Amount Match: SUCCESS")
            else:
                print(f"-> Amount Match: FAILED (Expected: {gt_total}, Got: {extracted_total})")

        except Exception as e:
            print(f"Error processing sample {i}: {e}")
        finally:
            if os.path.exists(temp_img_path):
                os.remove(temp_img_path)

    print("\n==========================================")
    print("EVALUATION SUMMARY")
    print("==========================================")
    print(f"Total Samples Processed : {total}")
    print(f"Successful Extractions  : {successful_samples}")
    print(f"Total VLM Duration      : {total_vlm_duration:.2f}s")
    if successful_samples > 0:
        print(f"Average Duration/Sample : {total_vlm_duration / successful_samples:.2f}s")
    print(f"Total Tokens Used       : {total_tokens}")
    print(
        f"Exact Match (Amount)    : {exact_matches_amount} / {successful_samples} ({exact_matches_amount / max(1, successful_samples) * 100:.1f}%)"  # noqa: E501
    )
    print("==========================================\n")


if __name__ == "__main__":
    asyncio.run(evaluate_extraction())
