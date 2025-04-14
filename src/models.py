from enum import StrEnum

from pydantic import BaseModel

class EvaluationItem(BaseModel):
  title: str
  point: int
  way: str

class EvaluationEvent(BaseModel):
  title: str
  point: int

class Requisite(StrEnum):
  REQUIRE = "必修"
  REQUIRE_ELECTIVE = "選択必修"
  ELECTIVE = "選択"

class Subject(BaseModel):
  name: str
  school_year: int
  requisite: Requisite
  is_CAP_target: bool
  category: str
  credits: int
  teacher_names: list[str]
  credit_manager: str
  summary: str
  goal: str
  evaluation_items: list[EvaluationItem]
  cources: list[str]
  self_study: str
  textbook: str
  reference: str
  evaluation_events: list[EvaluationEvent]
  evaluation_criterion: str
  additional_information: str

class Subjects(BaseModel):
  subjects: list[Subject]