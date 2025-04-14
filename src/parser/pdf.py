import models

import logging
import re

import pymupdf
import more_itertools


def excludes(l, targets):
    return (x for x in l if x not in targets)


def str_to_int(s):
    match = re.match(r"\d+", s.strip())
    if match is None:
        return 0

    return int(match.group(0))


def parse_chunk(chunk) -> models.Subject:
    _, name, *_ = excludes(chunk[0], [None])
    logging.debug("Parse %s", name)

    _, raw_school_year, _, required_elective, _, raw_is_CAP_target, *_ = excludes(
        chunk[1], [None]
    )

    school_year = str_to_int(raw_school_year)
    requisite = models.Requisite(required_elective.strip())
    is_CAP_target = raw_is_CAP_target == "対象"

    logging.debug(school_year)
    logging.debug(requisite)
    logging.debug(is_CAP_target)

    _, category, _, raw_credits, _, raw_cource_count, *_ = excludes(chunk[2], [None])
    credits = str_to_int(raw_credits)
    cource_count = str_to_int(raw_cource_count)

    logging.debug(category)
    logging.debug(credits)
    logging.debug(cource_count)

    _, raw_teacher_names, _, credit_manager, *_ = excludes(chunk[3], [None])
    teacher_names = "".join(raw_teacher_names).split("、")
    logging.debug(teacher_names)
    logging.debug(credit_manager)

    _, summary, *_ = excludes(chunk[6], [None])
    logging.debug(summary)

    _, goal, *_ = excludes(chunk[7], [None])
    logging.debug(goal)

    raw_evaluation_items = (list(excludes(row, [None, ""])) for row in chunk[9:18])
    evaluation_items = (
        models.EvaluationItem(title=title, point=str_to_int(detail[0]), way=detail[1])
        for title, *detail in raw_evaluation_items
        if len(detail) == 2
    )
    logging.debug(evaluation_items)

    cources = more_itertools.collapse(excludes(row[1:], [None]) for row in chunk[19:34])
    logging.debug(cources)

    _, self_study, *_ = excludes(chunk[34], [None])
    logging.debug(self_study)

    _, textbook, *_ = excludes(chunk[35], [None])
    logging.debug(textbook)

    _, reference, *_ = excludes(chunk[36], [None])
    logging.debug(reference)

    _, *raw_evaluation_events = excludes(list(zip(*chunk[37:40])), [(None, None, None)])
    evaluation_events = [
        models.EvaluationEvent(title=title, point=str_to_int(raw_point))
        for title, _, raw_point in raw_evaluation_events
    ]
    logging.debug(evaluation_events)

    _, evaluation_criterion, *_ = excludes(chunk[40], [None])
    logging.debug(evaluation_criterion)

    _, additional_information, *_ = excludes(chunk[41], [None])
    logging.debug(additional_information)

    return models.Subject(
        name=name,
        school_year=school_year,
        requisite=requisite,
        is_CAP_target=is_CAP_target,
        category=category,
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

def extract_rows(content, index):
    logging.info("Extracting rows at Page %d on %s", index, content[:20])

    doc = pymupdf.Document(stream=content)
    page = doc.load_page(index)

    inner_rect = pymupdf.Rect(0, page.rect.height * 0.06, page.rect.br)
    tables = page.find_tables(clip=inner_rect)

    rows = [table.extract() for table in tables]
    logging.info("Extracted rows at Page %d on %s", index, content[:20])

    return rows

def get_page_count(content):
    return pymupdf.Document(stream=content).page_count