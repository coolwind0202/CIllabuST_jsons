from parser import pdf
import models

import sys
from urllib.parse import urljoin, unquote
import concurrent.futures
import json

from bs4 import BeautifulSoup
import requests
import more_itertools
from loguru import logger

logger.remove()
logger.add("debug.log", level="DEBUG")
logger.add(sys.stdout, level="INFO")

DOMAIN = "https://www.chitose.ac.jp"
SYLLABUSES_PAGE_PATH = "/info/info_index/311"

def fetch(url: str):
    logger.debug(f"Requesting {unquote(url)}")

    resp = requests.get(url)
    if resp.status_code != requests.codes.ok:
        logger.error(f"Failed to fetch {unquote(url)}")
        return b""

    logger.debug("Fetched %s", unquote(url))
    return resp.content 

if __name__ == "__main__":
    logger.info("Fetching syllabus URLs")
    syllabuses_page_url = urljoin(DOMAIN, SYLLABUSES_PAGE_PATH)
    resp = requests.get(syllabuses_page_url)

    if resp.status_code != requests.codes.ok:
        logger.error("Request failed to %s", syllabuses_page_url)
        logger.error("Status Code: %d", resp.status_code)
        logger.error("Content: %s", resp.content)
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    syllabus_paths = [
        a["href"]
        for a in soup.find_all("a")
        if "シラバス" in str(a) and "大学院" not in str(a)
    ]

    syllabus_urls = [urljoin(DOMAIN, path) for path in syllabus_paths]

    with concurrent.futures.ProcessPoolExecutor() as executor:
        # TODO: 将来的には、Submitで非同期的に実行し、この直下でQueueを使って待機するように書き換える
        logger.info("Fetching syllabus contents")
        contents = list(executor.map(fetch, syllabus_urls))


        logger.info("Counting syllabus pages")
        page_counts = map(pdf.get_page_count, contents)


        logger.info("Extracting rows from PDF")
        nested_worker_args = (((content, i) for i in range(page_count)) for content, page_count in zip(contents, page_counts))
        worker_args = list(more_itertools.flatten(nested_worker_args))

        nested_rows = executor.map(pdf.extract_rows, *zip(*worker_args))
        rows = more_itertools.collapse(nested_rows, levels=2)


        logger.info("Parsing rows as subjects")
        chunks = list(more_itertools.chunked(rows, 42))
        subjects = models.Subjects(subjects=[pdf.parse_chunk(chunk) for chunk in chunks])    


        logger.info("Dump subjects to dist files")
        dump = subjects.model_dump_json()
        schema = json.dumps(subjects.model_json_schema())

        with open("./dist/out.json", "w") as f:
            f.write(dump)        

        with open("./dist/out.schema.json", "w") as f:
            f.write(schema)

        logger.info("Complete!")