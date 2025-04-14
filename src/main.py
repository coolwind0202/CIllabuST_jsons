from parser import pdf
import models

import logging
import sys
from urllib.parse import urljoin, unquote
import concurrent.futures

from bs4 import BeautifulSoup
import requests
import more_itertools

# logging.basicConfig(filename="debug.log", encoding="utf-8", level=logging.DEBUG)
logging.basicConfig(encoding="utf-8", level=logging.INFO)

DOMAIN = "https://www.chitose.ac.jp"
SYLLABUSES_PAGE_PATH = "/info/info_index/311"

def fetch(url: str):
    logging.info("Requesting %s", unquote(url))

    resp = requests.get(url)
    if resp.status_code != requests.codes.ok:
        logging.error("Failed to fetch %s", unquote(url))
        return b""

    logging.info("Fetched %s", unquote(url))
    return resp.content 

if __name__ == "__main__":
    syllabuses_page_url = urljoin(DOMAIN, SYLLABUSES_PAGE_PATH)
    resp = requests.get(syllabuses_page_url)

    if resp.status_code != requests.codes.ok:
        logging.error("Request failed to %s", syllabuses_page_url)
        logging.error("Status Code: %d", resp.status_code)
        logging.error("Content: %s", resp.content)
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
        contents = list(executor.map(fetch, syllabus_urls))

        page_counts = map(pdf.get_page_count, contents)
        logging.info(page_counts)

        nested_worker_args = (((content, i) for i in range(page_count)) for content, page_count in zip(contents, page_counts))
        worker_args = list(more_itertools.flatten(nested_worker_args))

        nested_rows = executor.map(pdf.extract_rows, *zip(*worker_args))
        rows = more_itertools.collapse(nested_rows, levels=2)

        chunks = list(more_itertools.chunked(rows, 42))
        
        subjects = models.Subjects(subjects=[pdf.parse_chunk(chunk) for chunk in chunks])    
        dump = subjects.model_dump_json()

        with open("out.json", "w") as f:
            f.write(dump)        