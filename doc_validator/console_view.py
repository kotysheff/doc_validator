"""Вывод результатов проверки в консоль.

Модуль отвечает за отображение результатов работы программы в консоли. Вывод
форматируется с использованием сторонней библиотеки Rich.

В зависимости от входных данных, результат работы программы может выводиться в двух форматах:
    - стандартный: включает в себя вывод статуса, основной статистики и проблем
    - расширенный: помимо стандартного вывода дополнительно включает в себя вывод информации о
    найденных файлах, ненайденных файлах, файлах с неверным расширением, лишних файлах
"""

from rich.console import Console
from rich.table import Table
from rich.panel import Panel

from doc_validator.config_logger import logger
from doc_validator.models import ValidationResult


def print_summary(result: ValidationResult, show_details: bool = False) -> None:
    """Принимает результат выполнения проверки и формирует структурированный вывод в консоль.

    Args:
        result (ValidationResult): Итог проверки, содержащий списки найденных,
            отсутствующих, пустых, лишних файлов и обнаруженных проблем.
        show_details (bool): Флаг включения расширенного (детального) вывода.
            По умолчанию False.

    Raises:
        TypeError: Если параметры result или show_details переданы с неверным типом данных.
    """

    # Валидация: входные параметры
    if not isinstance(result, ValidationResult):
        logger.error("Неправильный тип result: %s", type(result).__name__)
        raise TypeError(f"Поле result должно быть типа 'ValidationResult', получено: {type(result).__name__}")
    if not isinstance(show_details, bool):
        logger.error("Неправильный тип show_details: %s", type(show_details).__name__)
        raise TypeError(f"Поле show_details должно быть типа 'bool', получено: {type(show_details).__name__}")

    logger.info("Вывод сводки в консоль, детализация=%s", show_details)
    console = Console()
    console.print(Panel.fit("Отчет проверки каталога DocValidator", style="cyan"))
    console.print()

    # Выбор цвета в зависимости от статуса завершения
    if result.status.value == "OK":
        status_color = "green"
    elif result.status.value == "WARNING":
        status_color = "yellow"
    else:
        status_color = "red"

    console.print(f"Итоговый статус [{status_color}] {result.status.value} [/{status_color}]")
    console.print()

    # Формирование таблицы базовой статистики
    console.print("Статистика: ", style="bold")
    stats_table = Table(show_header=False)
    stats_table.add_column("Категория", no_wrap=True)
    stats_table.add_column("Количество", no_wrap=True)
    stats_table.add_row("Найдено корректных файлов", str(len(result.found_files)))
    stats_table.add_row("Отсутствует файлов", str(len(result.missing_files)))
    stats_table.add_row("Неверное расширение", str(len(result.wrong_extension_files)))
    stats_table.add_row("Пустые файлы", str(len(result.empty_files)))
    stats_table.add_row("Лишние файлы", str(len(result.extra_files)))
    stats_table.add_row("Всего проблем", str(len(result.issues)))

    console.print(stats_table)
    logger.debug("Таблица статистики успешно построена")
    console.print()

    # В случае включения режима расширенного вывода
    if show_details:
        # Формирование таблицы найденных файлов
        if result.found_files:
            console.print("Найденные файлы: ", style="bold green")
            found_table = Table(show_header=True, border_style="green")
            found_table.add_column("№", style="dim", width=4)
            found_table.add_column("Имя файла", style="white")
            found_table.add_column("Расширение", style="cyan")
            found_table.add_column("Размер (байт)", style="yellow", justify="right")

            for number, file in enumerate(result.found_files, start=1):
                name = file.name
                extension = file.extension
                size = str(file.size_bytes)
                found_table.add_row(str(number), name, extension, size)
            console.print(found_table)
            logger.debug("Таблица найденных файлов успешно построена")
            console.print()

        # Формирование таблицы отсутствующих файлов
        if result.missing_files:
            console.print("Отсутствующие файлы: ", style="bold red")
            missing_table = Table(show_header=True, border_style="red")
            missing_table.add_column("№", style="dim", width=4)
            missing_table.add_column("Имя файла", style="white")
            missing_table.add_column("Разрешённые расширения", style="cyan")
            missing_table.add_column("Обязательный", style="yellow")

            for idx, file in enumerate(result.missing_files, 1):
                name = file.name
                allowed = ', '.join(file.allowed_extensions)
                required = "Да" if file.required else "Нет"
                missing_table.add_row(str(idx), name, allowed, required)

            console.print(missing_table)
            logger.debug("Таблица отсутствующих файлов успешно построена")
            console.print()

        # Формирование таблицы файлов с неверным расширением
        if result.wrong_extension_files:
            console.print("Файлы с неверным расширением: ", style="bold yellow")
            wrong_table = Table(show_header=True, border_style="yellow")
            wrong_table.add_column("№", style="dim", width=4)
            wrong_table.add_column("Имя файла", style="white")
            wrong_table.add_column("Расширение", style="cyan")
            wrong_table.add_column("Путь", style="dim")

            for idx, file in enumerate(result.wrong_extension_files, 1):
                name = file.name
                extension = file.extension
                path = str(file.relative_path)
                wrong_table.add_row(str(idx), name, f"[red]{extension}[/red]", path)

            console.print(wrong_table)
            logger.debug("Таблица файлов с неверным расширением успешно построена")
            console.print()

        # Формирование таблицы пустых файлов
        if result.empty_files:
            console.print("Пустые файлы: ", style="bold yellow")
            empty_table = Table(show_header=True, border_style="yellow")
            empty_table.add_column("№", style="dim", width=4)
            empty_table.add_column("Имя файла", style="white")
            empty_table.add_column("Расширение", style="cyan")
            empty_table.add_column("Путь", style="dim")

            for idx, file in enumerate(result.empty_files, 1):
                name = file.name
                extension = file.extension
                path = str(file.relative_path)
                empty_table.add_row(str(idx), name, extension, path)

            console.print(empty_table)
            logger.debug("Таблица пустых файлов успешно построена")
            console.print()

        # Формирование таблицы лишних файлов
        if result.extra_files:
            console.print("Лишние файлы: ", style="bold yellow")
            extra_table = Table(show_header=True, border_style="yellow")
            extra_table.add_column("№", style="dim", width=4)
            extra_table.add_column("Имя файла", style="white")
            extra_table.add_column("Расширение", style="cyan")
            extra_table.add_column("Размер", style="yellow", justify="right")

            for idx, file in enumerate(result.extra_files, 1):
                name = file.name
                extension = file.extension
                size = file.size_bytes
                extra_table.add_row(str(idx), name, extension, str(size))

            console.print(extra_table)
            logger.debug("Таблица лишних файлов успешно построена")
            console.print()

    # Формирование таблицы проблем при сканировании
    if result.issues:
        console.print("Проблемы: ", style="bold red")
        issues_table = Table(show_header=True, border_style="red")
        issues_table.add_column("№", style="dim", width=4)
        issues_table.add_column("Важность", style="bold")
        issues_table.add_column("Тип", style="cyan")
        issues_table.add_column("Файл", style="white")
        issues_table.add_column("Сообщение", style="dim")

        for idx, issue in enumerate(result.issues, 1):
            severity = issue.severity.value
            issue_type = issue.issue_type.value
            file_name = issue.file_name if issue.file_name else "-"
            message = issue.message if issue.message else ""

            issues_table.add_row(str(idx), severity, issue_type, file_name, message)

        console.print(issues_table)
        logger.debug("Таблица с проблемами успешно построена")

    else:
        console.print("Проблем не обнаружено!", style="bold green")
    console.print()
