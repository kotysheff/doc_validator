from pathlib import Path

from doc_validator.models import (
    ExpectedFile,
    IssueType,
    ScannedFile,
    Severity,
    ValidationSettings,
)
from doc_validator.validator import validate_files


class TestValidator:
    def test_validate_files_returns_ok_for_matching_file(self):
        expected = ExpectedFile(name="contact", allowed_extensions=[".pdf"], required=True)
        actual = [
            ScannedFile(
                name="contact",
                extension=".pdf",
                size_bytes=10,
                absolute_path=Path("/tmp/contact.pdf"),
                relative_path=Path("contact.pdf"),
            )
        ]
        settings = ValidationSettings(recursive=False, check_empty_files=False, detect_extra_files=False)

        result = validate_files([expected], actual, settings)

        assert result.status.value == "OK"
        assert len(result.found_files) == 1
        assert result.issues == []

    def test_validate_files_reports_missing_required_file(self):
        expected = ExpectedFile(name="contact", allowed_extensions=[".pdf"], required=True)
        settings = ValidationSettings(recursive=False, check_empty_files=False, detect_extra_files=False)

        result = validate_files([expected], [], settings)

        assert result.status.value == "ERROR"
        assert len(result.missing_files) == 1
        assert result.issues[0].issue_type == IssueType.MISSING_FILE
        assert result.issues[0].severity == Severity.ERROR

    def test_validate_files_detects_empty_and_extra_files_when_enabled(self):
        expected = ExpectedFile(name="report", allowed_extensions=[".txt"], required=True)
        actual = [
            ScannedFile(
                name="report",
                extension=".txt",
                size_bytes=0,
                absolute_path=Path("/tmp/report.txt"),
                relative_path=Path("report.txt"),
            ),
            ScannedFile(
                name="extra",
                extension=".txt",
                size_bytes=5,
                absolute_path=Path("/tmp/extra.txt"),
                relative_path=Path("extra.txt"),
            ),
        ]
        settings = ValidationSettings(recursive=False, check_empty_files=True, detect_extra_files=True)

        result = validate_files([expected], actual, settings)

        assert len(result.empty_files) == 1
        assert len(result.extra_files) == 1
        assert any(issue.issue_type == IssueType.EMPTY_FILE for issue in result.issues)
        assert any(issue.issue_type == IssueType.EXTRA_FILE for issue in result.issues)
