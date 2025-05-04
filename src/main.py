from parser import category, navigation, subject_list, syallbus
import models
import utils

import sys
from urllib.parse import unquote
import concurrent.futures
import json

import more_itertools
from loguru import logger

logger.remove()
logger.add("debug.log", level="DEBUG")
logger.add(sys.stdout, level="INFO")

if __name__ == "__main__":
    nav = navigation.fetch_navigation()

    subject_list_content = utils.fetch(nav.subject_list_url)
    pe_page_cell_texts = subject_list.parse_pe_page_cell_texts(subject_list_content)

    subject_category_classifier = category.SubjectCategoryClassifier(
            pe_possibility_detector=category.PEPossibilityDetectorByCellTexts(pe_page_cell_texts),
            filename_hint_classifier=category.FilenameHintClassifier(),
        )
    parser = syallbus.Parser(category_classifier=subject_category_classifier)


    with concurrent.futures.ProcessPoolExecutor() as executor:
        logger.info("Fetching syllabus contents")
        contents = list(executor.map(utils.fetch, nav.syllabus_urls))

        logger.info("Counting syllabus pages")
        page_counts = list(executor.map(syallbus.get_page_count, contents))

        logger.info("Extracting rows from PDF")
        file_rows = list(executor.map(syallbus.extract_rows, contents))

        logger.info("Parsing rows as subjects")
        file_chunks = list(list(more_itertools.chunked(rows, 42)) for rows in file_rows)
        file_subjects = [[parser.parse_chunk(filename=unquote(url), chunk=chunk) for chunk in chunks] for url, chunks in zip(nav.syllabus_urls, file_chunks)]
        subjects = models.Subjects(subjects=more_itertools.flatten(file_subjects))

        logger.info("Dump subjects to dist files")
        dump = subjects.model_dump_json()
        schema = json.dumps(subjects.model_json_schema())

        with open("./dist/out.json", "w") as f:
            f.write(dump)

        with open("./dist/out.schema.json", "w") as f:
            f.write(schema)

        logger.info("Complete!")
