from pathlib import Path

from doc_validator.models import ReportFormat, ValidationResult, ValidationSettings
from doc_validator.reports import ReportBuilder


class TestReports:
    def test_report_builder_saves_text_report(self, tmp_path):
        output_path = tmp_path / "report.txt"
        result = ValidationResult()
        settings = ValidationSettings(recursive=False, check_empty_files=False, detect_extra_files=False)

        builder = ReportBuilder(result, settings, output_path, ReportFormat.TXT)
        builder.save_report()

        assert output_path.exists()
        assert output_path.read_text(encoding="utf-8")
