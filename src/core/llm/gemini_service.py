import json
import logging
import mimetypes

from google import genai

# pyrefly: ignore [missing-import]
from src.core.config import settings

# pyrefly: ignore [missing-import]
from src.core.constants import DocumentType
from src.core.llm.base import LLMService

# pyrefly: ignore [missing-import]
from src.core.llm.prompts import ROUTER_PROMPT, get_prompt_for_type

# pyrefly: ignore [missing-import]
from src.models.invoice import StructuredDocument, StructuredInvoice, get_model_for_type

logger = logging.getLogger(__name__)


class GeminiService(LLMService):
    def __init__(self):
        if not settings.GEMINI_API_KEY:
            logger.warning("GEMINI_API_KEY not set. Gemini features will be disabled or fail.")
            self.client = None
        else:
            self.client = genai.Client(api_key=settings.GEMINI_API_KEY)
            self.generative_model = settings.GEMINI_GENERATIVE_MODEL
            self.embedding_model = settings.GEMINI_EMBEDDING_MODEL

    def get_structured_data(self, text: str, doc_type: DocumentType = DocumentType.UNKNOWN) -> StructuredDocument:
        TargetModel = get_model_for_type(doc_type)
        if not self.client:
            return TargetModel()

        schema_json = json.dumps(TargetModel.model_json_schema(), indent=2)
        base_prompt = get_prompt_for_type(doc_type, schema_json)
        prompt = f"{base_prompt}\n\nDocument text:\n{text}"

        try:
            response = self.client.models.generate_content(model=self.generative_model, contents=prompt)
            # Simple JSON extraction
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            data = json.loads(content)
            return TargetModel(**data)
        except Exception as e:
            logger.error(f"Error calling Gemini for structuring: {e}")
            return TargetModel()

    def get_embeddings(self, texts: list[str], task_type: str = "RETRIEVAL_DOCUMENT") -> list[list[float]]:
        """Get embeddings for a list of texts.

        Args:
            texts: Text strings to embed.
            task_type: Gemini task type. Use "RETRIEVAL_DOCUMENT" when indexing,
                       "RETRIEVAL_QUERY" when embedding a search query.
        """
        if not self.client:
            raise ValueError("GEMINI_API_KEY is required for embeddings")

        try:
            embeddings = []
            for text in texts:
                result = self.client.models.embed_content(
                    model=self.embedding_model, contents=text, config={"task_type": task_type}
                )
                embeddings.extend([item.values for item in result.embeddings])
            return embeddings
        except Exception as e:
            logger.error(f"Error calling Gemini for embeddings: {e}")
            raise

    def extract_from_vision(
        self, image_path: str, doc_type: DocumentType = DocumentType.UNKNOWN
    ) -> tuple[str, StructuredDocument]:
        TargetModel = get_model_for_type(doc_type)
        if not self.client:
            return "", TargetModel()

        try:
            # Open image file
            with open(image_path, "rb") as f:
                image_data = f.read()

            schema_json = json.dumps(TargetModel.model_json_schema(), indent=2)
            base_prompt = get_prompt_for_type(doc_type, schema_json)
            prompt = f"""
            {base_prompt}
            
            Extract the full raw text first, then the JSON.
            Return your response in this exact format:
            RAW_TEXT:
            [Full extracted text here]
            
            STRUCTURED_JSON:
            [The JSON object here]
            """

            # Detect MIME type from file extension; fallback to image/jpeg
            mime_type, _ = mimetypes.guess_type(image_path)
            if mime_type not in ("image/jpeg", "image/png", "image/webp", "image/heic", "image/heif"):
                mime_type = "image/jpeg"

            response = self.client.models.generate_content(
                model=self.generative_model,
                contents=[prompt, {"inline_data": {"data": image_data, "mime_type": mime_type}}],
            )

            content = response.text

            # Parsing logic
            raw_text = ""
            structured_data = TargetModel()

            if "RAW_TEXT:" in content and "STRUCTURED_JSON:" in content:
                parts = content.split("STRUCTURED_JSON:")
                raw_text = parts[0].replace("RAW_TEXT:", "").strip()
                json_part = parts[1].strip()

                if "```json" in json_part:
                    json_part = json_part.split("```json")[1].split("```")[0].strip()
                elif "```" in json_part:
                    json_part = json_part.split("```")[1].split("```")[0].strip()

                data = json.loads(json_part)
                structured_data = TargetModel(**data)

            return raw_text, structured_data

        except Exception as e:
            logger.error(f"Error during Gemini Vision extraction: {e}")
            return str(e), TargetModel()

    def route_query(self, query: str) -> dict:
        if not self.client:
            return {"route": "vector"}

        try:
            response = self.client.models.generate_content(
                model=self.generative_model, contents=ROUTER_PROMPT.format(query=query)
            )
            content = response.text.strip()
            if "```json" in content:
                content = content.split("```json")[1].split("```")[0].strip()
            elif "```" in content:
                content = content.split("```")[1].split("```")[0].strip()

            return json.loads(content)
        except Exception as e:
            logger.error(f"Routing error: {e}")
            return {"route": "vector"}

    def generate_answer(self, query: str, context: str) -> str:
        if not self.client:
            return "Gemini API key is missing."

        prompt = f"""
        You are a helpful assistant specialized in processing invoices and documents.
        Answer the following query based ONLY on the provided context.
        If the answer is not in the context, say you don't know.
        
        Query: {query}
        
        Context:
        {context}
        """

        try:
            response = self.client.models.generate_content(model=self.generative_model, contents=prompt)
            return response.text.strip()
        except Exception as e:
            logger.error(f"Error calling Gemini for answering: {e}")
            return f"Error generating answer: {e}"
