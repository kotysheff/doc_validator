"""Пользовательские исключения приложения.

Модуль предназначен для формирования пользовательских классов исключений,
которые наследуются от базового класса Exception через промежуточное общее
исключение программы DocValidatorError.

Формирование собственных классов исключений позволяет более точно и гибко
классифицировать и обрабатывать ошибки, возникающие в процессе работы приложения
"""

class DocValidatorError(Exception):
    """Базовое исключение для всех ошибок приложения."""

    def __init__(self, message: str = "Ошибка в работе DocValidator") -> None:
        super().__init__(message)
        self.message = message


class DataFillError(DocValidatorError):
    """Ошибка при заполнении данных модели."""

    def __init__(self, model_name: str, field: str, value: object, reason: str) -> None:
        self.model_name = model_name
        self.field = field
        self.value = value
        self.reason = reason
        message = (
            f"Ошибка заполнения данных модели '{model_name}' "
            f"для поля '{field}': {reason}. Получено: {value!r}"
        )
        super().__init__(message)


class UserInputParseError(DocValidatorError):
    """Ошибка при разборе пользовательского ввода из CLI."""

    def __init__(self, argument: str, value: object, reason: str) -> None:
        self.argument = argument
        self.value = value
        self.reason = reason
        message = (
            f"Не удалось разобрать аргумент '{argument}': {reason}. "
            f"Входное значение: {value!r}"
        )
        super().__init__(message)


class InputRequirementFileError(DocValidatorError):
    """Ошибка переданного файла требований."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        message = f"Файл требований по пути '{path}' не может быть прочитан: {reason}"
        super().__init__(message)


class ReportWriteError(DocValidatorError):
    """Ошибка при записи отчета."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        message = f"Не удалось записать отчет в '{path}': {reason}"
        super().__init__(message)


class ScanError(DocValidatorError):
    """Техническая ошибка при сканировании каталога."""

    def __init__(self, path: str, reason: str) -> None:
        self.path = path
        self.reason = reason
        message = f"Ошибка сканирования каталога '{path}': {reason}"
        super().__init__(message)


class ValidationError(DocValidatorError):
    """Ошибка сравнения ожидаемых и фактически найденных файлов."""

    def __init__(self, expected_name: str, expected_extension: str, actual_name: str, actual_extension: str, reason: str) -> None:
        self.expected_name = expected_name
        self.expected_extension = expected_extension
        self.actual_name = actual_name
        self.actual_extension = actual_extension
        self.reason = reason
        message = (
            f"Ошибка валидации: {reason}. "
            f"Ожидалось '{expected_name}{expected_extension}', "
            f"получено '{actual_name}{actual_extension}'"
        )
        super().__init__(message)