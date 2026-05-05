from docling.document_converter import DocumentConverter
from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext
import os


class IngestionFilter(Filter):
    '''
    Filter responsável por:
    1. Receber um PDF
    2. Processar com Docling
    4. Exportar para Markdown   
    5. Realizar limpeza básica do texto
    6. Salvar no PipelineContext
    '''
    def __init__(self):
        self.converter = DocumentConverter()

    def process(self, context: PipelineContext) -> None:
        pdf_path = context.pdf_path

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f">> PDF não encontrado: {pdf_path}")

        try:
            result = self.converter.convert(pdf_path)  # converte em docling
            markdown = result.document.export_to_markdown()  # exporta em markdown
            markdown = self.clean_markdown(markdown) # remove colunas repetidas e refina markdown

            context.markdown_text = markdown
        except Exception as e:
            print(f"\n>> Erro ao processar PDF {pdf_path}: {e}")

        
    def clean_markdown(self, text) -> str:
        '''
        Limpeza inicial dos principais edge cases encontrados na A1.
        '''

        text = text.replace("&amp;", "&")
        text = text.replace("\\_", "_")

        lines = text.splitlines()
        cleaned_lines = []

        for line in lines:  
            # verifica se existem barras, linhas, colunas duplicadas    
            if set(line.replace("|", "").replace("-", "").replace(" ", "")) == set():
                continue
            
            # remover colunas duplicadas
            if line.strip().startswith("|"):
                line = self.remove_duplicate_columns(line)

            cleaned_lines.append(line)

        return "\n".join(cleaned_lines)
    
    def remove_duplicate_columns(self, row) -> str:
        '''
        Remove colunas duplicadas simples em tabelas Markdown.

        Exemplo:
        | A | A | A | Nota |

        vira:
        | A | Nota |
        '''

        # separa a linha usando |, remove espaços estras, ignora valores vazios
        columns = [col.strip() for col in row.split("|") if col.strip()]

        unique_columns = [] # salva valores unicos 


        for column in columns:
            if column not in unique_columns:
                unique_columns.append(column)

        # reconstroe a linha da tabela 
        return "| " + " | ".join(unique_columns) + " |"