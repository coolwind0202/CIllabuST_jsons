import models

from enum import auto, StrEnum
from typing import Protocol


class FilenameHint(StrEnum):
    General = auto()
    PEOrFL = auto()
    ChemBio = auto()
    Photon = auto()
    InfoSys = auto()
    Teacher = auto()
    Unknown = auto()

    def decide(self, is_pe_possibly: bool) -> models.SubjectCategory:
        match self:
            case FilenameHint.PEOrFL:
                if is_pe_possibly:
                    return models.SubjectCategory.PE
                else:
                    return models.SubjectCategory.FL
            case _:
                return models.SubjectCategory[self.name]


class BaseFilenameHintClassifier(Protocol):
    def classify(self, filename: str) -> FilenameHint: ...


class FilenameHintClassifier(BaseFilenameHintClassifier):
    def classify(self, filename: str):
        patterns = {
            "外国語": FilenameHint.PEOrFL,
            "共通教育科目": FilenameHint.General,
            "応用化学生物学科": FilenameHint.ChemBio,
            "電子光工学科": FilenameHint.Photon,
            "情報システム工学科": FilenameHint.InfoSys,
            "教職科目": FilenameHint.Teacher,
        }

        for pattern, filename_hint in patterns.items():
            if pattern in filename:
                return filename_hint
        
        return FilenameHint.Unknown


class BasePEPossibilityDetector(Protocol):
    def has_possibility(self, subject_name: str) -> bool: ...


class PEPossibilityDetectorByCellTexts(BasePEPossibilityDetector):
    cell_texts: list[str]

    def __init__(self, cell_texts: list[str]):
        self.cell_texts = cell_texts

    def has_possibility(self, subject_name: str) -> bool:
        return subject_name in self.cell_texts


class BaseSubjectCategoryClassifier(Protocol):
    def classify(self, *, subject_name: str, filename: str) -> models.SubjectCategory: ...


class SubjectCategoryClassifier(BaseSubjectCategoryClassifier):
    pe_possibility_detector: BasePEPossibilityDetector
    filename_hint_classifier: BaseFilenameHintClassifier

    def __init__(
        self,
        *,
        pe_possibility_detector: BasePEPossibilityDetector,
        filename_hint_classifier: BaseFilenameHintClassifier,
    ):
        self.pe_possibility_detector = pe_possibility_detector
        self.filename_hint_classifier = filename_hint_classifier

    def classify(self, *, subject_name: str, filename: str) -> models.SubjectCategory:
        has_pe_possibility = self.pe_possibility_detector.has_possibility(subject_name)
        filename_hint = self.filename_hint_classifier.classify(filename)

        return filename_hint.decide(has_pe_possibility)
