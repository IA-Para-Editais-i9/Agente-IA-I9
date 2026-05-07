from __future__ import annotations

from src.infrastructure.chroma_manager import ChromaManager
from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext


class RetrievalFilter(Filter):
    """
    Squad C — C3/C5

    Usa os critérios do edital (especialmente `resumo_objetivo`) como query e
    busca trechos relevantes do perfil da empresa no ChromaDB.
    """

    def __init__(
        self,
        collection_name: str = "perfil_empresa",
        n_results: int = 10,
        persist_directory: str = "./chroma_db",
    ):
        self.collection_name = collection_name
        self.n_results = n_results
        self.chroma_manager = ChromaManager(persist_directory=persist_directory)

    def process(self, ctx: PipelineContext) -> None:
        criterios = ctx.criterios_edital or {}
        resumo_objetivo = ""

        if isinstance(criterios, dict):
            resumo_objetivo = str(criterios.get("resumo_objetivo") or "").strip()

        if not resumo_objetivo:
            # sem query -> sem retrieval, mas não quebra o pipeline
            ctx.company_chunks = []
            return

        collection = (ctx.empresa_collection_id or "").strip() or self.collection_name

        try:
            info = self.chroma_manager.get_collection_info(collection)
            if info.get("count", 0) <= 0:
                ctx.company_chunks = []
                return

            result = self.chroma_manager.query(
                collection_name=collection,
                query_text=resumo_objetivo,
                n_results=self.n_results,
            )
            documents = result.get("documents") or [[]]
            ctx.company_chunks = [d for d in documents[0] if d]
        except Exception:
            # falha de Chroma / embeddings / coleção inexistente
            ctx.company_chunks = []
            return
