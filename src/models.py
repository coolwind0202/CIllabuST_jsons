from enum import StrEnum, auto

from pydantic import BaseModel


class EvaluationItem(BaseModel):
    title: str
    point: int
    way: str


class EvaluationEvent(BaseModel):
    title: str
    point: int


class Requisite(StrEnum):
    REQUIRE = auto()
    REQUIRE_ELECTIVE = auto()
    ELECTIVE = auto()


class SubjectCategory(StrEnum):
    General = auto()
    PE = auto()
    FL = auto()
    ChemBio = auto()
    Photon = auto()
    InfoSys = auto()
    Teacher = auto()
    Unknown = auto()


class Subject(BaseModel):
    name: str
    school_year: int
    requisite: Requisite
    category: SubjectCategory
    is_CAP_target: bool
    lecture_type: str
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
