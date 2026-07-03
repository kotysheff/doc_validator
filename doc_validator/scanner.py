"""Сканирование каталога.

Модуль отвечает за обход указанного каталога и преобразование найденных
файлов во внутренние объекты ScannedFile.
"""

import os
from pathlib import Path

from doc_validator.exceptions import ScanError
from doc_validator.models import ScannedFile


def scan_directory(target_dir: str | Path, recursive: bool = False) -> list[ScannedFile]:
    target_dir = Path(target_dir)

    if not target_dir.exists():
        raise ScanError(str(target_dir),
                        "Указанная директория не существует")
    if not target_dir.is_dir():
        raise ScanError(str(target_dir),
                        "Указанный путь не является директорией")
    if not os.access(target_dir, os.R_OK):
        raise ScanError(str(target_dir),
                        "Нет прав на чтение директории")

    base_path = target_dir.resolve()
    paths = base_path.rglob("*") if recursive else base_path.iterdir()

    scanned_files: list[ScannedFile] = []
    for file_path in paths:
        if not file_path.is_file():
            continue

        if not file_path.suffix:
            continue

        scanned_file = ScannedFile(
            name=file_path.stem,
            extension=file_path.suffix,
            size_bytes=file_path.stat().st_size,
            absolute_path=file_path.resolve(),
            relative_path=file_path.relative_to(base_path)
        )

        scanned_files.append(scanned_file)

    return scanned_files
