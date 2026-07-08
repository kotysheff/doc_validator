"""
Модуль сканирования каталога.

Модуль отвечает за обход указанного каталога, выявление файлов и
преобразование найденных результатов во внутренние объекты ScannedFile.
"""

import os
from pathlib import Path

from doc_validator.config_logger import logger
from doc_validator.exceptions import ScanError
from doc_validator.models import ScannedFile


def scan_directory(target_dir: str | Path, recursive: bool = False) -> list[ScannedFile]:
    """
    Функция предназначена для сканирования каталога и возврата списка найденных файлов.

    Обходит указанный каталог, собирает информацию о найденных файлах и
    преобразует их в объекты ScannedFile для дальнейшей обработки.

    Args:
        target_dir: путь к каталогу, который необходимо просканировать.
        recursive: флаг рекурсивного обхода подкаталогов.

    Returns:
        Список объектов ScannedFile, описывающих найденные файлы.

    Raises:
        ScanError: если целевой каталог не существует, не является директорией
            или недоступен для чтения.
    """
    logger.info("Запущено сканирование каталога %s рекурсивно=%s", target_dir, recursive)
    target_dir = Path(target_dir)

    # Валидация: пути к целевому каталогу существует
    if not target_dir.exists():
        logger.error("Целевая директория не существует: %s", target_dir)
        raise ScanError(str(target_dir),
                        "Указанная директория не существует")

    # Валидация: целевой каталог является директорией
    if not target_dir.is_dir():
        logger.error("Целевой путь не является директорией: %s", target_dir)
        raise ScanError(str(target_dir),
                        "Указанный путь не является директорией")

    # Валидация: у целевого каталога есть права на чтение
    if not os.access(target_dir, os.R_OK):
        logger.error("Нет прав на чтение директории: %s", target_dir)
        raise ScanError(str(target_dir),
                        "Нет прав на чтение директории")

    # Выбор режима обхода каталога и формирование списка объектов отсканированных файлов
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

    logger.info("Сканирование завершено, найдено файлов: %d", len(scanned_files))
    return scanned_files
