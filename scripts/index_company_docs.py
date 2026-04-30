#!/usr/bin/env python3
#indexação dos documentos internos da i9+.
# Executar UMA ÚNICA VEZ na inicialização do projeto.
import os
import sys
import argparse
import uuid
from pathlib import Path
from typing import List, Dict, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from src.pipeline.filters.f01_ingestion import IngestionFilter
from src.infrastructure.chroma_manager import ChromaManager
from src.utils.chunking import chunk_text


class CompanyDocsIndexer:    
    # indexa todos os documentos da i9 no ChromaDB
    
    def __init__(self, force: bool = False):
        self.force = force
        self.chroma_manager = ChromaManager()
        self.ingestion_filter = IngestionFilter()
        self.flag_file = Path(".company_docs_indexed")
        
    def already_indexed(self) -> bool:
        
        if self.force:
            print(">> Forçando recriação da indexação...")
            return False
        return self.flag_file.exists()
    
    def mark_as_indexed(self) -> None:
        self.flag_file.touch()
        print(f">> Marcação criada: {self.flag_file}")
    
    def get_pdf_files(self, base_path: str) -> List[tuple]:
        pdf_files = []
        base_dir = Path(base_path)
        
        # Mapeamento de pastas para tipos
        tipo_mapping = {
            "portfolio": "portfolio",
            "contratos": "contrato",
            "certificacoes": "certificacao"
        }
        
        for folder_name, doc_type in tipo_mapping.items():
            folder_path = base_dir / folder_name
            if not folder_path.exists():
                print(f">> Aviso: Pasta não encontrada: {folder_path}")
                continue
            
            for pdf_path in folder_path.glob("*.pdf"):
                pdf_files.append((str(pdf_path), doc_type))
        
        return pdf_files
    
    def get_metadata(self, pdf_path: str, doc_type: str, chunk_index: int) -> Dict[str, Any]:
        pdf_path_obj = Path(pdf_path)
        
        mod_time = pdf_path_obj.stat().st_mtime
        from datetime import datetime
        data_mod = datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d")
        
        return {
            "tipo": doc_type,
            "fonte": pdf_path,
            "data": data_mod,
            "chunk_index": chunk_index,
            "nome_arquivo": pdf_path_obj.name
        }
    
    def index_company_documents(self) -> None:
        base_path = "data/empresa"
        
        if not os.path.exists(base_path):
            print(f"Erro: Pasta '{base_path}' não encontrada!")
            print(f"   Certifique-se de que os documentos da i9+ estão em {base_path}")
            return
        
    
        if self.already_indexed():
            print("Documentos da empresa já estão indexados.")
            print(f"   Para reindexar, execute com --force")
            return
        
        print("Iniciando indexação dos documentos da i9+...")
        
        # Obter todos os PDFs
        pdf_files = self.get_pdf_files(base_path)
        
        if not pdf_files:
            print(f"Nenhum PDF encontrado em {base_path}")
            return
        
        print(f"Encontrados {len(pdf_files)} PDFs para indexar:")
        for pdf_path, doc_type in pdf_files:
            print(f"   - {doc_type}: {Path(pdf_path).name}")
        
        print("\n" + "-" * 50)
        
        all_chunks = []
        all_ids = []
        all_metadatas = []
        
        for pdf_path, doc_type in pdf_files:
            print(f"\nProcessando: {Path(pdf_path).name} ({doc_type})")
            
            try:
                # Usar o IngestionFilter para converter PDF para Markdown
                # Criamos um contexto temporário
                from src.pipeline.context import PipelineContext
                temp_ctx = PipelineContext(pdf_path=pdf_path)
                
                self.ingestion_filter.process(temp_ctx)
                markdown_text = temp_ctx.markdown_text
                
                if not markdown_text:
                    print(f"Aviso: Nenhum texto extraído de {pdf_path}")
                    continue
                
                # Chunkificar
                chunks = chunk_text(markdown_text)
                print(f"Gerados {len(chunks)} chunks")
                
                # Gerar IDs e metadados
                for i, chunk in enumerate(chunks):
                    chunk_id = str(uuid.uuid4())
                    metadata = self.get_metadata(pdf_path, doc_type, i)
                    
                    all_chunks.append(chunk)
                    all_ids.append(chunk_id)
                    all_metadatas.append(metadata)
                    
            except Exception as e:
                print(f"Erro ao processar {pdf_path}: {e}")
                continue
        
        if not all_chunks:
            print("\nNenhum chunk gerado. Indexação abortada.")
            return
        
        print("\n" + "-" * 50)
        print(f"Total de chunks: {len(all_chunks)}")
        
        # Indexar no ChromaDB (coleção 'perfil_empresa')
        print(f"\nIndexando no ChromaDB (coleção: 'perfil_empresa')...")
        
        self.chroma_manager.index_documents(
            collection_name="perfil_empresa",
            ids=all_ids,
            documents=all_chunks,
            metadatas=all_metadatas
        )
        
        # Salvar o ID da coleção (opcional: poderia ser salvo em algum lugar)
        info = self.chroma_manager.get_collection_info("perfil_empresa")
        print(f"✅ Coleção 'perfil_empresa' criada/atualizada com sucesso!")
        print(f"   ID da coleção: {info['name']}")
        print(f"   Total de documentos na coleção: {info['count']}")
        
        self.mark_as_indexed()
        
        print("\n" + "=" * 50)
        print("Indexação dos documentos da i9+ concluída com sucesso!")
        print("=" * 50)


def main():
    parser = argparse.ArgumentParser(
        description="Indexa os documentos internos da i9+ no ChromaDB"
    )
    parser.add_argument(
        "--force",
        action="store_true",
        help="Força a reindexação mesmo se já foi executada"
    )
    
    args = parser.parse_args()
    
    indexer = CompanyDocsIndexer(force=args.force)
    indexer.index_company_documents()


if __name__ == "__main__":
    main()
