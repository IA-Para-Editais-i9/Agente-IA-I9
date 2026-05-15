from pypdf import PdfReader, PdfWriter
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
    
    # caso seja necessário posteriormente, função pra o chunking pdf
    '''
    def split_pdf(self, pdf_path) -> list[str]: # vai retornar uma lista de paths para os chunks de pdf
        ''''''
        Divide PDFs grandes em blocos menores para evitar:
        - std::bad_alloc
        - travamentos com OCR
        - excesso de memória
        ''''''

        reader = PdfReader(pdf_path)
        total_pages = len(reader.pages)
        chunk_files = []

        if total_pages <= self.chunk_size:  # se o pdf for pequeno/menor que os chunks
            return [pdf_path] # retorna o pdf

        file_name = os.path.splitext(os.path.basename(pdf_path))[0] # pega o nome do arquivo

        for start in range(0, total_pages, self.chunk_size):  # loop de 0 -> última pagina, pulando o número de paginas do chunk
            writer = PdfWriter()
            end = min(start + self.chunk_size, total_pages) # define onde o chunk atual termina

            for page_num in range(start, end):
                writer.add_page(reader.pages[page_num]) # copia as páginas 

            chunk_path = os.path.join(
                self.temp_dir,
                f"{file_name}_chunk_{start + 1}_{end}.pdf" # cria o nome do novo arquivo, indicando as páginas dele
            )

            with open(chunk_path, "wb") as f:
                writer.write(f) # salva o novo pdf

            chunk_files.append(chunk_path)

        return chunk_files
    
    '''
    