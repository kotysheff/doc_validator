"""Обработка пользовательского ввода CLI.

Модуль предназначен для разбора аргументов командной строки, разделения
позиционных и опциональных параметров и передачи полученных данных далее
для последующей обработки.
"""

import argparse
from pathlib import Path

from doc_validator.models import ReportFormat
from doc_validator.exceptions import UserInputParseError

def create_parser() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="doc_validator",
        description="CLI-программа для автоматизированной проверки каталога документов по заданному набору требований."
                    "Она позволяет выявлять отсутствие файлов, несоответствие расширений, ошибки в структуре входных "
                    "данных и формирует отчет о результатах проверки",
        epilog="Разработано by kotysheff",
        prefix_chars="-",
    )
    parser.add_argument("target", type=Path, help="Путь к проверяемому каталогу")
    parser.add_argument("-r", "--requirements", type=Path, help="Пусть к JSON-файлу требований")
    parser.add_argument("-o", "--output", type=Path, help="Флаг отвечает за место вывода отчета. Указан - отчет "
                                                          "сохраняется в файл; не указан - отчет печатается в консоль через модуль 'rich'")
    parser.add_argument("-f", "--format", type=str, choices=[f.value for f in ReportFormat], default="txt",
                        help="Формат выходного отчета")
    parser.add_argument("--full", action="store_true", help="Флаг не влияет на алгоритм проверки. Отвечает за "
                                                            "детализацию консольного вывода")
    parser.add_argument("--debug", action="store_true", help="Флаг позволяет включить режим разработчика. При нем "
                                                             "программа будет: "
                                                             "- Печатать traceback"
                                                             "- Печатать, какие модули запускаются"
                                                             "- Печатать, сколько файлов найдено"
                                                             "- Печатать, сколько времени заняло сканирование"
                                                             "- Какие настройки загружены")

    args = parser.parse_args()

    if not isinstance(args.target, Path) or not args.target.exists() or not args.target.is_dir():
        raise UserInputParseError("target", args.target, "путь не существует или не является каталогом")

    if args.requirements is not None:
        if not isinstance(args.requirements, Path) or not args.requirements.exists() or not args.requirements.is_file():
            raise UserInputParseError("--requirements", args.requirements, "файл требований не найден или не является файлом")

    if args.output is not None:
        parent = args.output.parent
        if not parent.exists():
            raise UserInputParseError("--output", args.output, "каталог для вывода не существует")
        if not parent.is_dir():
            raise UserInputParseError("--output", args.output, "родительский путь не является каталогом")

    try:
        args.format = ReportFormat(args.format)
    except Exception as exc:
        raise UserInputParseError("--format", args.format, f"недопустимый формат: {exc}")

    return args