from docling.document_converter import DocumentConverter
from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext

class IngestionFilter(Filter):
    def __init__(self):
        self.converter = DocumentConverter()

    def process(self, context: PipelineContext) -> None:
        if not context.pdf_path:
            raise ValueError(">> pdf_path não foi fornecido")

        # result = self.converter.convert(context.pdf_path)
        #markdown = result.document.export_to_markdown() # apenas pra visualização de tabelas/estruturas do pdf

        #context.markdown_text = markdown