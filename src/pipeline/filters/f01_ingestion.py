from __future__ import annotations

import logging
import os
import re
import urllib.request
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from src.pipeline.base import Filter
from src.pipeline.context import PipelineContext

# ---------------------------------------------------------------------------
# PDF -> Markdown (PyMuPDF + OCR opcional)
# Código e lógica trazidos de `scripts/pdf_para_markdown.py`.
# ---------------------------------------------------------------------------

# OCR imports (pytesseract + Pillow)
try:
    import pytesseract
    from PIL import Image

    OCR_PY_DEPS_AVAILABLE = True
except ImportError:
    OCR_PY_DEPS_AVAILABLE = False

# Desabilita extensões proprietárias do PyMuPDF (consistência entre ambientes).
os.environ.setdefault("PYMUPDF_DISABLE_EXTRA", "1")

try:
    import fitz  # PyMuPDF
except ImportError as e:  # pragma: no cover
    raise ImportError("Instale o PyMuPDF: pip install pymupdf") from e

fitz.TOOLS.set_aa_level(0)

logger = logging.getLogger(__name__)


def _maybe_configure_ocr(lang: str = "por") -> bool:
    """
    Tenta habilitar OCR (tesseract + traineddata) sem exigir configuração manual.

    Estratégia:
    - Se já há `TESSDATA_PREFIX`, usa.
    - Tenta caminhos comuns de tessdata no Linux.
    - Se não encontrar, baixa `*.traineddata` para cache em `~/.cache/agente-ia-i9/tessdata`
      e aponta `TESSDATA_PREFIX` para lá.

    Retorna True se OCR parece funcional; False caso contrário.
    """
    if not OCR_PY_DEPS_AVAILABLE:
        return False

    # Se o usuário setou, respeita.
    if os.getenv("TESSDATA_PREFIX"):
        try:
            _img = Image.new("RGB", (1, 1), color=(255, 255, 255))
            pytesseract.image_to_string(_img, lang=lang)
            return True
        except Exception:
            return False

    # Caminhos comuns (Arch/Ubuntu variam).
    candidates = [
        "/usr/share/tessdata",
        "/usr/share/tesseract-ocr/tessdata",
        "/usr/share/tesseract-ocr/5/tessdata",
        "/usr/share/tesseract-ocr/4.00/tessdata",
    ]
    for c in candidates:
        if Path(c).exists():
            os.environ["TESSDATA_PREFIX"] = c
            try:
                _img = Image.new("RGB", (1, 1), color=(255, 255, 255))
                pytesseract.image_to_string(_img, lang=lang)
                return True
            except Exception:
                os.environ.pop("TESSDATA_PREFIX", None)

    # Cache local: baixa traineddata se necessário.
    cache_dir = Path.home() / ".cache" / "agente-ia-i9" / "tessdata"
    cache_dir.mkdir(parents=True, exist_ok=True)
    trained = cache_dir / f"{lang}.traineddata"

    if not trained.exists():
        # Fonte oficial (tessdata_fast) — menor e rápida.
        url = f"https://github.com/tesseract-ocr/tessdata_fast/raw/main/{lang}.traineddata"
        try:
            logger.warning("OCR: baixando '%s' para cache local (%s).", f"{lang}.traineddata", cache_dir)
            with urllib.request.urlopen(url, timeout=30) as r:  # nosec - URL fixa
                trained.write_bytes(r.read())
        except Exception as e:
            logger.warning("OCR: falha ao baixar traineddata (%s). OCR ficará desabilitado.", e)
            return False

    os.environ["TESSDATA_PREFIX"] = str(cache_dir)
    try:
        _img = Image.new("RGB", (1, 1), color=(255, 255, 255))
        pytesseract.image_to_string(_img, lang=lang)
        return True
    except Exception as e:
        logger.warning("OCR: tesseract não funcional mesmo após setup (%s).", e)
        return False


OCR_AVAILABLE = _maybe_configure_ocr(lang=os.getenv("TESSERACT_LANG", "por"))


