from pathlib import Path

from doc_validator.requirements_loader import load_requirements
from doc_validator.exceptions import InputRequirementFileError


class TestRequirementsLoader:
    def test_load_requirements_reads_valid_json(self, tmp_path):
        requirements_file = tmp_path / "requirements.json"
        requirements_file.write_text(
            '{"required_files": [{"name": "report", "allowed_extensions": [".txt"], "required": true}], "settings": {"recursive": false, "check_empty_files": false, "detect_extra_files": false}}',
            encoding="utf-8",
        )

        requirements = load_requirements(requirements_file)

        assert requirements.required_files[0].name == "report"
        assert requirements.settings.recursive is False

    def test_load_requirements_raises_for_invalid_file(self, tmp_path):
        missing_file = tmp_path / "missing.json"

        try:
            load_requirements(missing_file)
        except InputRequirementFileError:
            assert True
        else:
            assert False, "Ожидалось исключение InputRequirementFileError"
