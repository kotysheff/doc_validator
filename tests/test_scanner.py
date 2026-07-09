from pathlib import Path

from doc_validator.scanner import scan_directory
from doc_validator.exceptions import ScanError


class TestScanner:
    def test_scan_directory_returns_files_in_directory(self, tmp_path):
        sample_file = tmp_path / "sample.txt"
        sample_file.write_text("hello", encoding="utf-8")

        scanned = scan_directory(tmp_path, recursive=False)

        assert len(scanned) == 1
        assert scanned[0].name == "sample"
        assert scanned[0].extension == ".txt"

    def test_scan_directory_raises_for_missing_directory(self, tmp_path):
        missing_dir = tmp_path / "missing"

        try:
            scan_directory(missing_dir, recursive=False)
        except ScanError:
            assert True
        else:
            assert False, "Ожидалось исключение ScanError"
