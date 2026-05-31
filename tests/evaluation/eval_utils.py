from typing import cast

from datasets import Dataset, DatasetDict, load_dataset


def get_evaluation_dataset(num_samples: int = 5, seed: int = 42) -> Dataset | DatasetDict:
    """
    Loads the standard evaluation dataset and returns a randomized subset of samples.
    """
    print(f"Loading {num_samples} samples from 'katanaml-org/invoices-donut-data-v1'...")
    dataset = load_dataset("katanaml-org/invoices-donut-data-v1", split="train")
    samples = cast(Dataset, dataset.shuffle(seed=seed)).select(range(num_samples))
    return samples


def normalize_amount(val: str) -> float:
    """
    Normalizes a string representation of currency to a float value.
    Example: "$1,234.50" -> 1234.5
    """
    if not val:
        return 0.0
    val = val.replace("$", "").replace(" ", "").replace(",", ".")
    try:
        return float(val)
    except ValueError:
        return 0.0
