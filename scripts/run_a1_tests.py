from src.pipeline.pipeline import Pipeline
from src.pipeline.context import PipelineContext
from src.pipeline.filters.f01_ingestion import IngestionFilter
import os
'''
teste da atividade 1 Squad A, cria a pasta output(já no gitignore) e cria txt dos markdown dos editais pra conferencia de tabelas/estruturas/edge cases
'''

PDFS = [
    "data/editais/samples/06_02_2026_T_Energetica_Regulamento.pdf",
    # "data/editais/samples/Boletim-de-Oportunidades-09-2025.pdf",
    # "data/editais/samples/Chamada-Publica-03.2025-MCTI embrapii.pdf"
]

def main():
    os.makedirs("outputs", exist_ok=True)
    pipeline = Pipeline([IngestionFilter()])

   
    for pdf in PDFS:
        print(f"\n>> Processando: {pdf}")

        context = PipelineContext(pdf_path=pdf)
        result = pipeline.run(context)

        output_file = f"outputs/{os.path.basename(pdf)}.txt"

        with open(output_file, "w", encoding="utf-8") as f:
            f.write(result.markdown_text)

        print(f"Arquivo salvo em: {output_file}")
        print("Processamento concluído.")

    '''
        print(f">> Processando: {pdf}")

        print("\n=== INÍCIO ===\n")
        print(result.markdown_text[:2000])

        print("\n=== FIM ===\n")
        print(result.markdown_text[-1000:])
    '''

if __name__ == "__main__":
    main()