import os

import pytest

from src.core.config import settings
from src.core.llm.openai_service import OpenAIService


@pytest.mark.asyncio
async def test_vlm_extraction():
    svc = OpenAIService(base_url=settings.OPENAI_BASE_URL, gen_model=settings.OPENAI_VLM_MODEL)

    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    upload_dir = os.path.join(project_root, "data", "uploads")

    if not os.path.exists(upload_dir):
        pytest.skip(f"Upload directory {upload_dir} does not exist")

    images = [f for f in os.listdir(upload_dir) if f.endswith(".jpg")]
    if not images:
        pytest.skip("No images found in data/uploads")

    img_path = os.path.join(upload_dir, images[0])

    text, data, usage = await svc.extract_from_vision(img_path)

    print("RAW_TEXT:")
    print(text)
    print("JSON_DATA:")
    print(data.model_dump())

    assert text is not None
    assert data is not None
