"""
Модуль загрузки и обработки требований к файлам.

Модуль предназначен для чтения JSON-файла со списком документов,
которые необходимо найти, и преобразования его данных в структуры,
удобные для дальнейшей обработки в ходе валидации каталога.
"""

import json
import os
from pathlib import Path

from doc_validator.config_logger import logger
from doc_validator.models import Requirements, ExpectedFile, ValidationSettings
from doc_validator.exceptions import InputRequirementFileError, DataFillError


def load_requirements(path: str | Path) -> Requirements:
    """
    Функция предназначена для загрузки требования к поиску файлов из JSON-файла.

    Открывает файл с описанием ожидаемых файлов, валидирует его структуру
    и преобразует данные в объект Requirements, который затем используется
    в процессе проверки каталогов.

    Args:
        path: путь к JSON-файлу с требованиями.

    Returns:
        Объект Requirements, содержащий список ожидаемых файлов и настройки проверки.

    Raises:
        InputRequirementFileError: если файл отсутствует, имеет неверный формат
            или содержит некорректные данные.
    """
    logger.info("Начинаю загрузку требований из файла: %s", path)
    path = Path(path)

    # Валидация: путь к файлу требований
    if not path.exists():
        logger.error("Файл требований не найден: %s", path)
        raise InputRequirementFileError(str(path), "Указанный файл требований не существует")

    # Валидация: путь к файлу, а не к директории
    if not path.is_file():
        raise InputRequirementFileError(str(path), "Указанный путь является директорией, а не файлом")

    # Валидация: файл с расширением json
    if path.suffix.lower() != ".json":
        raise InputRequirementFileError(str(path), "Файл требований должен иметь расширение .json")

    # Валидация: есть права на чтение файла
    if not os.access(path, os.R_OK):
        logger.error("Нет прав на чтение файла требований: %s", path)
        raise InputRequirementFileError(str(path), "Нет прав на чтение файла требований")

    # Попытка чтения JSON файла
    try:
        with open(path, "r", encoding="utf-8") as file:
            requirements_raw = json.load(file)
    except json.JSONDecodeError as error: # Перехват исключения структуры JSON
        logger.exception("JSON-декодирование файла требований %s не удалось: %s", path, error)
        raise InputRequirementFileError(
            str(path),
            f"JSON-файл повреждён: {error.msg} в строке {error.lineno}, символ {error.colno}"
        )
    except UnicodeDecodeError as error: # Перехват исключения кодировки
        logger.exception("Ошибка кодировки JSON-файла требований %s: %s", path, error)
        raise InputRequirementFileError(
            str(path),
            f"Ошибка кодировки JSON-файла: {error}"
        )

    # Валидация: содержимое файла является словарем
    if not isinstance(requirements_raw, dict):
        logger.error("Неверная структура JSON в файле требований %s: корневой объект не объект", path)
        raise InputRequirementFileError(
            str(path),
            f"Корневой объект JSON должен быть объектом, получено {type(requirements_raw).__name__}"
        )

    # Валидация: наличие обязательного поля запрашиваемых файлов
    if "required_files" not in requirements_raw:
        raise InputRequirementFileError(str(path), "Отсутствует обязательное поле 'required_files'")

    required_files_raw = requirements_raw["required_files"]
    settings_raw = requirements_raw.get("settings", {})

    # Валидация: запрашиваемые файлы должны быть оформлены в виде списка
    if not isinstance(required_files_raw, list):
        logger.error("Поле required_files не является списком в файле требований %s", path)
        raise InputRequirementFileError(
            str(path),
            f"Поле 'required_files' должно быть списком, получено {type(required_files_raw).__name__}"
        )

    # Валидация: список требуемых файлов не может быть пуст
    if not required_files_raw:
        logger.error("Список required_files пуст в файле требований %s", path)
        raise InputRequirementFileError(str(path), "Список 'required_files' не должен быть пустым")

    # Валидация: конфигурация настроек должна быть представлена в виде словаря
    if not isinstance(settings_raw, dict):
        logger.error("Поле settings не является объектом в файле требований %s", path)
        raise InputRequirementFileError(
            str(path),
            f"Поле 'settings' должно быть объектом, получено {type(settings_raw).__name__}"
        )

    # Формирование списка запрашиваемых файлов
    expected_files: list[ExpectedFile] = []
    for index, file_data in enumerate(required_files_raw):
        if not isinstance(file_data, dict):
            raise InputRequirementFileError(
                str(path),
                f"Элемент 'required_files' по индексу {index} должен быть объектом, "
                f"получено {type(file_data).__name__}"
            )

        if "name" not in file_data:
            raise InputRequirementFileError(
                str(path),
                f"У элемента 'required_files' по индексу {index} отсутствует поле 'name'"
            )

        try:
            expected_file = ExpectedFile(
                name=file_data["name"],
                allowed_extensions=file_data.get("allowed_extensions", []),
                required=file_data.get("required", True),
            )
        except (DataFillError, TypeError) as error:
            logger.exception("Ошибка валидации элемента required_files в файле требований %s: %s", path, error)
            raise InputRequirementFileError(
                str(path),
                f"Ошибка валидации элемента 'required_files' по индексу {index}: {error}"
            )

        expected_files.append(expected_file)

    # Формирование объекта настроек
    try:
        settings = ValidationSettings(
            recursive=settings_raw.get("recursive", False),
            check_empty_files=settings_raw.get("check_empty_files", False),
            detect_extra_files=settings_raw.get("detect_extra_files", False),
        )
    except (DataFillError, TypeError) as error:
        logger.exception("Ошибка валидации настроек проверки в файле требований %s: %s", path, error)
        raise InputRequirementFileError(
            str(path),
            f"Ошибка валидации настроек проверки: {error}"
        )

    return Requirements(
        required_files=expected_files,
        settings=settings,
    )