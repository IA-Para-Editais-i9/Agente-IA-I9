import logging

import chromadb

from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext

logger = logging.getLogger(__name__)

N_RESULTS = 10  # trechos retornados para o Agente 2
DISTANCIA_MAX = 1.2  # cos distance: 0=igual, 2=oposto (limiar empírico)


class RetrievalFilter(Filter):
    """
    f04 — Busca RAG.
    Dado o objetivo do edital (ctx.criterios_edital["resumo_objetivo"]),
    retorna os N trechos mais relevantes do perfil da empresa no ChromaDB.
    Popula: ctx.company_chunks (list[str])
    """

    def __init__(
        self,
        chroma_path: str = "./chroma_db",
        collection_name: str = "perfil_empresa",
    ):
        self._chroma_path = chroma_path
        self._collection_name = collection_name

    def run(self, ctx: PipelineContext) -> PipelineContext:
        if not ctx.criterios_edital:
            raise ValueError(
                "f04: ctx.criterios_edital está vazio. f03 rodou corretamente?"
            )

        query_text = (ctx.criterios_edital or {}).get("resumo_objetivo", "") or ""
        if not query_text:
            palavras = (
                (ctx.criterios_edital or {}).get("palavras_chave_tematicas", []) or []
            )
            if isinstance(palavras, list):
                query_text = " ".join(str(p) for p in palavras if p)

        if not query_text.strip():
            logger.warning(
                "f04: nenhum texto de query disponível. Retornando chunks vazios."
            )
            ctx.company_chunks = []
            return ctx

        try:
            client = chromadb.PersistentClient(path=self._chroma_path)
            collection = client.get_collection(self._collection_name)
        except Exception as e:  # pragma: no cover (depende do ambiente)
            raise RuntimeError(
                f"f04: erro ao conectar ao ChromaDB em '{self._chroma_path}' "
                f"ou ao abrir a coleção '{self._collection_name}': {e}"
            ) from e

        try:
            results = collection.query(
                query_texts=[query_text],
                n_results=N_RESULTS,
                include=["documents", "metadatas", "distances"],
            )
        except Exception as e:  # pragma: no cover (depende do ambiente)
            raise RuntimeError(f"f04: erro na query ao ChromaDB: {e}") from e

        documents: list[str] = results.get("documents", [[]])[0] if results else []
        distances: list[float] = results.get("distances", [[]])[0] if results else []

        if not documents:
            logger.warning(
                "f04: ChromaDB não retornou nenhum documento. "
                "Coleção '%s' está populada?",
                self._collection_name,
            )
            ctx.company_chunks = []
            return ctx

        if distances and len(distances) == len(documents):
            chunks_filtrados = [
                doc
                for doc, dist in zip(documents, distances, strict=False)
                if dist < DISTANCIA_MAX
            ]
        else:
            chunks_filtrados = documents

        if not chunks_filtrados:
            logger.warning(
                "f04: todos os %d chunks ficaram acima do limiar de distância %.1f. "
                "Usando os 3 mais próximos sem filtro.",
                len(documents),
                DISTANCIA_MAX,
            )
            chunks_filtrados = documents[:3]

        ctx.company_chunks = chunks_filtrados
        logger.info(
            "f04: %d chunks retornados para o Agente 2.", len(ctx.company_chunks)
        )
        return ctx
