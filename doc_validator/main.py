"""
Модуль точки входа CLI-приложения DocValidator.

В случае запуска из-под CLI-интерфейса Модуль отвечает за запуск основного
пайплайна обработки данных, связывание всех модулей между собой,
обработку ошибок верхнего уровня и выбор режима вывода результатов в консоль или в файл.
"""

from doc_validator.cli import parse_arguments
from doc_validator.console_view import print_summary
from doc_validator.config_logger import logger
from doc_validator.models import ReportFormat
from doc_validator.reports import ReportBuilder
from doc_validator.requirements_loader import load_requirements
from doc_validator.scanner import scan_directory
from doc_validator.validator import validate_files
from doc_validator.exceptions import InputRequirementFileError, ScanError, ReportWriteError

import logging
import sys
import time
from pathlib import Path

def main() -> int:
    """
    Запустить основной цикл работы CLI-приложения.

    Выполняет запуск функций разбора аргументов командной строки, загрузки требований,
    сканирования каталога, валидации файлов и формирования отчета или
    вывода результата в консоль.

    Returns:
        Код завершения приложения: 0 при успешном завершении и ненулевой код при ошибке.
    """

    # Попытка парсинга аргументов командной строки
    try:
        cli_arguments = parse_arguments()

        # Создание объектов на основе аргументов командной строки
        target_directory = cli_arguments.target
        requirements_file = cli_arguments.requirements
        output_path = cli_arguments.output
        format = cli_arguments.format
        full_flag = cli_arguments.full
        debug_flag = cli_arguments.debug
        start_time = None

        # Проверка включенного флага debug-мода
        if debug_flag:
            start_time = time.monotonic() # Засекаем время старта выполнения программы

            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_handler.setFormatter(logging.Formatter("[%(asctime)s] - %(name)s - %(levelname)s - %(message)s",
                                                           datefmt="%Y-%m-%d %H:%M:%S"))

            root_logger = logging.getLogger()
            root_logger.addHandler(console_handler)
            root_logger.setLevel(logging.DEBUG)

            for name in logging.root.manager.loggerDict:
                logging.getLogger(name).setLevel(logging.DEBUG)

            logger.info("Включен режим отладки")
            logger.info("Запуск программы doc_validator")
            logger.debug("Текущая рабочая директория: %s", Path.cwd())
            logger.debug("Аргументы командной строки:")
            logger.debug("target: %s", target_directory)
            logger.debug("requirements: %s", requirements_file)
            logger.debug("output: %s", output_path)
            logger.debug("format: %s", format)
            logger.debug("full: %s", full_flag)
            logger.debug("debug: %s", debug_flag)

        # Попытка загрузить файл требований, парсинг на объекты требуемых файлов и настроек
        try:
            logger.info("Загружаю требования из файла: %s", requirements_file)

            if debug_flag:
                logger.debug("Проверка файла требований")
                logger.debug("Путь: %s", requirements_file)
                logger.debug("Существует: %s", requirements_file.exists() if requirements_file else False)
                logger.debug("Это файл: %s", requirements_file.is_file() if requirements_file else False)

            requirements = load_requirements(requirements_file)
            expected_files = requirements.required_files
            settings = requirements.settings

            if debug_flag:
                logger.debug(
                    "Требования загружены: ожидаемых файлов=%d, рекурсивно=%s, check_empty_files=%s, detect_extra_files=%s",
                    len(expected_files),
                    settings.recursive,
                    settings.check_empty_files,
                    settings.detect_extra_files,
                )

        except InputRequirementFileError as exception:
            logger.exception("Ошибка загрузки требований: %s", exception)
            return 2

        # Попытка запуска механизма сканирования каталога(ов), создания объекта
        # отсканированных файлов
        try:
            logger.info("Сканирую каталог: %s", target_directory)
            if debug_flag:
                logger.debug("Параметры сканирования: рекурсивно=%s", settings.recursive)

            scanned_files = scan_directory(target_directory, settings.recursive)

            if debug_flag:
                logger.debug("Сканирование завершено: найдено %d файлов", len(scanned_files))
        except ScanError as exception:
            logger.exception("Ошибка при сканировании каталога: %s", exception)
            return 3

        # Запуск функционала валидации файлов, формирования объекта результата валидации
        validation_result = validate_files(expected_files, scanned_files, settings)

        if debug_flag:
            logger.debug("Результат валидации: найдено=%d, отсутствует=%d, неверных расширений=%d, пустых=%d, лишних=%d, проблем=%d",
                         len(validation_result.found_files),
                         len(validation_result.missing_files),
                         len(validation_result.wrong_extension_files),
                         len(validation_result.empty_files),
                         len(validation_result.extra_files),
                         len(validation_result.issues),
            )

        # Попытка формирования отчета и его дальнейшего вывода в консоль или файл
        try:
            if output_path:
                logger.info("Формирую отчет: %s формат=%s", output_path, format)
                report = ReportBuilder(validation_result, settings, output_path, ReportFormat(format))
                report.save_report()
                logger.info("Отчет успешно записан: %s", output_path)
            else:
                logger.info("Вывожу результат в консоль")
                print_summary(validation_result, full_flag)
        except ReportWriteError as exception:
            logger.exception("Ошибка при записи отчета: %s", exception)
            return 4

        if debug_flag and start_time is not None:
            duration = time.monotonic() - start_time
            logger.debug("Общее время выполнения: %.3f секунд", duration)

    # Перехват исключений всех типов
    except Exception as exception:
        logger.exception("Неожиданная ошибка в ходе выполнения: %s", exception)
        return 1

    return 0

if __name__ == "__main__":
    raise SystemExit(main())