import models

import logging
import re

import pymupdf
import more_itertools

def excludes(l, targets):
  return (x for x in l if x not in targets)

def parse_point(s):
    match = re.match(r"\d+", s.strip())
    if match is None:
       return 0
    
    return int(match.group(0))

def parse_chunk(chunk) -> models.Subject:
  name, *_ = excludes(chunk[0], ["科 目 名", None])
  logging.debug("Parse %s", name)

  raw_school_year, required_elective, raw_is_CAP_target = excludes(chunk[1], ["配 当 学 年", "必修・選択", "ＣＡＰ制", None])

  school_year = int(raw_school_year[0])
  is_required = "必修" in required_elective
  is_elective = "選択" in required_elective
  is_CAP_target = raw_is_CAP_target == "必修"

  logging.debug(school_year)
  logging.debug(is_required)
  logging.debug(is_elective)
  logging.debug(is_CAP_target)

  category, raw_credits, _ = excludes(chunk[2], ["授 業 の 種 類", "単位数", "授業回数", None])
  credits = int(raw_credits[0])

  logging.debug(category)
  logging.debug(credits)


  raw_teacher_names, credit_manager = excludes(chunk[3], ["授 業 担 当 者", "単位認定責任者", None])
  teacher_names = "".join(raw_teacher_names).split("、")
  logging.debug(teacher_names)
  logging.debug(credit_manager)


  summary, *_ = excludes(chunk[6], ["授業科目の概要", None])
  logging.debug(summary)


  goal, *_ = excludes(chunk[7], ["授 業 科 目 の\n到 達 目 標", None])
  logging.debug(goal)

  raw_evaluation_items = (list(excludes(row, [None, ""])) for row in chunk[9: 18])
  evaluation_items = (
      models.EvaluationItem(title=title, point=parse_point(detail[0]), way=detail[1])
      for title, *detail in raw_evaluation_items if len(detail) == 2
  )
  logging.debug(evaluation_items)

  cources = (more_itertools.collapse(excludes(row[1:], [None]) for row in chunk[19:34]))
  logging.debug(cources)

  self_study, *_ = excludes(chunk[34], ["授業外学修について", None])
  logging.debug(self_study)

  textbook, *_ = excludes(chunk[35], ["教 科 書", None])
  logging.debug(textbook)

  reference, *_ = excludes(chunk[36], ["参 考 文 献", None])
  logging.debug(reference)

  raw_evaluation_events = (excludes(list(zip(*chunk[37:40])), [(None, None, None), ("試 験 等 の 実 施", None, "成績評価の割合")]))
  evaluation_events = [
      models.EvaluationEvent(title=title, point=parse_point(raw_point))
      for title, _, raw_point in raw_evaluation_events
  ]
  logging.debug(evaluation_events)

  evaluation_criterion, *_ = excludes(chunk[40], ["成績評価の基準", None])
  logging.debug(evaluation_criterion)
  additional_information, *_ = excludes(chunk[41], ["試験等の実施、成\n績評価の基準に関\nする補足事項", None])
  logging.debug(additional_information)

  return models.Subject(
      name=name,
      school_year=school_year,
      is_required=is_required,
      is_elective=is_elective,
      is_CAP_target=is_CAP_target,
      category= category,
      credits= credits,
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
      additional_information=additional_information
  )

def parse_pdf(doc: pymupdf.Document) -> list[models.Subject]:
    nested_rows = ([table.extract() for table in page.find_tables().tables] for page in doc)
    rows = list(more_itertools.collapse(nested_rows, levels=2))

    chunks = list(more_itertools.chunked(rows, 42))
    return [parse_chunk(chunk) for chunk in chunks]
