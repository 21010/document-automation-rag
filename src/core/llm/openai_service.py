import base64
import json
import logging

import httpx

from src.core.config import settings
from src.core.constants import DocumentType
from src.core.llm.base import LLMService
from src.core.llm.prompts import ROUTER_PROMPT, get_prompt_for_type
from src.models.invoice import StructuredInvoice

logger = logging.getLogger(__name__)


class OpenAIService(LLMService):
    def __init__(self):
        self.base_url = settings.OPENAI_BASE_URL.rstrip("/")
        self.api_key = settings.OPENAI_API_KEY
        self.gen_model = settings.OPENAI_GENERATIVE_MODEL
        self.embed_model = settings.OPENAI_EMBEDDING_MODEL
        logger.info(
            f"Initialized OpenAIService. URL: {self.base_url}, Model: {self.gen_model}"
        )

    def _get_headers(self) -> dict:
        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def _call_generate(self, prompt: str, base64_image: str | None = None) -> str:
        """Call OpenAI-compatible /chat/completions endpoint."""
        url = f"{self.base_url}/chat/completions"

        messages = []
        if base64_image:
            # Vision schema
            messages.append(
                {
                    "role": "user",
                    "content": [
                        {"type": "text", "text": prompt},
                        {
                            "type": "image_url",
                            "image_url": {"url": f"data:image/jpeg;base64,{base64_image}"},
                        },
                    ],
                }
            )
        else:
            # Standard text schema
            messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.gen_model,
            "messages": messages,
            "temperature": 0.0,
        }

        try:
            with httpx.Client(timeout=600.0) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()
                return response.json()["choices"][0]["message"]["content"]
        except Exception as e:
            logger.error(f"Error calling OpenAI API: {e}")
            return ""

    def get_structured_data(self, text: str, doc_type: DocumentType = DocumentType.UNKNOWN) -> StructuredInvoice:
        base_prompt = get_prompt_for_type(doc_type)
        prompt = f"{base_prompt}\n\nDocument text:\n{text}\n\nOutput only JSON."

        content = self._call_generate(prompt)

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return StructuredInvoice(**data)
        except Exception as e:
            logger.error(
                f"Error parsing JSON from OpenAI structuring: {e}. Raw content: {content}"
            )
            return StructuredInvoice()

    def get_embeddings(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        url = f"{self.base_url}/embeddings"
        payload = {"model": self.embed_model, "input": texts}

        try:
            with httpx.Client(timeout=60.0) as client:
                response = client.post(url, headers=self._get_headers(), json=payload)
                response.raise_for_status()

                # OpenAI format returns a list of data objects
                data = response.json().get("data", [])
                # Ensure they are sorted by index to preserve order
                data.sort(key=lambda x: x["index"])
                return [item["embedding"] for item in data]
        except Exception as e:
            logger.error(f"Error calling OpenAI embed API: {e}")
            raise

    def extract_from_vision(
        self, image_path: str, doc_type: DocumentType = DocumentType.UNKNOWN
    ) -> tuple[str, StructuredInvoice]:
        try:
            with open(image_path, "rb") as f:
                image_data = f.read()

            b64_image = base64.b64encode(image_data).decode("utf-8")

            base_prompt = get_prompt_for_type(doc_type)
            prompt = f"""
            {base_prompt}
            
            Extract the full raw text first, then the JSON.
            Return your response in this exact format:
            RAW_TEXT:
            [Full extracted text here]
            
            STRUCTURED_JSON:
            [The JSON object here]
            """

            content = self._call_generate(prompt, base64_image=b64_image)

            raw_text = ""
            structured_data = StructuredInvoice()

            if "RAW_TEXT:" in content and "STRUCTURED_JSON:" in content:
                parts = content.split("STRUCTURED_JSON:")
                raw_text = parts[0].replace("RAW_TEXT:", "").strip()
                json_part = parts[1].strip()

                if "```json" in json_part:
                    json_part = json_part.split("```json")[1].split("```")[0].strip()
                elif "```" in json_part:
                    json_part = json_part.split("```")[1].split("```")[0].strip()

                data = json.loads(json_part)
                structured_data = StructuredInvoice(**data)

            return raw_text, structured_data

        except Exception as e:
            logger.error(f"Error during OpenAI Vision extraction: {e}")
            return str(e), StructuredInvoice()

    def route_query(self, query: str) -> dict:
        prompt = f"{ROUTER_PROMPT.format(query=query)}\n\nOutput only JSON."
        content = self._call_generate(prompt)

        try:
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            logger.error(f"Routing error: {e}. Raw content: {content}")
            return {"route": "vector"}

    def generate_answer(self, query: str, context: str) -> str:
        prompt = f"""
        You are a helpful assistant specialized in processing invoices and documents.
        Answer the following query based ONLY on the provided context.
        If the answer is not in the context, say you don't know.
        
        Query: {query}
        
        Context:
        {context}
        """

        return self._call_generate(prompt)
