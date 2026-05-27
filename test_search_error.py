import asyncio

from src.services.rag_service import RAGService


async def test():
    rag = RAGService()
    try:
        results = rag.search("invoice", limit=5)
        print("Success:", results)
    except Exception:
        import traceback

        traceback.print_exc()


asyncio.run(test())
