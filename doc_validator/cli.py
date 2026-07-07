"""Обработка пользовательского ввода CLI.

Модуль предназначен для разбора аргументов командной строки, разделения
позиционных и опциональных параметров и передачи полученных данных далее
для последующей обработки.

Данный модуль является входным интерфейсом приложения, главная задача которого -
реализовать паттерн Fail-Fast: перехватить ввод пользователя, проверить его на корректность и,
если что-то не так, упасть еще до того, как система начнет тратить ресурсы на сканирование диска.
"""

import argparse
from pathlib import Path

from doc_validator.config_logger import logger
from doc_validator.models import ReportFormat
from doc_validator.exceptions import UserInputParseError


def parse_arguments() -> argparse.Namespace:
    """Разбирает и валидирует аргументы командной строки.

    Выполняет синтаксический анализ переданных параметров, проверяет физическое существование
    данных на диске и преобразует типы данных в объекты Path и Enum.

    :return:
        - argparse.Namespace - объект, содержащий валидированные параметры:
            - target (Path): Путь к проверяемому каталогу.
            - requirements (Path | None): Путь к файлу требований.
            - output (Path | None): Путь к файлу отчета.
            - format (ReportFormat): Необходимый формат отчета.
            - full (bool): Флаг детального вывода в консоль.
            - debug (bool): Флаг режима разработчика

    :raises:
        UserInputParseError: Если какой то из переданных путей некорректен, или
        целевой формат не поддерживается.
    """

    # Создание парсера аргументов командной строки
    parser = argparse.ArgumentParser(
        prog="doc_validator",
        description="CLI-программа для автоматизированной проверки каталога документов по заданному набору требований."
                    "Она позволяет выявлять отсутствие файлов, несоответствие расширений, ошибки в структуре входных "
                    "данных и формирует отчет о результатах проверки",
        epilog="Разработано by kotysheff",
        prefix_chars="-",
    )

    # Обязательные позиционные аргументы
    parser.add_argument(
        "target",
        type=Path,
        help="Путь к проверяемому каталогу"
    )

    # Опциональные аргументы
    parser.add_argument(
        "-r", "--requirements",
        type=Path,
        help="Путь к JSON-файлу требований")
    parser.add_argument(
        "-o", "--output",
        type=Path,
        help="Путь к файлу вывода отчета. Указан - отчет сохраняется в файл; "
             "не указан - отчет печатается в консоль через модуль 'rich'")
    parser.add_argument(
        "-f", "--format",
        type=str,
        choices=[f.value for f in ReportFormat],
        default="txt",
        help="Формат выходного отчета")

    # Флаги детализации
    parser.add_argument(
        "--full",
        action="store_true",
        help="Флаг не влияет на алгоритм проверки. Отвечает за детализацию консольного вывода")
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Флаг позволяет включить режим разработчика. При нем программа будет: "
        "- Печатать traceback"
        "- Печатать, какие модули запускаются"
        "- Печатать, сколько файлов найдено"
        "- Печатать, сколько времени заняло сканирование"
        "- Какие настройки загружены")

    args = parser.parse_args()
    logger.info("Получен ввод от пользователя: %s", args)

    # Валидация: целевая директория для сканирования
    if not isinstance(args.target, Path) or not args.target.exists() or not args.target.is_dir():
        logger.error("Неверный аргумент target: %s", args.target)
        raise UserInputParseError("target", args.target, "путь не существует или не является каталогом")

    # Валидация: файл требований
    if args.requirements is not None:
        if not isinstance(args.requirements, Path) or not args.requirements.exists() or not args.requirements.is_file():
            logger.error("Неверный аргумент --requirements: %s", args.requirements)
            raise UserInputParseError("--requirements", args.requirements,
                                      "файл требований не найден или не является файлом")

    # Валидация: директория сохранения отчета
    if args.output is not None:
        parent = args.output.parent
        if not parent.exists():
            logger.error("Каталог для вывода не существует: %s", parent)
            raise UserInputParseError("--output", args.output, "каталог для вывода не существует")
        if not parent.is_dir():
            logger.error("Родительский путь вывода не является каталогом: %s", parent)
            raise UserInputParseError("--output", args.output, "родительский путь не является каталогом")

    # Валидация: формат отчета
    try:
        args.format = ReportFormat(args.format)
    except Exception as exc:
        logger.error("Передан недопустимый формат выходного файла: %s", exc)
        raise UserInputParseError("--format", args.format, f"недопустимый формат: {exc}")

    logger.info(f"Возврат аргументов командной строки {vars(args)}")
    return args
