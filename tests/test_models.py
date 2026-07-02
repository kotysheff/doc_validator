import pytest
from pathlib import Path

from doc_validator.models import *
from doc_validator.exceptions import DataFillError

@pytest.fixture
def expected_file_factory():
    def _create_expected_file(name="testName", allowed_extensions=[".txt", ".docx"], required=True):
        file = ExpectedFile(
            name=name,
            allowed_extensions=allowed_extensions,
            required=required,
        )
        return file
    return _create_expected_file

@pytest.fixture
def scanned_file_factory():
    def _create_scanned_file(name="testName", extension=".txt", size_bytes=400, absolute_path=None,
                             relative_path=None):

        if absolute_path is None:
            absolute_path = Path(__file__).resolve()
        if relative_path is None:
            relative_path = Path("some/relative/path/to/file.txt")

        file = ScannedFile(
            name=name,
            extension=extension,
            size_bytes=size_bytes,
            absolute_path=absolute_path,
            relative_path=relative_path,
        )

        return file
    return _create_scanned_file

@pytest.fixture
def validation_issue_factory():
    def _create_validation_issue(issue_type=IssueType.MISSING_FILE, message="File 123.txt missed",
                                 severity=Severity.WARNING, file_name="123.txt"):

        issue = ValidationIssue(
            issue_type=issue_type,
            message=message,
            severity=severity,
            file_name=file_name
        )
        return issue
    return _create_validation_issue


@pytest.fixture
def validation_result_factory(found_files=None, missing_files=None, wrong_extension_files=None,
                                  empty_files=None, extra_files=None, issues=None, status=ValidationStatus.OK):
    def _create_validation_result(
            found_files=found_files,
            missing_files=missing_files,
            wrong_extension_files=wrong_extension_files,
            empty_files=empty_files,
            extra_files=extra_files,
            issues=issues,
            status=status,
    ):
        if found_files is None:
            found_files = []
        if missing_files is None:
            missing_files = []
        if wrong_extension_files is None:
            wrong_extension_files = []
        if empty_files is None:
            empty_files = []
        if extra_files is None:
            extra_files = []
        if issues is None:
            issues = []

        result = ValidationResult(
            status=status,
            found_files=found_files,
            missing_files=missing_files,
            wrong_extension_files=wrong_extension_files,
            empty_files=empty_files,
            extra_files=extra_files,
            issues=issues,
        )
        return result
    return _create_validation_result


class TestIssueType:
    """Тестирование модели перечисления типов проблем"""

    def test_str_returns_value(self):
        assert str(IssueType.MISSING_FILE) == "missing_file"

    def test_description_exists(self):
        for member in IssueType:
            assert member.description
            assert isinstance(member.description, str)
            assert len(member.description) > 0

    def test_description_returns_value(self):
        assert IssueType.MISSING_FILE.description == "обязательный файл отсутствует"

    def test_from_value_existing(self):
        issue = IssueType("missing_file")
        assert issue == IssueType.MISSING_FILE

    def test_from_value_non_exists(self):
        with pytest.raises(ValueError) as exc_info:
            IssueType("test")

        assert exc_info.type is ValueError


class TestSeverity:
    """Тестирование модели уровней важности отдельных проблем"""

    def test_str_returns_value(self):
        assert str(Severity.INFO) == "info"

    def test_description_exists(self):
        for member in Severity:
            assert member.description
            assert isinstance(member.description, str)
            assert len(member.description) > 0

    def test_description_returns_value(self):
        assert Severity.INFO.description == "информационное сообщение"

    def test_from_value_existing(self):
        severity = Severity("info")
        assert severity == Severity.INFO

    def test_from_value_non_exists(self):
        with pytest.raises(ValueError) as exc_info:
            Severity("test")
        assert exc_info.type is ValueError


