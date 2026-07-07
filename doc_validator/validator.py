"""Проверка и валидация результатов поиска.

Этот модуль является ключевым звеном приложения: он сравнивает список
ожидаемых файлов с фактически обнаруженными в указанном каталоге.
Результат проверки далее используется для формирования итогового отчета.
"""

from doc_validator.config_logger import logger
from doc_validator.models import (
    ExpectedFile,
    IssueType,
    ScannedFile,
    Severity,
    ValidationIssue,
    ValidationResult,
    ValidationSettings,
)


def validate_files(expected_files: list[ExpectedFile], actual_files: list[ScannedFile], settings: ValidationSettings) -> ValidationResult:
    logger.info("Запуск валидации: ожидаемых файлов=%d, фактически найденных=%d", len(expected_files), len(actual_files))
    """Сравнить ожидаемые файлы с фактически найденными файлами."""
    if not isinstance(expected_files, list):
        raise TypeError(f"expected_files должен быть типа 'list', получено: {type(expected_files).__name__}")

    if not isinstance(actual_files, list):
        raise TypeError(f"actual_files должен быть типа 'list', получено: {type(actual_files).__name__}")

    if not isinstance(settings, ValidationSettings):
        raise TypeError(f"settings должен быть типа 'ValidationSettings', получено: {type(settings).__name__}")

    if any(not isinstance(actual_file, ScannedFile) for actual_file in actual_files):
        raise TypeError("Список actual_files должен содержать только объекты типа 'ScannedFile'")

    if any(not isinstance(expected_file, ExpectedFile) for expected_file in expected_files):
        raise TypeError("Список expected_files должен содержать только объекты типа 'ExpectedFile'")

    found_files: list[ScannedFile] = []
    missing_files: list[ExpectedFile] = []
    wrong_extension_files: list[ScannedFile] = []
    empty_files: list[ScannedFile] = []
    extra_files: list[ScannedFile] = []
    issues: list[ValidationIssue] = []

    actual_files_by_name: dict[str, list[ScannedFile]] = {}

    for actual_file in actual_files:
        actual_files_by_name.setdefault(actual_file.name, []).append(actual_file)

    for expected_file in expected_files:
        related_files = actual_files_by_name.get(expected_file.name, [])

        if not related_files:
            if expected_file.required:
                missing_files.append(expected_file)
                issues.append(
                    ValidationIssue(
                        issue_type=IssueType.MISSING_FILE,
                        severity=Severity.ERROR,
                        message=f"Обязательный файл '{expected_file.name}' не найден",
                        file_name=expected_file.name,
                    )
                )
            continue

        matching_extension_files = [
            actual_file for actual_file in related_files
            if actual_file.extension in expected_file.allowed_extensions
        ]

        wrong_extension_matches = [
            actual_file for actual_file in related_files
            if actual_file.extension not in expected_file.allowed_extensions
        ]

        if matching_extension_files:
            found_files.extend(matching_extension_files)

            if wrong_extension_matches:
                wrong_extension_files.extend(wrong_extension_matches)
                for actual_file in wrong_extension_matches:
                    issues.append(
                        ValidationIssue(
                            issue_type=IssueType.WRONG_EXTENSION,
                            severity=Severity.WARNING,
                            message=(
                                f"Файл '{actual_file.relative_path}' имеет недопустимое расширение "
                                f"'{actual_file.extension}'"
                            ),
                            file_name=str(actual_file.relative_path),
                        )
                    )
        else:
            wrong_extension_files.extend(related_files)
            severity = Severity.ERROR if expected_file.required else Severity.WARNING

            for actual_file in related_files:
                issues.append(
                    ValidationIssue(
                        issue_type=IssueType.WRONG_EXTENSION,
                        severity=severity,
                        message=(
                            f"Файл '{actual_file.relative_path}' найден, но его расширение "
                            f"'{actual_file.extension}' не входит в список допустимых: "
                            f"{', '.join(expected_file.allowed_extensions)}"
                        ),
                        file_name=str(actual_file.relative_path),
                    )
                )

        if settings.check_empty_files:
            for actual_file in matching_extension_files:
                if actual_file.size_bytes == 0:
                    empty_files.append(actual_file)
                    issues.append(
                        ValidationIssue(
                            issue_type=IssueType.EMPTY_FILE,
                            severity=Severity.WARNING,
                            message=f"Файл '{actual_file.relative_path}' пуст",
                            file_name=str(actual_file.relative_path),
                        )
                    )

    if settings.detect_extra_files:
        expected_names = {expected_file.name for expected_file in expected_files}

        for actual_file in actual_files:
            if actual_file.name not in expected_names:
                extra_files.append(actual_file)
                issues.append(
                    ValidationIssue(
                        issue_type=IssueType.EXTRA_FILE,
                        severity=Severity.WARNING,
                        message=f"Обнаружен лишний файл '{actual_file.relative_path}'",
                        file_name=str(actual_file.relative_path),
                    )
                )

    result = ValidationResult(
        found_files=found_files,
        missing_files=missing_files,
        wrong_extension_files=wrong_extension_files,
        empty_files=empty_files,
        extra_files=extra_files,
        issues=issues,
    )
    logger.info(
        "Валидация завершена: найдено=%d, пропущено=%d, неверных расширений=%d, пустых=%d, лишних=%d, проблем=%d",
        len(found_files),
        len(missing_files),
        len(wrong_extension_files),
        len(empty_files),
        len(extra_files),
        len(issues),
    )
    return result