class TextBlock:
    def __init__(
        self,
        text: str,
        font_size: float,
        is_bold: bool,
        is_italic: bool,
        block_type: str,
        page: int,
        bbox: Tuple[float, float, float, float],
    ):
        self.text = text
        self.font_size = font_size
        self.is_bold = is_bold
        self.is_italic = is_italic
        self.block_type = block_type
        self.page = page
        self.bbox = bbox


class TableBlock:
    def __init__(self, rows: List[List[str]], page: int, bbox: Tuple[float, float, float, float]):
        self.rows = rows
        self.page = page
        self.bbox = bbox


def _fix_encoding(text: str) -> str:
    try:
        return text.encode("latin-1").decode("utf-8")
    except (UnicodeEncodeError, UnicodeDecodeError):
        return text


def _percentile(data: list, pct: float) -> float:
    if not data:
        return 10.0
    sorted_data = sorted(data)
    idx = min(int(len(sorted_data) * pct / 100), len(sorted_data) - 1)
    return sorted_data[idx]


def _collect_font_stats(doc: "fitz.Document") -> dict:
    sizes: List[float] = []
    for page in doc:
        blocks = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)["blocks"]
        for block in blocks:
            if block.get("type") != 0:
                continue
            for line in block.get("lines", []):
                for span in line.get("spans", []):
                    if span["text"].strip():
                        sizes.append(round(span["size"], 1))

    if len(sizes) < 10:
        logger.warning("Poucos spans de texto encontrados (%d). Usando thresholds padrão de fonte.", len(sizes))
        return {"body": 10.0, "h3": 11.0, "h2": 13.0, "h1": 16.0}

    body_size = _percentile(sizes, 40)

    if body_size < 6.0:
        logger.warning("Tamanho de corpo estimado muito pequeno (%.1f pt). Usando thresholds padrão.", body_size)
        return {"body": 10.0, "h3": 11.0, "h2": 13.0, "h1": 16.0}

    return {"body": body_size, "h3": body_size * 1.1, "h2": body_size * 1.3, "h1": body_size * 1.6}


def _classify_line(span_size: float, is_bold: bool, text: str, thresholds: dict) -> str:
    text = text.strip()

    if re.match(r"^[\u2022\u2023\u25aa\u25cf\-\*•]\s", text):
        return "list_item"
    if re.match(r"^\d+[\.\)]\s", text):
        return "list_item"
    if re.match(r"^[a-zA-Z]\.\s", text):
        return "list_item"
    if re.match(r"^\(\d+\)\s", text):
        return "list_item"

    if span_size >= thresholds["h1"]:
        return "heading_1"
    if span_size >= thresholds["h2"]:
        return "heading_2"
    if span_size >= thresholds["h3"] or (is_bold and len(text) < 120):
        return "heading_3"

    return "body"


def _extract_tables_from_page(page: "fitz.Page") -> List[TableBlock]:
    tables: List[TableBlock] = []
    try:
        tab_finder = page.find_tables()
        for tab in tab_finder.tables:
            rows = [[cell.strip() if cell else "" for cell in row] for row in tab.extract()]
            if rows:
                tables.append(TableBlock(rows=rows, page=page.number + 1, bbox=tab.bbox))
    except AttributeError:
        logger.debug("find_tables() indisponível. Tabelas tratadas como texto na página %d.", page.number + 1)
    return tables


def _bbox_overlaps_any(bbox: Tuple, bboxes: List[Tuple], tolerance: float = 5.0) -> bool:
    x0, y0, x1, y1 = bbox
    for bx0, by0, bx1, by1 in bboxes:
        if x0 < bx1 + tolerance and x1 > bx0 - tolerance and y0 < by1 + tolerance and y1 > by0 - tolerance:
            return True
    return False


