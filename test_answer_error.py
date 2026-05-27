import asyncio

from src.services.rag_service import RAGService


async def test():
    rag = RAGService()
    try:
        results = rag.answer("Kto jest sprzedawcą na fakturze 40378170?", limit=3)
        print("Success:", results)
    except Exception:
        import traceback

        traceback.print_exc()


asyncio.run(test())
