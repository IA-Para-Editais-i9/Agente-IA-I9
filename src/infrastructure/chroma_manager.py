import chromadb
from chromadb.config import Settings
from typing import List, Dict, Any, Optional
import os

class ChromaManager:
    # gerencia as coleções do ChromaDB para o projeto.
    # - editais: documentos dos editais (processados pelo pipeline principal)
    # - perfil_empresa: documentos internos da i9+ (portfólio, contratos, certificações)

    def __init__(self, persist_directory: str = "./chroma_db"):
        self.persist_directory = persist_directory

        os.makedirs(persist_directory, exist_ok=True)
        
        self.client = chromadb.PersistentClient(
            path=persist_directory,
            settings=Settings(anonymized_telemetry=False)
        )
        
        self._collections = {}
    
    def get_or_create_collection(self, name: str) -> chromadb.Collection:
        
        # obtém ou cria uma coleção pelo nome.
        Coleções esperadas: 'editais' e 'perfil_empresa'

        if name not in self._collections:
            self._collections[name] = self.client.get_or_create_collection(name=name)
        return self._collections[name]
    
    def index_documents(
        self,
        collection_name: str,
        ids: List[str],
        documents: List[str],
        metadatas: Optional[List[Dict[str, Any]]] = None
    ) -> None:
        # indexa documentos em uma coleção.
        
        """Args:
            collection_name: 'editais' ou 'perfil_empresa'
            ids: Lista de IDs únicos para cada chunk
            documents: Lista de textos (chunks) para indexar
            metadatas: Lista de metadados para cada chunk (tipo, data, fonte)
        """
        collection = self.get_or_create_collection(collection_name)
        
        collection.add(
            ids=ids,
            documents=documents,
            metadatas=metadatas
        )
    
    def get_collection_info(self, collection_name: str) -> dict:
        collection = self.get_or_create_collection(collection_name)
        return {
            "name": collection.name,
            "count": collection.count(),
        }
