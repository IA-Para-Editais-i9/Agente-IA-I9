
from fastapi import APIRouter, UploadFile, File, HTTPException
import shutil
import os
from pathlib import Path
from src.schemas.resultado_fit import ResultadoFit
from src.pipeline.pipeline import Pipeline, build_pipeline
from src.pipeline.context import PipelineContext

router = APIRouter()

# Configurações de limites
MAX_FILE_SIZE = 100 * 1024 * 1024  # 100MB
TEMP_DIR = Path("temp_uploads")
TEMP_DIR.mkdir(exist_ok=True) # Cria a pasta se não existir

@router.post("/analisar-edital", response_model=ResultadoFit)
async def analisar_edital(file: UploadFile = File(...)):
    # 1. Validação de Formato
    if file.content_type != "application/pdf":
        raise HTTPException(status_code=400, detail="O arquivo deve ser um PDF.")

    # 2. Salva o arquivo temporariamente para o pipeline conseguir ler do disco
    temp_file_path = TEMP_DIR / file.filename
    
    try:
        # Salva o conteúdo binário no arquivo físico
        with temp_file_path.open("wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # 3. Execução do Pipeline (Ajustado para o Contexto da Lanna/Rebecca)
        # Usamos pdf_path.resolve() para passar o caminho completo e absoluto
        ctx = PipelineContext(
            pdf_path=str(temp_file_path.resolve()), 
            markdown_text=""
        ) 
        
        pipeline = build_pipeline()
        resultado_contexto = pipeline.run(ctx)
        
        # 4. Retorno do Resultado
        # No context.py delas, o objeto final se chama 'resultado_fit'
        if resultado_contexto.resultado_fit is None:
            raise Exception("O pipeline terminou, mas o 'resultado_fit' está vazio.")
            
        return resultado_contexto.resultado_fit
    
    except Exception as e:
        # Log de erro para o terminal
        print(f"ERRO CRÍTICO NO PIPELINE: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Erro no processamento do pipeline: {str(e)}")
    
    finally:
        # 5. Limpeza: apaga o arquivo temporário
        if temp_file_path.exists():
            os.remove(temp_file_path)
"""
Squad Responsável: Squad D — Orquestração & Backend

Responsabilidades (Task D3):
- Criar endpoint `POST /analisar-edital`
- Receber upload de PDF de edital (validação: só PDF, máx 100MB)
- Acionar o pipeline completo (Docling → ChromaDB → Agente 1 → Agente 2)
- Retornar o JSON final com o `ResultadoFit`
"""
