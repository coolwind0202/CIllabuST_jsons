import pymupdf
import more_itertools
from loguru import logger

PE_FL_PAGE_INDEX = 1
PE_TABLE_INDEX = 1

def parse_pe_page_cell_texts(content) -> list[str]:
    logger.debug("Parsing PE page cell texts")

    doc = pymupdf.Document(stream=content)
    tables = doc[PE_FL_PAGE_INDEX].find_tables().tables             
    cell_texts = [c for c in more_itertools.collapse(tables[PE_TABLE_INDEX].extract()) if c is not None and c != '']

    logger.debug(cell_texts)

    return cell_texts
