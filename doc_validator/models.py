"""Модели данных приложения.

В этом модуле описаны структуры данных, используемые в программе для
представления объектов и их параметров. Использование dataclass делает
модели более удобными и понятными по сравнению со словарями и проще,
чем реализация через обычные классы с ручным управлением состоянием.
"""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from enum import Enum
import re
from typing import ClassVar

from .exceptions import DataFillError


class IssueType(Enum):
    """Перечисление типов проблем, которые могут быть обнаружены во время проверки"""

    MISSING_FILE = "missing_file"
    WRONG_EXTENSION = "wrong_extension"
    EMPTY_FILE = "empty_file"
    EXTRA_FILE = "extra_file"
    INVALID_REQUIREMENTS = "invalid_requirements"
    DIRECTORY_NOT_FOUND = "directory_not_found"
    REPORT_WRITE_ERROR = "report_write_error"

    def __str__(self):
        return self.value

    @property
    def description(self) -> str:
        issued_description = {
            IssueType.MISSING_FILE: "обязательный файл отсутствует",
            IssueType.WRONG_EXTENSION: "файл найден, но его расширение не соответствует ожидаемому",
            IssueType.EMPTY_FILE: "файл найден, но он пустой",
            IssueType.EXTRA_FILE: "в каталоге обнаружен файл, который не был указан в требованиях",
            IssueType.INVALID_REQUIREMENTS: "структура или содержимое файла требований некорректны",
            IssueType.DIRECTORY_NOT_FOUND: "целевой каталог не существует",
            IssueType.REPORT_WRITE_ERROR: "ошибка при запсии отчета"
        }
        return issued_description[self]

