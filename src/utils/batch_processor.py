import os
from datetime import datetime
from pathlib import Path
from typing import Callable, List, Optional


class BatchProcessor:
    def __init__(self, progress_callback: Optional[Callable] = None):
        self.progress_callback = progress_callback

    def scan_pdfs(self, directory: str) -> List[str]:
        # retorna lista de todos PDFs em um diretório
        pdfs = []
        path = Path(directory)

        if not path.exists():
            return []

        for file in path.rglob("*.pdf"):
            pdfs.append(str(file))

        return pdfs

    def process_batch(self, files: List[str], processor_func: Callable) -> List[dict]:
        # processa lista de arquivos
        results = []
        total = len(files)

        for idx, file_path in enumerate(files):
            if self.progress_callback:
                self.progress_callback(idx + 1, total, file_path)

            try:
                result = processor_func(file_path)
                results.append({
                    "file": file_path,
                    "success": True,
                    "data": result
                })
            except Exception as e:
                results.append({
                    "file": file_path,
                    "success": False,
                    "error": str(e)
                })

        return results

    def get_file_metadata(self, file_path: str, doc_type: str) -> dict:
        # extrai metadados padrão de um arquivo
        path = Path(file_path)
        mod_time = os.path.getmtime(file_path)

        return {
            "tipo": doc_type,
            "fonte": path.name,
            "data": datetime.fromtimestamp(mod_time).strftime("%Y-%m-%d"),
            "caminho": str(path),
            "categoria": path.parent.name
        }
