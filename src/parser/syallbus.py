import models
from parser import category

import re

import pymupdf
import more_itertools
from loguru import logger


def excludes(l, targets):
    return (x for x in l if x not in targets)


def str_to_int(s):
    match = re.match(r"\d+", s.strip())
    if match is None:
        return 0

    return int(match.group(0))

def parse_requisite(required_elective: str) -> models.Requisite:
    if "必修" in required_elective:
        if "選択" in required_elective:
            return models.Requisite.REQUIRE_ELECTIVE
        else:
            return models.Requisite.REQUIRE
    return models.Requisite.ELECTIVE


class Parser:
    category_classifier: category.BaseSubjectCategoryClassifier

    def __init__(self, *, category_classifier: category.BaseSubjectCategoryClassifier):
        self.category_classifier = category_classifier

    def parse_chunk(self, *, filename, chunk) -> models.Subject:
        _, name, *_ = excludes(chunk[0], [None])
        logger.debug(name)

        subject_category = self.category_classifier.classify(
            filename=filename, subject_name=name
        )

        _, raw_school_year, _, required_elective, _, raw_is_CAP_target, *_ = excludes(
            chunk[1], [None]
        )

        school_year = str_to_int(raw_school_year)
        requisite = parse_requisite(required_elective)
        is_CAP_target = raw_is_CAP_target == "対象"
        logger.debug(school_year)
        logger.debug(requisite)
        logger.debug(is_CAP_target)

        _, lecture_type, _, raw_credits, _, raw_cource_count, *_ = excludes(
            chunk[2], [None]
        )
        credits = str_to_int(raw_credits)
        cource_count = str_to_int(raw_cource_count)

        logger.debug(lecture_type)
        logger.debug(credits)
        logger.debug(cource_count)

        _, raw_teacher_names, _, credit_manager, *_ = excludes(chunk[3], [None])
        teacher_names = "".join(raw_teacher_names).split("、")
        logger.debug(teacher_names)
        logger.debug(credit_manager)

        _, summary, *_ = excludes(chunk[6], [None])
        logger.debug(summary)

        _, goal, *_ = excludes(chunk[7], [None])
        logger.debug(goal)

        raw_evaluation_items = (list(excludes(row, [None, ""])) for row in chunk[9:18])
        evaluation_items = [
            models.EvaluationItem(
                title=title, point=str_to_int(detail[0]), way=detail[1]
            )
            for title, *detail in raw_evaluation_items
            if len(detail) == 2
        ]
        logger.debug(evaluation_items)

        cources = list(
            more_itertools.collapse(excludes(row[1:], [None]) for row in chunk[19:34])
        )
        logger.debug(cources)

        _, self_study, *_ = excludes(chunk[34], [None])
        logger.debug(self_study)

        _, textbook, *_ = excludes(chunk[35], [None])
        logger.debug(textbook)

        _, reference, *_ = excludes(chunk[36], [None])
        logger.debug(reference)

        _, *raw_evaluation_events = excludes(
            list(zip(*chunk[37:40])), [(None, None, None)]
        )
        evaluation_events = [
            models.EvaluationEvent(title=title, point=str_to_int(raw_point))
            for title, _, raw_point in raw_evaluation_events
        ]
        logger.debug(evaluation_events)

        _, evaluation_criterion, *_ = excludes(chunk[40], [None])
        logger.debug(evaluation_criterion)

        _, additional_information, *_ = excludes(chunk[41], [None])
        logger.debug(additional_information)

        return models.Subject(
            name=name,
            school_year=school_year,
            requisite=requisite,
            is_CAP_target=is_CAP_target,
            category=subject_category,
            lecture_type=lecture_type,
            credits=credits,
            teacher_names=teacher_names,
            credit_manager=credit_manager,
            summary=summary,
            goal=goal,
            evaluation_items=evaluation_items,
            cources=cources,
            self_study=self_study,
            textbook=textbook,
            reference=reference,
            evaluation_events=evaluation_events,
            evaluation_criterion=evaluation_criterion,
            additional_information=additional_information,
        )


def extract_rows(content):
    doc = pymupdf.Document(stream=content)

    rows_per_pages = more_itertools.flatten(extract_rows_page(page) for page in doc)
    rows = more_itertools.flatten(rows_per_pages)
    return list(rows)


def extract_rows_page(page):
    inner_rect = pymupdf.Rect(0, page.rect.height * 0.06, page.rect.br)
    tables = page.find_tables(clip=inner_rect)

    rows = [table.extract() for table in tables]
    return rows


def get_page_count(content):
    return pymupdf.Document(stream=content).page_count
