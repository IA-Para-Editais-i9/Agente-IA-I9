import pytest

from src.pipeline.context import PipelineContext
from src.pipeline.filters.f04_retrieval import DISTANCIA_MAX, RetrievalFilter


def test_f04_exige_criterios_edital():
    ctx = PipelineContext(criterios_edital=None)
    with pytest.raises(ValueError, match="ctx\\.criterios_edital"):
        RetrievalFilter().run(ctx)


def test_f04_retorna_vazio_quando_nao_ha_query_text():
    ctx = PipelineContext(criterios_edital={"resumo_objetivo": "", "palavras_chave_tematicas": []})
    ctx = RetrievalFilter().run(ctx)
    assert ctx.company_chunks == []


def test_f04_consulta_chromadb_e_filtra_por_distancia(monkeypatch):
    class FakeCollection:
        def query(self, query_texts, n_results, include):
            assert query_texts == ["economia circular"]
            assert n_results == 10
            assert "documents" in include
            return {
                "documents": [["doc-1", "doc-2", "doc-3"]],
                "distances": [[DISTANCIA_MAX - 0.01, DISTANCIA_MAX + 0.5, DISTANCIA_MAX - 0.2]],
                "metadatas": [[{}, {}, {}]],
            }

    class FakeClient:
        def __init__(self, path):
            assert path == "./chroma_db"

        def get_collection(self, name):
            assert name == "perfil_empresa"
            return FakeCollection()

    import src.pipeline.filters.f04_retrieval as f04

    monkeypatch.setattr(f04.chromadb, "PersistentClient", FakeClient)

    ctx = PipelineContext(criterios_edital={"resumo_objetivo": "economia circular"})
    ctx = RetrievalFilter().run(ctx)
    assert ctx.company_chunks == ["doc-1", "doc-3"]