def _blocks_to_text_blocks(page: "fitz.Page", thresholds: dict, table_bboxes: List[Tuple]) -> List[TextBlock]:
    result: List[TextBlock] = []
    raw = page.get_text("dict", flags=fitz.TEXT_PRESERVE_WHITESPACE)

    for block in raw.get("blocks", []):
        if block.get("type") != 0:
            continue
        block_bbox = tuple(block["bbox"])
        if _bbox_overlaps_any(block_bbox, table_bboxes):
            continue

        for line in block.get("lines", []):
            spans = line.get("spans", [])
            if not spans:
                continue
            line_text = " ".join(_fix_encoding(s["text"]) for s in spans).strip()
            if not line_text:
                continue

            dominant = max(spans, key=lambda s: s["size"])
            size = dominant["size"]
            flags = dominant["flags"]
            is_bold = bool(flags & 2**4)
            is_italic = bool(flags & 2**1)

            block_type = _classify_line(size, is_bold, line_text, thresholds)
            result.append(
                TextBlock(
                    text=line_text,
                    font_size=round(size, 1),
                    is_bold=is_bold,
                    is_italic=is_italic,
                    block_type=block_type,
                    page=page.number + 1,
                    bbox=tuple(line["bbox"]),
                )
            )

    if not result and OCR_AVAILABLE:
        try:
            pix = page.get_pixmap(dpi=300)
            img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
            ocr_lang = os.getenv("TESSERACT_LANG", "por")
            ocr_text = pytesseract.image_to_string(img, lang=ocr_lang)
            if ocr_text.strip():
                result.append(
                    TextBlock(
                        text=ocr_text.strip(),
                        font_size=10.0,
                        is_bold=False,
                        is_italic=False,
                        block_type="body",
                        page=page.number + 1,
                        bbox=page.rect,
                    )
                )
        except Exception as e:
            logger.debug("Falha no OCR da página %d: %s", page.number + 1, e)

    return result


def _merge_body_lines(blocks: List[TextBlock]) -> List[TextBlock]:
    if not blocks:
        return blocks

    merged: List[TextBlock] = []
    current = blocks[0]

    for nxt in blocks[1:]:
        same_type = current.block_type == nxt.block_type == "body"
        same_page = current.page == nxt.page
        gap = nxt.bbox[1] - current.bbox[3]
        line_height = current.bbox[3] - current.bbox[1]
        close_vertical = 0 <= gap < line_height * 1.5

        if same_type and same_page and close_vertical:
            current = TextBlock(
                text=current.text + " " + nxt.text,
                font_size=current.font_size,
                is_bold=current.is_bold,
                is_italic=current.is_italic,
                block_type="body",
                page=current.page,
                bbox=(min(current.bbox[0], nxt.bbox[0]), current.bbox[1], max(current.bbox[2], nxt.bbox[2]), nxt.bbox[3]),
            )
        else:
            merged.append(current)
            current = nxt

    merged.append(current)
    return merged


def _remove_repeated_headers(blocks: list, threshold: float = 0.6) -> list:
    text_pages: Dict[str, set] = {}
    text_only = [b for b in blocks if isinstance(b, TextBlock)]
    total_pages = max((b.page for b in text_only), default=1)

    for block in text_only:
        if block.text.strip():
            text_pages.setdefault(block.text.strip(), set()).add(block.page)

    repeated = {t for t, pages in text_pages.items() if len(pages) / total_pages >= threshold and total_pages > 2}

    return [b for b in blocks if b is None or isinstance(b, TableBlock) or (isinstance(b, TextBlock) and b.text.strip() not in repeated)]


def _table_to_markdown(table: TableBlock) -> str:
    if not table.rows:
        return ""

    ncols = max((len(row) for row in table.rows), default=0)
    if ncols == 0:
        return ""

    rows = [row + [""] * (ncols - len(row)) for row in table.rows]
    widths = [max(max(len(rows[r][c]) for r in range(len(rows))), 3) for c in range(ncols)]

    def fmt_row(row: List[str]) -> str:
        return "| " + " | ".join(cell.ljust(w) for cell, w in zip(row, widths)) + " |"

    lines = [fmt_row(rows[0])]
    lines.append("| " + " | ".join("-" * w for w in widths) + " |")
    for row in rows[1:]:
        lines.append(fmt_row(row))

    return "\n".join(lines)


