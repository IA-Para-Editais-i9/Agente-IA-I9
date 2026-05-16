import os
from typing import Any, Dict, List, Optional

import chromadb
from chromadb.config import Settings


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

    def query(
        self,
        collection_name: str,
        query_text: str,
        n_results: int = 10,
        where: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """
        Consulta uma coleção e retorna o resultado bruto do Chroma.

        Args:
            collection_name: nome da coleção (ex: 'editais', 'perfil_empresa')
            query_text: texto de consulta
            n_results: quantidade de resultados
            where: filtro de metadados (opcional)
        """
        collection = self.get_or_create_collection(collection_name)
        return collection.query(
            query_texts=[query_text],
            n_results=n_results,
            where=where,
            include=["documents", "metadatas", "distances", "ids"],
        )