class TestReportFormat:
    """Тестирование модели перечисления поддерживаемых форматов отчета"""

    def test_str_returns_value(self):
        assert str(ReportFormat.TXT) == "txt"

    def test_from_value_existing(self):
        format = ReportFormat.TXT
        assert format == ReportFormat.TXT

    def test_from_value_non_exists(self):
        with pytest.raises(ValueError) as exc_info:
            ReportFormat("test")
        assert exc_info.type is ValueError


class TestValidationStatus:
    """Тестирование модели перечисления итоговых статусов проверки в целом"""

    def test_str_returns_value(self):
        assert str(ValidationStatus.OK) == "OK"
        assert str(ValidationStatus.WARNING) == "WARNING"
        assert str(ValidationStatus.ERROR) == "ERROR"

    def test_from_value_existing(self):
        validation_status = ValidationStatus("OK")
        assert validation_status == ValidationStatus.OK

    def test_from_value_non_exists(self):
        with pytest.raises(ValueError) as exc_info:
            ValidationStatus("test")
        assert exc_info.type is ValueError

class TestExpectedFile:
    """Тестирование модели файла, который должен быть найден в целевом каталоге"""
    """Поозитивные проверки"""
    def test_create_expected_file_correctly(self, expected_file_factory):
        file = expected_file_factory()
        assert isinstance(file, ExpectedFile)
        assert file.name == "testName"
        assert isinstance(file.allowed_extensions, list)
        assert file.allowed_extensions == [".txt", ".docx"]
        assert file.required is True

    def test_create_expected_file_one_character_name(self, expected_file_factory):
        file = expected_file_factory(
            name="a"
        )
        assert isinstance(file, ExpectedFile)
        assert file.name == "a"

    def test_create_expected_file_longest_name(self, expected_file_factory):
        file = expected_file_factory(
            name="a" * 255
        )
        assert isinstance(file, ExpectedFile)
        assert file.name == "a" * 255

    def test_create_expected_file_check_normalize_extensions(self, expected_file_factory):
        file = expected_file_factory(
            allowed_extensions=[".TXT", ".dOcX"]
        )
        assert isinstance(file, ExpectedFile)
        assert isinstance(file.allowed_extensions, list)
        assert file.allowed_extensions == [".txt", ".docx"]

    def test_create_expected_file_delete_duplicates(self, expected_file_factory):
        file = expected_file_factory(
            allowed_extensions=[".txt", ".docx", ".dOcX", ".TXT"]
        )
        assert isinstance(file, ExpectedFile)
        assert isinstance(file.allowed_extensions, list)
        assert file.allowed_extensions == [".txt", ".docx"]

    def test_create_expected_file_required_default_true(self, expected_file_factory):
        file = expected_file_factory(
            name="testName",
            allowed_extensions=[".txt", ".docx"]
        )
        assert isinstance(file, ExpectedFile)
        assert file.required is True

    """Негативные проверки"""
    def test_create_expected_file_name_not_str(self, expected_file_factory):
        with pytest.raises(TypeError) as exc_info:
            expected_file_factory(
                name=None
            )
        assert exc_info.type is TypeError
        assert "Поле 'name' должно быть типа 'str'" in str(exc_info.value)

    def test_create_expected_file_empty_name(self, expected_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            expected_file_factory(
                name=""
            )
        assert exc_info.type is DataFillError
        assert "длина имени должна быть от 1" in str(exc_info.value)

    def test_create_expected_file_name_longer_needed(self, expected_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            expected_file_factory(
                name="a" * 256
            )
        assert exc_info.type is DataFillError
        assert "длина имени должна быть от 1" in str(exc_info.value)

    def test_create_expected_file_invalid_characters_in_name(self, expected_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            expected_file_factory(
                name="hello?world"
            )
        assert exc_info.type is DataFillError
        assert "имя содержит запрещенные символы" in str(exc_info.value)

    def test_create_expected_file_non_list_allowed_extensions(self, expected_file_factory):
        with pytest.raises(TypeError) as exc_info:
            expected_file_factory(
                allowed_extensions=None
            )
        assert exc_info.type is TypeError
        assert "Поле 'allowed_extensions' должно быть типа 'list'" in str(exc_info.value)

    def test_create_expected_file_non_string_in_allowed_extensions(self, expected_file_factory):
        with pytest.raises(TypeError) as exc_info:
            expected_file_factory(
                allowed_extensions=[".txt", ".docx", None]
            )

        assert exc_info.type is TypeError
        assert "Элемент списка 'allowed_extensions' по индексу" in str(exc_info.value)

    def test_create_expected_file_empty_extension_not_startswith_with_dot(self, expected_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            expected_file_factory(
                allowed_extensions=["txt", "docx"]
            )
        assert exc_info.type is DataFillError
        assert "расширение должно начинаться с точки (.)" in str(exc_info.value)

    def test_create_expected_file_non_valid_extension(self, expected_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            expected_file_factory(
                allowed_extensions=[".mp4"]
            )
        assert exc_info.type is DataFillError
        assert "неподдерживаемое расширение. Допустимые:" in str(exc_info.value)

    def test_create_expected_file_non_bool_required_false(self, expected_file_factory):
        with pytest.raises(TypeError) as exc_info:
            expected_file_factory(
                required=None
            )
        assert exc_info.type is TypeError
        assert "Поле 'required' должно быть типа 'bool', получено" in str(exc_info.value)

class TestScannedFile:
    """Тестирование модели файла, который был найден в целевом каталоге"""
    """Позитивные проверки"""
    def test_create_scanned_file_correctly(self, scanned_file_factory):
        scanned_file = scanned_file_factory()
        assert isinstance(scanned_file, ScannedFile)
        assert scanned_file.name == "testName"
        assert scanned_file.extension == ".txt"
        assert scanned_file.size_bytes == 400
        assert scanned_file.absolute_path == Path(__file__).resolve()
        assert scanned_file.relative_path == Path("some/relative/path/to/file.txt")

    def test_create_scanned_file_one_character_name(self, scanned_file_factory):
        file = scanned_file_factory(
            name="a"
        )
        assert isinstance(file, ScannedFile)
        assert file.name == "a"

    def test_create_scanned_file_longest_name(self, scanned_file_factory):
        file = scanned_file_factory(
            name="a" * 255
        )
        assert isinstance(file, ScannedFile)
        assert file.name == "a" * 255

    def test_create_scanned_file_normalize_extension(self, scanned_file_factory):
        scanned_file = scanned_file_factory(
            extension=".TXT"
        )
        assert isinstance(scanned_file, ScannedFile)
        assert scanned_file.extension == ".txt"

    def test_create_scanned_file_zero_size_bytes(self, scanned_file_factory):
        scanned_file = scanned_file_factory(
            size_bytes=0
        )
        assert isinstance(scanned_file, ScannedFile)
        assert scanned_file.size_bytes == 0

    """Негативные проверки"""
    def test_create_scanned_file_name_not_str(self, scanned_file_factory):
        with pytest.raises(TypeError) as exc_info:
            scanned_file_factory(
                name=None
            )
        assert exc_info.type is TypeError
        assert "Поле 'name' должно быть типа 'str'" in str(exc_info.value)

    def test_create_scanned_file_empty_name(self, scanned_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            scanned_file_factory(
                name=""
            )
        assert exc_info.type is DataFillError
        assert "длина имени должна быть от 1" in str(exc_info.value)

    def test_create_scanned_file_name_longer_needed(self, scanned_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            scanned_file_factory(
                name="a" * 256
            )
        assert exc_info.type is DataFillError
        assert "длина имени должна быть от 1" in str(exc_info.value)

    def test_create_scanned_file_not_valid_characters_in_name(self, scanned_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            scanned_file_factory(
                name="hello?world"
            )
        assert exc_info.type is DataFillError
        assert "имя содержит запрещенные символы из набора" in str(exc_info.value)

    def test_create_scanned_file_extension_not_str(self, scanned_file_factory):
        with pytest.raises(TypeError) as exc_info:
            scanned_file_factory(
                extension=None
            )
        assert exc_info.type is TypeError
        assert "Поле 'extension' должно быть типа 'str'" in str(exc_info.value)

    def test_create_scanned_file_extension_empty_extension(self, scanned_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            scanned_file_factory(
                extension=""
            )
        assert exc_info.type is DataFillError
        assert "расширение не может быть пустым" in str(exc_info.value)

    def test_create_scanned_file_extension_not_startswith_dot(self, scanned_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            scanned_file_factory(
                extension="txt"
            )
        assert exc_info.type is DataFillError
        assert "расширение должно начинаться с точки" in str(exc_info.value)

    def test_create_scanned_file_size_bytes_not_int(self, scanned_file_factory):
        with pytest.raises(TypeError) as exc_info:
            scanned_file_factory(
                size_bytes=None
            )
        assert exc_info.type is TypeError
        assert "Поле 'size_bytes' должно быть типа 'int'" in str(exc_info.value)

    def test_create_scanned_file_negative_size_bytes(self, scanned_file_factory):
        with pytest.raises(DataFillError) as exc_info:
            scanned_file_factory(
                size_bytes=-1
            )
        assert exc_info.type is DataFillError
        assert "размер должен быть целым неотрицательным числом" in str(exc_info.value)

    def test_create_scanned_file_non_path_absolute_path(self, scanned_file_factory):
        with pytest.raises(TypeError) as exc_info:
            scanned_file_factory(
                absolute_path="str"
            )
        assert exc_info.type is TypeError
        assert "Поле 'absolute_path' должно быть типа 'Path'" in str(exc_info.value)

    def test_create_scanned_file_non_path_relative_path(self, scanned_file_factory):
        with pytest.raises(TypeError) as exc_info:
            scanned_file_factory(
                relative_path="str"
            )
        assert exc_info.type is TypeError
        assert "Поле 'relative_path' должно быть типа 'Path'" in str(exc_info.value)

class TestValidationIssue:
    """Тестирование модели одной обнаруженной проблемы"""

    def test_create_validation_issue_correctly(self, validation_issue_factory):
        issue = validation_issue_factory()

        assert isinstance(issue, ValidationIssue)
        assert issue.issue_type == IssueType.MISSING_FILE
        assert issue.message == "File 123.txt missed"
        assert issue.severity == Severity.WARNING
        assert issue.file_name == "123.txt"

    def test_create_validation_issue_with_none_file_name(self, validation_issue_factory):
        issue = validation_issue_factory(file_name=None)

        assert isinstance(issue, ValidationIssue)
        assert issue.file_name is None

    def test_create_validation_issue_with_error_severity(self, validation_issue_factory):
        issue = validation_issue_factory(severity=Severity.ERROR)

        assert isinstance(issue, ValidationIssue)
        assert issue.severity == Severity.ERROR

    def test_create_validation_issue_issue_type_not_enum(self, validation_issue_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_issue_factory(issue_type="missing_file")

        assert exc_info.type is TypeError
        assert "Поле 'issue_type' должно быть экземпляром IssueType" in str(exc_info.value)

    def test_create_validation_issue_message_not_str(self, validation_issue_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_issue_factory(message=None)

        assert exc_info.type is TypeError
        assert "Поле 'message' должно быть типа 'str'" in str(exc_info.value)

    def test_create_validation_issue_file_name_not_str(self, validation_issue_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_issue_factory(file_name=123)

        assert exc_info.type is TypeError
        assert "Поле 'file_name' должно быть типа 'str' или None" in str(exc_info.value)

    def test_create_validation_issue_severity_not_enum(self, validation_issue_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_issue_factory(severity="warning")

        assert exc_info.type is TypeError
        assert "Поле 'severity' должно быть экземпляром Severity" in str(exc_info.value)


class TestValidationResult:
    """Тестирование модели итогового результата проверки"""

    def test_create_validation_result_default(self, validation_result_factory):
        result = validation_result_factory()

        assert isinstance(result, ValidationResult)
        assert result.status == ValidationStatus.OK
        assert result.found_files == []
        assert result.missing_files == []
        assert result.wrong_extension_files == []
        assert result.empty_files == []
        assert result.extra_files == []
        assert result.issues == []

    def test_create_validation_result_with_collections(self, validation_result_factory, scanned_file_factory,
                                                     expected_file_factory, validation_issue_factory):
        found_file = scanned_file_factory(name="file1", extension=".pdf", size_bytes=100)
        missing_file = expected_file_factory(name="missing", allowed_extensions=[".txt"])
        wrong_extension_file = scanned_file_factory(name="file2", extension=".TXT", size_bytes=200)
        empty_file = scanned_file_factory(name="file3", extension=".docx", size_bytes=0)
        extra_file = scanned_file_factory(name="file4", extension=".ppt", size_bytes=10)
        issue = validation_issue_factory(issue_type=IssueType.EXTRA_FILE, severity=Severity.INFO,
                                         message="Extra file found", file_name="file4")

        result = validation_result_factory(
            found_files=[found_file],
            missing_files=[missing_file],
            wrong_extension_files=[wrong_extension_file],
            empty_files=[empty_file],
            extra_files=[extra_file],
            issues=[issue],
            status=ValidationStatus.WARNING,
        )

        assert isinstance(result, ValidationResult)
        assert result.found_files == [found_file]
        assert result.missing_files == [missing_file]
        assert result.wrong_extension_files == [wrong_extension_file]
        assert result.empty_files == [empty_file]
        assert result.extra_files == [extra_file]
        assert result.issues == [issue]
        assert result.status == ValidationStatus.WARNING

    def test_refresh_status_sets_ok_when_no_issues(self, validation_result_factory):
        result = validation_result_factory(status=ValidationStatus.ERROR)

        assert result.status == ValidationStatus.OK

    def test_refresh_status_sets_error_when_issue_has_error(self, validation_result_factory,
                                                            validation_issue_factory):
        issue = validation_issue_factory(severity=Severity.ERROR)
        result = validation_result_factory(issues=[issue], status=ValidationStatus.OK)

        assert result.status == ValidationStatus.ERROR

    def test_refresh_status_sets_warning_when_issue_has_warning_only(self, validation_result_factory,
                                                                      validation_issue_factory):
        issue = validation_issue_factory(severity=Severity.WARNING)
        result = validation_result_factory(issues=[issue], status=ValidationStatus.OK)

        assert result.status == ValidationStatus.WARNING

    def test_validation_result_status_not_enum(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(status="OK")

        assert exc_info.type is TypeError
        assert "Поле 'status' должно быть экземпляром ValidationStatus" in str(exc_info.value)

    def test_validation_result_found_files_not_list(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(found_files="not-a-list")

        assert exc_info.type is TypeError
        assert "Поле 'found_files' должно быть типа 'list'" in str(exc_info.value)

    def test_validation_result_missing_files_not_list(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(missing_files="not-a-list")

        assert exc_info.type is TypeError
        assert "Поле 'missing_files' должно быть типа 'list'" in str(exc_info.value)

    def test_validation_result_wrong_extension_files_not_list(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(wrong_extension_files="not-a-list")

        assert exc_info.type is TypeError
        assert "Поле 'wrong_extension_files' должно быть типа 'list'" in str(exc_info.value)

    def test_validation_result_empty_files_not_list(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(empty_files="not-a-list")

        assert exc_info.type is TypeError
        assert "Поле 'empty_files' должно быть типа 'list'" in str(exc_info.value)

    def test_validation_result_extra_files_not_list(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(extra_files="not-a-list")

        assert exc_info.type is TypeError
        assert "Поле 'extra_files' должно быть типа 'list'" in str(exc_info.value)

    def test_validation_result_issues_not_list(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(issues="not-a-list")

        assert exc_info.type is TypeError
        assert "Поле 'issues' должно быть типа 'list'" in str(exc_info.value)

    def test_validation_result_found_file_item_wrong_type(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(found_files=["not-a-scanned-file"])

        assert exc_info.type is TypeError
        assert "Элемент списка 'found_files' по индексу 0 должен быть экземпляром ScannedFile" in str(exc_info.value)

    def test_validation_result_missing_file_item_wrong_type(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(missing_files=["not-an-expected-file"])

        assert exc_info.type is TypeError
        assert "Элемент списка 'missing_files' по индексу 0 должен быть экземпляром ExpectedFile" in str(exc_info.value)

    def test_validation_result_wrong_extension_file_item_wrong_type(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(wrong_extension_files=["not-a-scanned-file"])

        assert exc_info.type is TypeError
        assert "Элемент списка 'wrong_extension_files' по индексу 0 должен быть экземпляром ScannedFile" in str(exc_info.value)

    def test_validation_result_empty_file_item_wrong_type(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(empty_files=["not-a-scanned-file"])

        assert exc_info.type is TypeError
        assert "Элемент списка 'empty_files' по индексу 0 должен быть экземпляром ScannedFile" in str(exc_info.value)

    def test_validation_result_extra_file_item_wrong_type(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(extra_files=["not-a-scanned-file"])

        assert exc_info.type is TypeError
        assert "Элемент списка 'extra_files' по индексу 0 должен быть экземпляром ScannedFile" in str(exc_info.value)

    def test_validation_result_issue_item_wrong_type(self, validation_result_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_result_factory(issues=["not-a-validation-issue"])

        assert exc_info.type is TypeError
        assert "Элемент списка 'issues' по индексу 0 должен быть экземпляром ValidationIssue" in str(exc_info.value)


@pytest.fixture
def validation_settings_factory(recursive=False, check_empty_files=False, detect_extra_files=False):
    def _create_validation_settings(
            recursive=recursive,
            check_empty_files=check_empty_files,
            detect_extra_files=detect_extra_files,
    ):
        return ValidationSettings(
            recursive=recursive,
            check_empty_files=check_empty_files,
            detect_extra_files=detect_extra_files,
        )
    return _create_validation_settings


class TestValidationSettings:
    """Тестирование модели настроек поиска файлов"""

    def test_create_validation_settings_default(self, validation_settings_factory):
        settings = validation_settings_factory()

        assert isinstance(settings, ValidationSettings)
        assert settings.recursive is False
        assert settings.check_empty_files is False
        assert settings.detect_extra_files is False

    def test_create_validation_settings_all_true(self, validation_settings_factory):
        settings = validation_settings_factory(
            recursive=True,
            check_empty_files=True,
            detect_extra_files=True,
        )

        assert isinstance(settings, ValidationSettings)
        assert settings.recursive is True
        assert settings.check_empty_files is True
        assert settings.detect_extra_files is True

    def test_create_validation_settings_recursive_not_bool(self, validation_settings_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_settings_factory(recursive="yes")

        assert exc_info.type is TypeError
        assert "Поле 'recursive' должно быть типа 'bool'" in str(exc_info.value)

    def test_create_validation_settings_check_empty_files_not_bool(self, validation_settings_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_settings_factory(check_empty_files=None)

        assert exc_info.type is TypeError
        assert "Поле 'check_empty_files' должно быть типа 'bool'" in str(exc_info.value)

    def test_create_validation_settings_detect_extra_files_not_bool(self, validation_settings_factory):
        with pytest.raises(TypeError) as exc_info:
            validation_settings_factory(detect_extra_files=0)

        assert exc_info.type is TypeError
        assert "Поле 'detect_extra_files' должно быть типа 'bool'" in str(exc_info.value)
    