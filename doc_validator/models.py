"""Модели данных приложения.

Модуль предназначен для формирования и описания структур моделей данных,
используемых в ходе работы приложения. Они определяют, какие поля есть у объекта,
какие типы данных в них хранятся, какие правила валидации к ним применяются, и как
эти данные взаимодействуют друг с другом.

Для описания моделей данных применялся подход с использованием встроенного модуля dataclass.
Такой способ позволяет сделать модели более удобными и понятными по сравнению с хранением
данных в словарях, и одновременно с этим проще, чем описание данных с использованием обычных
классов с ручным управлением состоянием из-за отсутствия необходимости вручную прописывать
базовые методы
"""

from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from enum import Enum
import re
from typing import ClassVar

from .exceptions import DataFillError


class IssueType(Enum):
    """
    Модель представляет собой перечисление типов проблем поиска.

    Используется при возникновении исключения в ходе работы программы, что позволяет
    более точно их классифицировать

    Attributes:
        MISSING_FILE: состояние при ненайденном требуемом файле.
        WRONG_EXTENSION: состояние при найденном требуемом файле с неверным расширением.
        EMPTY_FILE: состояние при найденном пустом файле.
        EXTRA_FILE: состояние при найденном файле, который не был запрошен.
        INVALID_REQUIREMENTS: состояние при некорректной структуре или содержимом файле требований.
        DIRECTORY_NOT_FOUND: состояние при несуществующем корневом каталоге.
        REPORT_WRITE_ERROR: состояние при ошибке записи отчета.
    """

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
            IssueType.REPORT_WRITE_ERROR: "ошибка при записи отчета"
        }
        return issued_description[self]


class Severity(Enum):
    """
    Модель представляет собой перечисление уровней важности проблемы.

    Используется для маркировки отдельной найденной проблемы и определения
    того, насколько серьезно она влияет на итоговый результат проверки.

    Attributes:
        INFO: информационное сообщение, не влияющее на успешность проверки.
        WARNING: предупреждение, не блокирующее завершение проверки.
        ERROR: критическая ошибка, приводящая к неуспешному результату.
    """

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
    """
    Модель представляет собой перечисление поддерживаемых форматов отчетов.

    Используется для выбора способа представления результатов проверки в
    выходном файле.

    Attributes:
        TXT: текстовый формат отчета.
        JSON: структурированный JSON-отчет.
        CSV: табличный CSV-отчет.
    """

    TXT = "txt"
    JSON = "json"
    CSV = "csv"
    PDF = "pdf"

    def __str__(self):
        return self.value


class ValidationStatus(Enum):
    """
    Модель представляет собой перечисление итоговых статусов проверки.

    Используется для описания общего результата выполнения процедуры валидации
    по завершении работы приложения.

    Attributes:
        OK: проверка успешно завершена без проблем.
        WARNING: проверка завершена, но были обнаружены предупреждения.
        ERROR: проверка завершена с ошибками.
    """

    OK = "OK"
    WARNING = "WARNING"
    ERROR = "ERROR"

    def __str__(self) -> str:
        return self.value


@dataclass
class ExpectedFile:
    """
    Модель описывает файл, который должен быть найден в целевом каталоге.

    Используется для задания требований к ожидаемым документам и определения
    допустимых расширений, а также обязательности их наличия.

    Attributes:
        name: имя файла или шаблон имени, который должен быть найден.
        allowed_extensions: список допустимых расширений файла.
        required: признак обязательности файла для успешной проверки.
    """
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
    """
    Модель описывает файл, который был найден в целевом каталоге.

    Используется для хранения информации о реально обнаруженном файле,
    включая его имя, расширение, размер и пути.

    Attributes:
        name: имя найденного файла.
        extension: расширение файла с точкой в начале.
        size_bytes: размер файла в байтах.
        absolute_path: абсолютный путь к файлу.
        relative_path: относительный путь к файлу относительно целевого каталога.
    """

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
            raise TypeError(
                f"Поле 'absolute_path' должно быть типа 'Path', получено {type(self.absolute_path).__name__}")

    def _validate_relative_path(self) -> None:
        """Проверка инварианта относительного пути"""
        if not isinstance(self.relative_path, Path):
            raise TypeError(
                f"Поле 'relative_path' должно быть типа 'Path', получено {type(self.relative_path).__name__}")


