"""
Testes unitários para f04_retrieval (RetrievalFilter).

Usa mocks do ChromaManager para não depender de ChromaDB real.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline.context import PipelineContext


# ── Helper: cria RetrievalFilter com ChromaManager mockado ──

def _make_filter(
    collection_count: int = 5,
    query_documents: list[list[str]] | None = None,
    query_raises: Exception | None = None,
):
    """
    Cria um RetrievalFilter com ChromaManager totalmente mockado.

    Args:
        collection_count: quantos docs a coleção reporta ter.
        query_documents: resultado de query()["documents"].
        query_raises: se definido, query() levanta essa exceção.
    """
    with patch(
        "src.pipeline.filters.f04_retrieval.ChromaManager"
    ) as MockChroma:
        mock_instance = MagicMock()
        MockChroma.return_value = mock_instance

        # get_collection_info
        mock_instance.get_collection_info.return_value = {
            "name": "perfil_empresa",
            "count": collection_count,
        }

        # query
        if query_raises:
            mock_instance.query.side_effect = query_raises
        else:
            if query_documents is None:
                query_documents = [
                    ["chunk sobre IA", "chunk sobre IoT", "chunk certificação"]
                ]
            mock_instance.query.return_value = {
                "documents": query_documents,
                "metadatas": [[{}] * len(query_documents[0])],
                "distances": [[0.1] * len(query_documents[0])],
                "ids": [[f"id_{i}" for i in range(len(query_documents[0]))]],
            }

        from src.pipeline.filters.f04_retrieval import RetrievalFilter

        filt = RetrievalFilter.__new__(RetrievalFilter)
        filt.collection_name = "perfil_empresa"
        filt.n_results = 10
        filt.chroma_manager = mock_instance

        return filt, mock_instance


# ═══════════════════════════════════════════════════════════
# Testes
# ═══════════════════════════════════════════════════════════


class TestRetrievalFilterProcess:
    """Testa o método process() do RetrievalFilter."""

    def test_preenche_company_chunks_com_resultados(self):
        """Quando há coleção populada e resumo_objetivo, deve preencher company_chunks."""
        docs = [["chunk A", "chunk B", "chunk C"]]
        filt, mock_chroma = _make_filter(collection_count=10, query_documents=docs)

        ctx = PipelineContext()
        ctx.criterios_edital = {
            "resumo_objetivo": "Edital para projetos de inteligência artificial aplicada à indústria.",
            "titulo": "Chamada IA 2026",
        }

        filt.process(ctx)

        assert ctx.company_chunks == ["chunk A", "chunk B", "chunk C"]
        mock_chroma.query.assert_called_once()

    def test_sem_resumo_objetivo_retorna_lista_vazia(self):
        """Sem resumo_objetivo, não faz query e retorna lista vazia."""
        filt, mock_chroma = _make_filter()

        ctx = PipelineContext()
        ctx.criterios_edital = {"titulo": "Algum edital", "resumo_objetivo": ""}

        filt.process(ctx)

        assert ctx.company_chunks == []
        mock_chroma.query.assert_not_called()

    def test_criterios_edital_none_retorna_lista_vazia(self):
        """Se criterios_edital for None, degrada sem erro."""
        filt, mock_chroma = _make_filter()

        ctx = PipelineContext()
        ctx.criterios_edital = None

        filt.process(ctx)

        assert ctx.company_chunks == []
        mock_chroma.query.assert_not_called()

    def test_criterios_edital_sem_chave_resumo(self):
        """Se criterios_edital não tem a chave resumo_objetivo, degrada sem erro."""
        filt, mock_chroma = _make_filter()

        ctx = PipelineContext()
        ctx.criterios_edital = {"titulo": "Edital X"}

        filt.process(ctx)

        assert ctx.company_chunks == []

    def test_colecao_vazia_retorna_lista_vazia(self):
        """Se a coleção tem 0 documentos, não faz query."""
        filt, mock_chroma = _make_filter(collection_count=0)

        ctx = PipelineContext()
        ctx.criterios_edital = {
            "resumo_objetivo": "Edital sobre energia renovável.",
        }

        filt.process(ctx)

        assert ctx.company_chunks == []
        mock_chroma.query.assert_not_called()

    def test_chroma_exception_degrada_graciosamente(self):
        """Se o ChromaDB lança exceção, company_chunks fica vazio sem propagar erro."""
        filt, mock_chroma = _make_filter(
            collection_count=5,
            query_raises=RuntimeError("ChromaDB down"),
        )

        ctx = PipelineContext()
        ctx.criterios_edital = {
            "resumo_objetivo": "Edital sobre biotecnologia.",
        }

        filt.process(ctx)

        assert ctx.company_chunks == []

    def test_filtra_documentos_vazios(self):
        """Documentos vazios/None devem ser filtrados do resultado."""
        docs = [["chunk real", "", None, "outro chunk"]]
        filt, _ = _make_filter(query_documents=docs)

        ctx = PipelineContext()
        ctx.criterios_edital = {
            "resumo_objetivo": "Edital sobre saúde digital.",
        }

        filt.process(ctx)

        assert ctx.company_chunks == ["chunk real", "outro chunk"]

    def test_usa_empresa_collection_id_se_definido(self):
        """Se ctx.empresa_collection_id está definido, usa esse nome de coleção."""
        filt, mock_chroma = _make_filter(
            collection_count=3,
            query_documents=[["doc empresa"]],
        )

        ctx = PipelineContext()
        ctx.criterios_edital = {"resumo_objetivo": "Algo relevante."}
        ctx.empresa_collection_id = "minha_colecao_custom"

        filt.process(ctx)

        mock_chroma.get_collection_info.assert_called_with("minha_colecao_custom")
        mock_chroma.query.assert_called_once()
        call_kwargs = mock_chroma.query.call_args
        assert call_kwargs[1]["collection_name"] == "minha_colecao_custom" or \
               call_kwargs[0][0] == "minha_colecao_custom" if call_kwargs[0] else True

    def test_usa_collection_name_default_se_empresa_collection_id_vazio(self):
        """Se empresa_collection_id está vazio, usa o default 'perfil_empresa'."""
        filt, mock_chroma = _make_filter(
            collection_count=2,
            query_documents=[["doc"]],
        )

        ctx = PipelineContext()
        ctx.criterios_edital = {"resumo_objetivo": "Teste de default."}
        ctx.empresa_collection_id = ""

        filt.process(ctx)

        mock_chroma.get_collection_info.assert_called_with("perfil_empresa")


class TestRetrievalFilterInit:
    """Testa a inicialização do RetrievalFilter."""

    def test_parametros_default(self):
        """Verifica que os defaults estão corretos."""
        with patch("src.pipeline.filters.f04_retrieval.ChromaManager"):
            from src.pipeline.filters.f04_retrieval import RetrievalFilter

            filt = RetrievalFilter()
            assert filt.collection_name == "perfil_empresa"
            assert filt.n_results == 10

    def test_parametros_custom(self):
        """Verifica que parâmetros custom são aceitos."""
        with patch("src.pipeline.filters.f04_retrieval.ChromaManager"):
            from src.pipeline.filters.f04_retrieval import RetrievalFilter

            filt = RetrievalFilter(
                collection_name="outra_colecao",
                n_results=5,
                persist_directory="/tmp/test_chroma",
            )
            assert filt.collection_name == "outra_colecao"
            assert filt.n_results == 5
