import utils

from dataclasses import dataclass
from urllib.parse import urljoin
import sys

from loguru import logger
from bs4 import BeautifulSoup

DOMAIN = "https://www.chitose.ac.jp"
SYLLABUSES_PAGE_PATH = "/info/info_index/311"

@dataclass
class Navigation:
    syllabus_urls: list[str]
    subject_list_url: str | None


def fetch_navigation() -> Navigation:
    logger.info("Fetching syllabus URLs")
    
    syllabuses_page_url = urljoin(DOMAIN, SYLLABUSES_PAGE_PATH)
    content = utils.fetch(syllabuses_page_url)

    soup = BeautifulSoup(content.decode(), "html.parser")
    
    syllabus_a_elements = soup.find_all(lambda tag: tag.name == "a" and "シラバス" in str(tag) and "大学院" not in str(tag))
    syllabus_paths = [a["href"] for a in syllabus_a_elements]
    syllabus_urls = [urljoin(DOMAIN, path) for path in syllabus_paths]
    logger.debug(syllabus_urls)

    subject_list_a_element = soup.find(lambda tag: tag.name == "a" and "開講科目一覧" in str(tag))
    if subject_list_a_element is None:
        logger.error("Subject list link is not found")
        sys.exit(1)
    
    subject_list_path = subject_list_a_element["href"]
    subject_list_url = urljoin(DOMAIN, subject_list_path)
    logger.debug(subject_list_url)

    return Navigation(syllabus_urls=syllabus_urls, subject_list_url=subject_list_url)