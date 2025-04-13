from parser import pdf
import models

import logging
import sys
from urllib.parse import urljoin

from bs4 import BeautifulSoup
import requests
import pymupdf
import more_itertools

logging.basicConfig(filename="debug.log", encoding='utf-8', level=logging.DEBUG)

DOMAIN = "https://www.chitose.ac.jp"
SYLLABUSES_PAGE_PATH = "/info/info_index/311"

if __name__ == "__main__":
    syllabuses_page_url = urljoin(DOMAIN, SYLLABUSES_PAGE_PATH)
    resp = requests.get(syllabuses_page_url)

    if resp.status_code != requests.codes.ok:
        logging.error("Request failed to %s", syllabuses_page_url)
        logging.error("Status Code: %d", resp.status_code)
        logging.error("Content: %s", resp.content)
        sys.exit(1)

    soup = BeautifulSoup(resp.text, "html.parser")

    syllabus_paths = [a["href"] for a in soup.find_all("a") if "シラバス" in str(a)]
    syllabus_urls = [urljoin(DOMAIN, path) for path in syllabus_paths]

    syllabus_resps = (requests.get(url) for url in syllabus_urls)
    syllabus_contents = (resp.content for resp in syllabus_resps if resp.status_code == requests.codes.ok)
    
    docs = (pymupdf.Document(stream=content) for content in syllabus_contents)
    subjects = models.Subjects(subjects=more_itertools.flatten(pdf.parse_pdf(doc) for doc in docs))

    dump = subjects.model_dump_json()
    with open("out.json", "w") as f:
        f.write(dump)