@dataclass
class ValidationIssue:
    """
    Модель описывает одну обнаруженную проблему в процессе проверки файла.

    Используется для представления отдельной ошибки, предупреждения или
    информационного сообщения, связанного с конкретным файлом или общей проверкой.

    Attributes:
        issue_type: тип проблемы из перечисления IssueType.
        message: текстовое описание проблемы.
        severity: уровень важности проблемы.
        file_name: имя файла, к которому относится проблема, если применимо.
    """

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
            raise TypeError(
                f"Поле 'file_name' должно быть типа 'str' или None, получено {type(self.file_name).__name__}")

    def _validate_severity(self) -> None:
        """Проверка инварианта важности проблемы"""
        if not isinstance(self.severity, Severity):
            raise TypeError(
                f"Поле 'severity' должно быть экземпляром Severity, получено {type(self.severity).__name__}"
            )


@dataclass
class ValidationResult:
    """
    Модель представляет итог результата проверки.

    Содержит информацию о найденных, отсутствующих и некорректных файлах,
    а также о возникших проблемах и общем статусе проверки.

    Attributes:
        status: итоговый статус выполнения проверки.
        found_files: список успешно обнаруженных файлов.
        missing_files: список ожидаемых, но отсутствующих файлов.
        wrong_extension_files: список файлов с неподходящим расширением.
        empty_files: список пустых файлов.
        extra_files: список лишних файлов.
        issues: список отдельных проблем, выявленных в ходе проверки.
    """

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


@dataclass
class ValidationSettings:
    """
    Модель описывает настройки поиска и проверки файлов.

    Используется для управления поведением программы при сканировании
    каталога и анализе найденных документов.

    Attributes:
        recursive: признак рекурсивного обхода каталогов.
        check_empty_files: признак необходимости проверки файлов на пустоту.
        detect_extra_files: признак необходимости выявления лишних файлов.
    """

    recursive: bool = False
    check_empty_files: bool = False
    detect_extra_files: bool = False

    def __post_init__(self) -> None:
        self._validate_recursive()
        self._validate_empty_files()
        self._validate_detect_extra_files()

    def _validate_recursive(self) -> None:
        if not isinstance(self.recursive, bool):
            raise TypeError(
                f"Поле 'recursive' должно быть типа 'bool', получено {type(self.recursive).__name__}"
            )

    def _validate_empty_files(self) -> None:
        if not isinstance(self.check_empty_files, bool):
            raise TypeError(
                f"Поле 'check_empty_files' должно быть типа 'bool', получено {type(self.check_empty_files).__name__}"
            )

    def _validate_detect_extra_files(self) -> None:
        if not isinstance(self.detect_extra_files, bool):
            raise TypeError(
                f"Поле 'detect_extra_files' должно быть типа 'bool', получено {type(self.detect_extra_files).__name__}"
            )


@dataclass
class Requirements:
    """
    Модель описывает набор требований к проверяемому каталогу.

    Содержит список ожидаемых файлов и настройки, определяющие правила
    проверки этих файлов.

    Attributes:
        required_files: список файлов, которые должны быть найдены.
        settings: настройки проверки, применяемые к данному набору требований.
    """

    required_files: list[ExpectedFile] = field(default_factory=list)
    settings: ValidationSettings = field(default_factory=ValidationSettings)
    def __post_init__(self) -> None:
        self._validate_required_files()
        self._validate_settings()

    def _validate_required_files(self) -> None:
        """Проверка инварианта списка ожидаемых файлов"""
        if not isinstance(self.required_files, list):
            raise TypeError(
                f"Поле 'required_files' должно быть типа 'list', получено {type(self.required_files).__name__}"
            )

        for index, item in enumerate(self.required_files):
            if not isinstance(item, ExpectedFile):
                raise TypeError(
                    f"Элемент списка 'required_files' по индексу {index} должен быть экземпляром ExpectedFile, "
                    f"получено {type(item).__name__}"
                )

    def _validate_settings(self) -> None:
        """Проверка инварианта настроек проверки"""
        if not isinstance(self.settings, ValidationSettings):
            raise TypeError(
                f"Поле 'settings' должно быть экземпляром ValidationSettings, получено {type(self.settings).__name__}"
            )
