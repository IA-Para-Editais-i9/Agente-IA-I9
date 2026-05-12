import logging
import time

from fastapi import FastAPI

# configuração do logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)

logger = logging.getLogger("agente-ia-i9")


def run_pipeline_with_logging(pipeline, context):
    """
    Executa o pipeline registrando tempo de cada etapa.
    """
    logger.info(f"Iniciando processamento do edital: {context.pdf_path}")
    total_start = time.time()

    for f in pipeline.filters:
        nome = type(f).__name__
        start = time.time()
        try:
            result = f.process(context)
            if result is not None:
                context = result
            elapsed = round(time.time() - start, 2)
            logger.info(f"[OK] {nome} concluído em {elapsed}s")
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            logger.error(f"[ERRO] {nome} falhou após {elapsed}s: {e}")
            raise

    total = round(time.time() - total_start, 2)
    logger.info(f"Pipeline completo em {total}s")
    return context


app = FastAPI(
    title="Agente IA i9+",
    description="API para análise de editais e verificação de fit da empresa.",
    version="1.0.0",
)


@app.get("/")
def health_check():
    return {"status": "ok", "message": "Agente IA i9+ rodando!"}