class Severity(Enum):
    """Уровень важности отдельной проблемы."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"

    def __str__(self):
        return self.value

    @property
    def description(self) -> str:
        descriptions = {
            Severity.INFO: "информационное сообщение",
            Severity.WARNING: "предупреждение, не блокирующее выполнение",
            Severity.ERROR: "критическая ошибка",
        }
        return descriptions[self]

class ReportFormat(Enum):
    """Перечисление поддерживаемых форматов отчетов"""

    TXT = "txt"
    JSON = "json"
    CSV = "csv"

    def __str__(self):
        return self.value


class ValidationStatus(Enum):
    """Итоговый статус проверки в целом"""

    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value

@dataclass
class ExpectedFile:
    """Описывает файл, который должен быть найден в целевом каталоге"""
    name: str
    allowed_extensions: list[str] = field(default_factory=list)
    required: bool = True

    def __post_init__(self):
        """Проверка инварианта после инициализации"""
        self._validate_name()
        self._validate_allowed_extensions()
        self._validate_required()

    def _validate_name(self) -> None:
        """Проверка инварианта имени"""
        if not isinstance(self.name, str):
            raise TypeError(f"Поле 'name' должно быть типа 'str', получено {type(self.name).__name__}")

        if len(self.name) < 1 or len(self.name) > 255:
            raise DataFillError(
                model_name="ExpectedFile",
                field="name",
                value=self.name,
                reason="длина имени должна быть от 1 до 255 символов включительно"
            )

        forbidden_chars = set('\\/:*?"<>|')
        if any(char in forbidden_chars for char in self.name):
            raise DataFillError(
                model_name="ExpectedFile",
                field="name",
                value=self.name,
                reason="имя содержит запрещенные символы из набора \\ / : * ? \" < > |"
            )

    def _validate_allowed_extensions(self) -> None:
        """Проверка инварианта списка переданных расширений"""
        if not isinstance(self.allowed_extensions, list):
            raise TypeError(f"Поле 'allowed_extensions' должно быть типа 'list', получено"
                            f" {type(self.allowed_extensions).__name__}")

        for number, element in enumerate(self.allowed_extensions):
            if not isinstance(element, str):
                raise TypeError(f"Элемент списка 'allowed_extensions' по индексу {number} должен быть строкой, "
                                f"получено {type(element).__name__}")

        valid_extensions = {
            '.txt', '.doc', '.docx', '.pdf',
            '.xls', '.xlsx', '.ppt', '.pptx'
        }

        if not self.allowed_extensions:
            raise DataFillError(
                model_name="ExpectedFile",
                field="allowed_extensions",
                value=self.allowed_extensions,
                reason=f"расширение не было передано для запроса {self.name}"
            )

        normalized_extensions: list[str] = []
        for extension in self.allowed_extensions:
            if not isinstance(extension, str):
                raise TypeError(f"Элемент списка 'allowed_extensions' должен быть строкой, получено {type(extension).__name__}")

            if not extension.startswith('.'):
                raise DataFillError(
                    model_name="ExpectedFile",
                    field="allowed_extensions",
                    value=extension,
                    reason=f"расширение должно начинаться с точки (.), получено: {extension}"
                )

            normalized_extension = extension.lower()
            if normalized_extension not in valid_extensions:
                raise DataFillError(
                    model_name="ExpectedFile",
                    field="allowed_extensions",
                    value=extension,
                    reason=f"неподдерживаемое расширение. Допустимые: {', '.join(sorted(valid_extensions))}"
                )

            if normalized_extension not in normalized_extensions:
                normalized_extensions.append(normalized_extension)

        self.allowed_extensions = normalized_extensions

    def _validate_required(self) -> None:
        """Проверка инварианта флага обязательности"""
        if not isinstance(self.required, bool):
            raise TypeError(f"Поле 'required' должно быть типа 'bool', получено {type(self.required).__name__}")

@dataclass
class ScannedFile:
    """Описывает файл, который был найден в целевом каталоге."""

    name: str
    extension: str
    size_bytes: int
    absolute_path: Path = field(default_factory=Path)
    relative_path: Path = field(default_factory=Path)

    def __post_init__(self):
        self._validate_name()
        self._validate_extension()
        self._validate_size_bytes()
        self._validate_absolute_path()
        self._validate_relative_path()

    def _validate_name(self) -> None:
        """Проверка инварианта имени"""
        if not isinstance(self.name, str):
            raise TypeError(f"Поле 'name' должно быть типа 'str', получено {type(self.name).__name__}")

        if len(self.name) < 1 or len(self.name) > 255:
            raise DataFillError(
                model_name="ScannedFile",
                field="name",
                value=self.name,
                reason="длина имени должна быть от 1 до 255 символов включительно"
            )

        forbidden_chars = set('\\/:*?"<>|')
        if any(char in forbidden_chars for char in self.name):
            raise DataFillError(
                model_name="ScannedFile",
                field="name",
                value=self.name,
                reason="имя содержит запрещенные символы из набора \\ / : * ? \" < > |"
            )

    def _validate_extension(self) -> None:
        """Проверка инварианта расширения"""
        if not isinstance(self.extension, str):
            raise TypeError(f"Поле 'extension' должно быть типа 'str', получен {type(self.extension).__name__}")

        if not self.extension:
            raise DataFillError(
                model_name="ScannedFile",
                field="extension",
                value=self.extension,
                reason="расширение не может быть пустым"
            )

        if not self.extension.startswith('.'):
            raise DataFillError(
                model_name="ScannedFile",
                field="extension",
                value=self.extension,
                reason="расширение должно начинаться с точки"
            )

        self.extension = self.extension.lower()

    def _validate_size_bytes(self) -> None:
        """Проверка инварианта размера файла"""
        if not isinstance(self.size_bytes, int):
            raise TypeError(f"Поле 'size_bytes' должно быть типа 'int', получено {type(self.size_bytes).__name__}")

        if self.size_bytes < 0:
            raise DataFillError(
                model_name="ScannedFile",
                field="size_bytes",
                value=self.size_bytes,
                reason="размер должен быть целым неотрицательным числом"
            )

    def _validate_absolute_path(self) -> None:
        """Проверка инварианта абсолютного пути"""
        if not isinstance(self.absolute_path, Path):
            raise TypeError(f"Поле 'absolute_path' должно быть типа 'Path', получено {type(self.absolute_path).__name__}")

    def _validate_relative_path(self) -> None:
        """Проверка инварианта относительного пути"""
        if not isinstance(self.relative_path, Path):
            raise TypeError(f"Поле 'relative_path' должно быть типа 'Path', получено {type(self.relative_path).__name__}")

@dataclass
class ValidationIssue:
    """Описывает одну обнаруженную проблему в процессе проверки файла."""

    issue_type: IssueType
    message: str
    severity: Severity
    file_name: str | None = None

    def __post_init__(self) -> None:
        """Вызов функции проверок инвариантов после инициализации"""
        self._validate_issue_type()
        self._validate_message()
        self._validate_file_name()
        self._validate_severity()

    def _validate_issue_type(self) -> None:
        """Проверка инварианта типа проблемы"""
        if not isinstance(self.issue_type, IssueType):
            raise TypeError(
                f"Поле 'issue_type' должно быть экземпляром IssueType, получено {type(self.issue_type).__name__}"
            )

    def _validate_message(self) -> None:
        """Проверка инварианта сообщения"""
        if not isinstance(self.message, str):
            raise TypeError(f"Поле 'message' должно быть типа 'str', получено {type(self.message).__name__}")

    def _validate_file_name(self) -> None:
        """Проверка инварианта имени файла"""
        if self.file_name is not None and not isinstance(self.file_name, str):
            raise TypeError(f"Поле 'file_name' должно быть типа 'str' или None, получено {type(self.file_name).__name__}")

    def _validate_severity(self) -> None:
        """Проверка инварианта важности проблемы"""
        if not isinstance(self.severity, Severity):
            raise TypeError(
                f"Поле 'severity' должно быть экземпляром Severity, получено {type(self.severity).__name__}"
            )

@dataclass
class ValidationResult:
    """Представляет итог результата проверки."""

    ALLOWED_STATUSES: ClassVar[tuple[ValidationStatus, ...]] = (
        ValidationStatus.OK,
        ValidationStatus.WARNING,
        ValidationStatus.ERROR,
    )

    status: ValidationStatus = ValidationStatus.OK
    found_files: list[ScannedFile] = field(default_factory=list)
    missing_files: list[ExpectedFile] = field(default_factory=list)
    wrong_extension_files: list[ScannedFile] = field(default_factory=list)
    empty_files: list[ScannedFile] = field(default_factory=list)
    extra_files: list[ScannedFile] = field(default_factory=list)
    issues: list[ValidationIssue] = field(default_factory=list)

    def __post_init__(self) -> None:
        """Вызывает функции проверки инвариантов полей"""
        self._validate_status()
        self._validate_found_files()
        self._validate_missing_files()
        self._validate_wrong_extension_files()
        self._validate_empty_files()
        self._validate_extra_files()
        self._validate_issues()
        self._refresh_status()

    def _validate_status(self) -> None:
        """Проверка инварианта статуса завершения работы программы"""
        if not isinstance(self.status, ValidationStatus):
            raise TypeError(
                f"Поле 'status' должно быть экземпляром ValidationStatus, получено {type(self.status).__name__}"
            )

    def _refresh_status(self) -> None:
        """Пересчитать итоговый статус по списку проблем."""
        if not self.issues:
            self.status = ValidationStatus.OK
            return

        if any(issue.severity == Severity.ERROR for issue in self.issues):
            self.status = ValidationStatus.ERROR
            return

        self.status = ValidationStatus.WARNING

    def _validate_found_files(self) -> None:
        """Проверка инварианта списка найденных файлов"""
        self._validate_list("found_files", self.found_files, ScannedFile)

    def _validate_missing_files(self) -> None:
        """Проверка инварианта списка потерянных файлов"""
        self._validate_list("missing_files", self.missing_files, ExpectedFile)

    def _validate_wrong_extension_files(self) -> None:
        """Проверка инварианта списка файлов с некорректным расширением"""
        self._validate_list("wrong_extension_files", self.wrong_extension_files, ScannedFile)

    def _validate_empty_files(self) -> None:
        """Проверка инварианта списка пустых файлов"""
        self._validate_list("empty_files", self.empty_files, ScannedFile)

    def _validate_extra_files(self) -> None:
        """Проверка инварианта списка лишних файлов"""
        self._validate_list("extra_files", self.extra_files, ScannedFile)

    def _validate_issues(self) -> None:
        """Проверка инварианта списка проблем"""
        self._validate_list("issues", self.issues, ValidationIssue)

    def _validate_list(self, field_name: str, values: list[object], expected_type: type) -> None:
        """Общая функция проверки инвариантов"""
        if not isinstance(values, list):
            raise TypeError(f"Поле '{field_name}' должно быть типа 'list', получено {type(values).__name__}")

        for index, value in enumerate(values):
            if not isinstance(value, expected_type):
                raise TypeError(
                    f"Элемент списка '{field_name}' по индексу {index} должен быть экземпляром "
                    f"{expected_type.__name__}, получено {type(value).__name__}"
                )