def _block_to_markdown(block) -> str:
    if isinstance(block, TableBlock):
        return _table_to_markdown(block)

    text = block.text.strip()
    if not text:
        return ""

    btype = block.block_type

    if btype == "heading_1":
        return f"# {text}"
    if btype == "heading_2":
        return f"## {text}"
    if btype == "heading_3":
        return f"### {text}"
    if btype == "list_item":
        clean = re.sub(r"^[\u2022\u2023\u25aa\u25cf\-\*•]\s+", "", text)
        clean = re.sub(r"^\d+[\.\)]\s+", "", clean)
        clean = re.sub(r"^[a-zA-Z]\.\s+", "", clean)
        clean = re.sub(r"^\(\d+\)\s+", "", clean)
        return f"- {clean}"

    return text


def pdf_to_markdown(pdf_path: str, include_page_breaks: bool = False, deduplicate_headers: bool = True) -> str:
    pdf_path_obj = Path(pdf_path)
    if not pdf_path_obj.exists():
        raise FileNotFoundError(f"Arquivo não encontrado: {pdf_path}")

    doc = fitz.open(str(pdf_path_obj))
    thresholds = _collect_font_stats(doc)

    all_blocks: list = []

    for page in doc:
        tables = _extract_tables_from_page(page)
        table_bboxes = [t.bbox for t in tables]

        text_blocks = _blocks_to_text_blocks(page, thresholds, table_bboxes)
        text_blocks = _merge_body_lines(text_blocks)

        combined: list = list(text_blocks) + list(tables)
        combined.sort(key=lambda b: b.bbox[1])

        if include_page_breaks and page.number > 0:
            all_blocks.append(None)

        all_blocks.extend(combined)

    doc.close()

    if deduplicate_headers:
        all_blocks = _remove_repeated_headers(all_blocks)

    lines: List[str] = []
    prev_type: Optional[str] = None

    for block in all_blocks:
        if block is None:
            lines.append("\n---\n")
            prev_type = None
            continue

        md = _block_to_markdown(block)
        if not md.strip():
            continue

        btype = getattr(block, "block_type", "table")
        needs_blank_before = (
            btype in ("heading_1", "heading_2", "heading_3")
            or prev_type in ("heading_1", "heading_2", "heading_3")
            or (btype == "body" and prev_type == "body")
            or btype == "table"
        )

        if needs_blank_before and lines:
            lines.append("")

        lines.append(md)
        prev_type = btype

    return "\n".join(lines).strip() + "\n"

# ---------------------------------------------------------------------------
# Docling (desativado por enquanto)
# ---------------------------------------------------------------------------
# from docling.document_converter import DocumentConverter


class IngestionFilter(Filter):
    """
    Filter responsável por:
    1. Receber um PDF
    2. Processar com Docling
    4. Exportar para Markdown
    5. Realizar limpeza básica do texto
    6. Salvar no PipelineContext
    """
    def __init__(self):
        # Docling desativado temporariamente.
        # self.converter = DocumentConverter()
        pass

    def run(self, context: PipelineContext) -> PipelineContext:
        self.process(context)
        return context

    def process(self, context: PipelineContext) -> PipelineContext:
        pdf_path = context.pdf_path

        if not os.path.exists(pdf_path):
            raise FileNotFoundError(f">> PDF não encontrado: {pdf_path}")

        try:
            # --- Docling (desativado por enquanto) ---
            # result = self.converter.convert(pdf_path)  # converte em docling
            # markdown = result.document.export_to_markdown()  # exporta em markdown

            markdown = pdf_to_markdown(pdf_path)
            markdown = self.clean_markdown(markdown) # remove colunas repetidas e refina markdown

            context.markdown_text = markdown
        except Exception as e:
            print(f"\n>> Erro ao processar PDF {pdf_path}: {e}")


    def clean_markdown(self, text) -> str:
        """
        Limpeza inicial dos principais edge cases encontrados na A1.
        """

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
        """
        Remove colunas duplicadas simples em tabelas Markdown.

        Exemplo:
        | A | A | A | Nota |

        vira:
        | A | Nota |
        """

        # separa a linha usando |, remove espaços estras, ignora valores vazios
        columns = [col.strip() for col in row.split("|") if col.strip()]

        unique_columns = [] # salva valores unicos


        for column in columns:
            if column not in unique_columns:
                unique_columns.append(column)

        # reconstroe a linha da tabela
        return "| " + " | ".join(unique_columns) + " |"
