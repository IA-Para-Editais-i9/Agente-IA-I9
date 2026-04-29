from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext
from src.infrastructure.chroma_manager import ChromaManager
from src.utils.chunking import chunk_text
import uuid

class IndexingFilter(Filter):
    def __init__(self):
        self.chroma_manager = ChromaManager()

    def process(self, ctx: PipelineContext) -> None:
        if not ctx.markdown_text:
            raise ValueError(">> Nenhum markdown_text encontrado no contexto. Certifique-se de que o IngestionFilter foi executado.")
    
        # deixa txt chunkificado
        chunks = chunk_text(ctx.markdown_text)
        
        if not chunks:
            raise ValueError(">> Nenhum chunk gerado a partir do markdown_text.")
        
        # id p cada chunk
        ids = [str(uuid.uuid4()) for _ in chunks]
        
        # indexa nos editais
        self.chroma_manager.index_documents(
            collection_name="editais",
            ids=ids,
            documents=chunks,
            metadatas=[{
                "tipo": "edital",
                "fonte": ctx.pdf_path,
                "chunk_index": i
            } for i in range(len(chunks))]
        )
        
        # armazena id
        collection_info = self.chroma_manager.get_collection_info("editais")
        ctx.edital_collection_id = collection_info["name"]
        
        print(f">> Indexados {len(chunks)} chunks na coleção 'editais'")
