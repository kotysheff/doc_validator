"""Формирование и запись отчетов.

Данный модуль отвечает за создание отчетов и их вывод в консоль либо
в указанный файл. Для предотвращения частичной записи данных и потери
информации используется подход атомарной записи.
"""

import csv
import json
import os
from pathlib import Path
from typing import Any

from doc_validator.models import ValidationResult, ValidationSettings, ReportFormat
from doc_validator.exceptions import ReportWriteError


class ReportBuilder(object):
    def __init__(self, result: ValidationResult, settings: ValidationSettings, output_path: Path, report_format: ReportFormat):
        self.result = result
        self.settings = settings
        self.output_path = Path(output_path)
        self.report_format = report_format

    def _validate_output_path(self) -> None:
        if self.output_path.exists() and self.output_path.is_dir():
            raise ReportWriteError(str(self.output_path), "указанный путь указывает на директорию")

        parent_dir = self.output_path.parent
        if not parent_dir.exists():
            raise ReportWriteError(str(self.output_path), "родительский каталог для отчета не существует")

        if not parent_dir.is_dir():
            raise ReportWriteError(str(self.output_path), "родительский путь не является директорией")

        if not os.access(parent_dir, os.W_OK):
            raise ReportWriteError(str(self.output_path), "нет прав на запись в каталог")

    def _build_txt_report(self) -> str:
        txt_report = "Отчет проверки каталога DocValidator\n\n"
        txt_report += f"Итоговый статус {self.result.status}\n\n"
        txt_report += "Статистика: \n"
        txt_report += f"Найдено корректных файлов: {len(self.result.found_files)}\n"
        txt_report += f"Отсутствуют обязательных файлов: {len(self.result.missing_files)}\n"
        txt_report += f"Файлов с неверным расширением: {len(self.result.wrong_extension_files)}\n"

        if self.settings.check_empty_files:
            txt_report += f"Пустых файлов: {len(self.result.empty_files)}\n"

        if self.settings.detect_extra_files:
            txt_report += f"Лишних файлов: {len(self.result.extra_files)}\n"
        txt_report += f"Проблем возникло при поиске: {len(self.result.issues)}\n\n"

        txt_report += "Найденные файлы: \n"
        if not self.result.found_files:
            txt_report += "Нет\n"
        else:
            for number, file in enumerate(self.result.found_files, start=1):
                txt_report += f"{number}. {file.name}{file.extension}\n"
        txt_report += "\n"

        txt_report += "Отсутствующие файлы: \n"
        if not self.result.missing_files:
            txt_report += "Нет\n"
        else:
            for number, file in enumerate(self.result.missing_files, start=1):
                txt_report += f"{number}. {file.name}\n"
        txt_report += "\n"

        txt_report += "Файлы с неверным расширением: \n"
        if not self.result.wrong_extension_files:
            txt_report += "Нет\n"
        else:
            for number, file in enumerate(self.result.wrong_extension_files, start=1):
                txt_report += f"{number}. {file.name}{file.extension}\n"
        txt_report += "\n"

        if self.settings.check_empty_files:
            txt_report += "Пустые файлы: \n"
            if not self.result.empty_files:
                txt_report += "Нет\n"
            else:
                for number, file in enumerate(self.result.empty_files, start=1):
                    txt_report += f"{number}. {file.name}{file.extension}\n"
                txt_report += "\n"

        if self.settings.detect_extra_files:
            txt_report += "Лишние файлы: \n"
            if not self.result.extra_files:
                txt_report += "Нет\n"
            else:
                for number, file in enumerate(self.result.extra_files, start=1):
                    txt_report += f"{number}. {file.name}{file.extension}\n"
                txt_report += "\n"

        txt_report += "Проблемы: \n"
        if not self.result.issues:
            txt_report += "Нет\n"
        else:
            for number, issue in enumerate(self.result.issues, start=1):
                txt_report += f"{number}. [{issue.issue_type}] {issue.file_name} - {issue.message}\n"
        return txt_report

    def _save_txt_report(self, report: str) -> None:
        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                f.write(report)
        except OSError as exc:
            raise ReportWriteError(str(self.output_path), f"ошибка записи файла: {exc}") from exc

    def _serialize_found_files(self) -> list[dict[str, Any]]:
        found_files = []
        for file in self.result.found_files:
            file_dict = {
                "name": file.name,
                "extension": file.extension,
                "relative_path": str(file.relative_path),
                "size_bytes": file.size_bytes,
            }
            found_files.append(file_dict)
        return found_files

    def _serialize_missing_files(self) -> list[dict[str, Any]]:
        missing_files = []
        for file in self.result.missing_files:
            file_dict = {
                "name": file.name,
                "allowed_extensions": file.allowed_extensions,
                "required": file.required,
            }
            missing_files.append(file_dict)
        return missing_files

    def _serialize_wrong_extension_files(self) -> list[dict[str, Any]]:
        wrong_extension_files = []
        for file in self.result.wrong_extension_files:
            file_dict = {
                "name": file.name,
                "extension": file.extension,
                "relative_path": str(file.relative_path),
                "size_bytes": file.size_bytes,
            }
            wrong_extension_files.append(file_dict)
        return wrong_extension_files

    def _serialize_empty_files(self) -> list[dict[str, Any]]:
        empty_files = []
        for file in self.result.empty_files:
            file_dict = {
                "name": file.name,
                "extension": file.extension,
                "relative_path": str(file.relative_path),
                "size_bytes": file.size_bytes,
            }
            empty_files.append(file_dict)
        return empty_files

    def _serialize_extra_files(self) -> list[dict[str, Any]]:
        extra_files = []
        for file in self.result.extra_files:
            file_dict = {
                "name": file.name,
                "extension": file.extension,
                "relative_path": str(file.relative_path),
                "size_bytes": file.size_bytes,
            }
            extra_files.append(file_dict)
        return extra_files

    def _serialize_issues(self) -> list[dict[str, Any]]:
        issues = []
        for issue in self.result.issues:
            issue_dict = {
                "type": issue.issue_type.value,
                "severity": issue.severity.value,
                "file_name": issue.file_name,
                "message": issue.message,
            }
            issues.append(issue_dict)
        return issues

    def _build_json_report(self) -> dict[str, Any]:
        json_report = {
            "status": self.result.status.value,
            "summary": {
                "found_files": len(self.result.found_files),
                "missing_files": len(self.result.missing_files),
                "wrong_extension_files": len(self.result.wrong_extension_files),
                "empty_files": len(self.result.empty_files),
                "extra_files": len(self.result.extra_files),
                "issues": len(self.result.issues),
            },
            "found_files": self._serialize_found_files(),
            "missing_files": self._serialize_missing_files(),
            "wrong_extension_files": self._serialize_wrong_extension_files(),
            "empty_files": self._serialize_empty_files(),
            "extra_files": self._serialize_extra_files(),
            "issues": self._serialize_issues(),
        }
        return json_report

    def _save_json_report(self, report: dict[str, Any]) -> None:
        try:
            with open(self.output_path, "w", encoding="utf-8") as f:
                json.dump(report, f, ensure_ascii=False, indent=2)
        except OSError as exc:
            raise ReportWriteError(str(self.output_path), f"ошибка записи файла: {exc}") from exc

    def _build_csv_report(self) -> list[dict[str, Any]]:
        issues_data = []

        if not self.result.issues:
            issues_data.append(
                {
                    "type": "info",
                    "severity": "no_issues",
                    "file_name": "",
                    "message": "Проблем не обнаружено",
                }
            )
        else:
            for issue in self.result.issues:
                issues_data.append(
                    {
                        "type": issue.issue_type.value,
                        "severity": issue.severity.value,
                        "file_name": issue.file_name,
                        "message": issue.message,
                    }
                )
        return issues_data

    def _save_csv_report(self, report: list[dict[str, Any]]) -> None:
        fieldnames = ["type", "severity", "file_name", "message"]

        try:
            with open(self.output_path, "w", encoding="utf-8", newline="") as f:
                writer = csv.DictWriter(f, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(report)
        except OSError as exc:
            raise ReportWriteError(str(self.output_path), f"ошибка записи файла: {exc}") from exc

    def save_report(self) -> None:
        supported_formats = {member for member in ReportFormat}
        if self.report_format not in supported_formats:
            raise ReportWriteError(str(self.output_path), "передан неподдерживаемый формат отчета")

        self._validate_output_path()

        if self.report_format == ReportFormat.TXT:
            report = self._build_txt_report()
            self._save_txt_report(report)
        elif self.report_format == ReportFormat.JSON:
            report = self._build_json_report()
            self._save_json_report(report)
        elif self.report_format == ReportFormat.CSV:
            report = self._build_csv_report()
            self._save_csv_report(report)
        else:
            raise ReportWriteError(str(self.output_path), "передан неподдерживаемый формат отчета")
