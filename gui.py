"""
Модуль графического интерфейса приложения DocValidator.

Предоставляет пользовательский интерфейс на базе tkinter для выбора каталога,
ввода списка ожидаемых файлов, настройки параметров проверки и запуска
процесса валидации с выводом результатов в консоль или файл.
"""

import sys
import os
import re
import io
import contextlib
import threading
import logging
import time
import tkinter as tk
from tkinter import filedialog, ttk
from tkinter.scrolledtext import ScrolledText
from pathlib import Path

from doc_validator.models import ExpectedFile, ValidationSettings, ReportFormat
from doc_validator.scanner import scan_directory
from doc_validator.validator import validate_files
from doc_validator.reports import ReportBuilder
from doc_validator.console_view import print_summary
from doc_validator.config_logger import logger

BG_MAIN = "#212529"
BG_CARD = "#2b3035"
FG_TEXT = "#f8f9fa"
BG_ENTRY = "#ffffff"
FG_ENTRY = "#000000"
BG_BTN_PRIMARY = "#0d6efd"
BG_BTN_SECONDARY = "#6c757d"
FG_BTN = "#000000"
BG_CONSOLE = "#111417"
FG_CONSOLE = "#e9ecef"


class TkinterLogHandler(logging.Handler):
    """
    Обработчик логирования для вывода сообщений в текстовую область tkinter.

    Перенаправляет записи логгера в интерфейс приложения и обновляет виджет
    асинхронно, чтобы не блокировать основной поток GUI.

    Args:
        text_widget: виджет tkinter.Text для отображения логов.
    """

    def __init__(self, text_widget):
        super().__init__()
        self.text_widget = text_widget

    def emit(self, record):
        msg = self.format(record)

        def append():
            self.text_widget.insert(tk.END, f"{msg}\n")
            self.text_widget.see(tk.END)

        self.text_widget.after(0, append)


class DocValidatorGUI:
    """
    Главный класс графического интерфейса приложения.

    Создает и управляет элементами интерфейса, собирает пользовательские
    настройки, запускает проверку и отображает ее результаты.

    Args:
        root: корневой виджет tkinter.
    """

    def __init__(self, root):
        self.root = root
        self.root.title("DocValidator GUI")
        self.root.geometry("850x750")
        self.root.configure(bg=BG_MAIN)

        style = ttk.Style()
        style.theme_use("default")
        style.configure("TCombobox", fieldbackground=BG_ENTRY, background=BG_BTN_SECONDARY, foreground=FG_ENTRY)

        self.target_dir_var = tk.StringVar()
        self.output_file_var = tk.StringVar()
        self.use_output_var = tk.BooleanVar(value=False)
        self.recursive_var = tk.BooleanVar(value=False)
        self.extra_files_var = tk.BooleanVar(value=False)
        self.empty_files_var = tk.BooleanVar(value=False)
        self.debug_var = tk.BooleanVar(value=False)

        # Инициализация: создание и размещение элементов пользовательского интерфейса
        self.create_widgets()

    def create_widgets(self):
        """Создать и разместить все элементы интерфейса."""
        # Разметка: блок выбора каталога для проверки
        target_frame = tk.LabelFrame(self.root, text=" Выбор проверяемого каталога ", bg=BG_CARD, fg=FG_TEXT,
                                     font=("Arial", 10, "bold"), bd=1, relief="solid")
        target_frame.pack(fill="x", padx=15, pady=10)

        tk.Entry(target_frame, textvariable=self.target_dir_var, bg=BG_ENTRY, fg=FG_ENTRY, insertbackground=FG_ENTRY,
                 font=("Arial", 10)).pack(side="left", fill="x", expand=True, padx=10, pady=10)

        btn_browse_target = tk.Button(target_frame, text="Обзор...", bg=BG_BTN_SECONDARY, fg=FG_BTN,
                                      activebackground="#5a6268", activeforeground=FG_BTN, bd=0, padx=10,
                                      command=self.browse_target)
        btn_browse_target.pack(side="right", padx=10, pady=10)

        # Разметка: блок ввода списка ожидаемых файлов
        req_frame = tk.LabelFrame(self.root, text=" Список искомых файлов ", bg=BG_CARD, fg=FG_TEXT,
                                  font=("Arial", 10, "bold"), bd=1, relief="solid")
        req_frame.pack(fill="both", expand=False, padx=15, pady=5)

        self.files_text = ScrolledText(req_frame, height=6, bg=BG_ENTRY, fg=FG_ENTRY, insertbackground=FG_ENTRY,
                                       font="TkFixedFont")
        self.files_text.pack(fill="both", expand=True, padx=10, pady=5)
        self.files_text.insert("1.0", "document.txt\nword.docx")

        # Разметка: блок настроек проверки и вывода отчета
        settings_frame = tk.Frame(self.root, bg=BG_CARD, bd=1, relief="solid")
        settings_frame.pack(fill="x", padx=15, pady=10)

        flags_frame = tk.Frame(settings_frame, bg=BG_CARD)
        flags_frame.pack(side="left", padx=10, pady=5)

        tk.Checkbutton(flags_frame, text="Искать в подпапках", variable=self.recursive_var, bg=BG_CARD, fg=FG_TEXT,
                       activebackground=BG_CARD, activeforeground=FG_TEXT, selectcolor=BG_MAIN).pack(anchor="w", pady=2)
        tk.Checkbutton(flags_frame, text="Показать лишние файлы", variable=self.extra_files_var, bg=BG_CARD, fg=FG_TEXT,
                       activebackground=BG_CARD, activeforeground=FG_TEXT, selectcolor=BG_MAIN).pack(anchor="w", pady=2)
        tk.Checkbutton(flags_frame, text="Показать пустые файлы", variable=self.empty_files_var, bg=BG_CARD, fg=FG_TEXT,
                       activebackground=BG_CARD, activeforeground=FG_TEXT, selectcolor=BG_MAIN).pack(anchor="w", pady=2)
        tk.Checkbutton(flags_frame, text="Режим отладки (Debug)", variable=self.debug_var, bg=BG_CARD, fg=FG_TEXT,
                       activebackground=BG_CARD, activeforeground=FG_TEXT, selectcolor=BG_MAIN).pack(anchor="w", pady=2)

        report_frame = tk.Frame(settings_frame, bg=BG_CARD)
        report_frame.pack(side="right", fill="both", expand=True, padx=10, pady=5)

        tk.Checkbutton(report_frame, text="Сохранять в файл", variable=self.use_output_var, bg=BG_CARD, fg=FG_TEXT,
                       activebackground=BG_CARD, activeforeground=FG_TEXT, selectcolor=BG_MAIN,
                       command=self.toggle_output_fields).pack(anchor="w")

        self.output_entry = tk.Entry(report_frame, textvariable=self.output_file_var, bg=BG_ENTRY, fg=FG_ENTRY,
                                     insertbackground=FG_ENTRY, state="disabled")
        self.output_entry.pack(side="left", fill="x", expand=True, padx=5, pady=5)

        self.btn_browse_out = tk.Button(report_frame, text="...", bg=BG_BTN_SECONDARY, fg=FG_BTN, state="disabled",
                                        command=self.browse_output)
        self.btn_browse_out.pack(side="left", padx=5, pady=5)

        tk.Label(report_frame, text="Формат:", bg=BG_CARD, fg=FG_TEXT).pack(side="left", padx=5)
        self.format_cb = ttk.Combobox(report_frame, values=[f.value for f in ReportFormat], width=7, state="readonly")
        self.format_cb.set("txt")
        self.format_cb.pack(side="left", padx=5)

        self.btn_run = tk.Button(self.root, text="ЗАПУСТИТЬ ПРОВЕРКУ", bg=BG_BTN_PRIMARY, fg=FG_BTN,
                                 font=("Arial", 12, "bold"), activebackground="#0b5ed7", activeforeground=FG_BTN, bd=0,
                                 pady=8, command=self.start_validation_thread)
        self.btn_run.pack(fill="x", padx=15, pady=5)

        # Разметка: блок консоли для отображения хода проверки
        console_label_frame = tk.LabelFrame(self.root, text=" Консоль ", bg=BG_CARD, fg=FG_TEXT,
                                            font=("Arial", 10, "bold"), bd=1, relief="solid")
        console_label_frame.pack(fill="both", expand=True, padx=15, pady=10)

        self.console_area = ScrolledText(console_label_frame, bg=BG_CONSOLE, fg=FG_CONSOLE, insertbackground=FG_CONSOLE,
                                         font="TkFixedFont")
        self.console_area.pack(fill="both", expand=True, padx=5, pady=5)

    def toggle_output_fields(self):
        """Включить или отключить поля выбора пути сохранения отчета."""
        state = "normal" if self.use_output_var.get() else "disabled"
        self.output_entry.config(state=state)
        self.btn_browse_out.config(state=state)

    def browse_target(self):
        """Открыть диалог выбора каталога для проверки."""
        directory = filedialog.askdirectory()
        if directory:
            self.target_dir_var.set(directory)

    def browse_output(self):
        """Открыть диалог выбора файла для сохранения отчета."""
        fmt = self.format_cb.get()
        file_path = filedialog.asksaveasfilename(
            defaultextension=f".{fmt}",
            filetypes=[(f"{fmt.upper()} файлы", f"*.{fmt}"), ("Все файлы", "*.*")]
        )
        if file_path:
            self.output_file_var.set(file_path)

    def clear_console(self):
        """Очистить область вывода консоли."""
        self.console_area.delete("1.0", tk.END)

    def write_console(self, message):
        """Вывести сообщение в консоль интерфейса."""
        self.console_area.insert(tk.END, message + "\n")
        self.console_area.see(tk.END)

    def start_validation_thread(self):
        """Запустить процесс проверки в отдельном потоке."""
        threading.Thread(target=self.run_validation_pipeline, daemon=True).start()

    def run_validation_pipeline(self):
        """
        Выполнить полный цикл проверки через графический интерфейс.

        Считывает параметры из формы, запускает сканирование каталога,
        выполняет валидацию файлов и выводит результат либо в файл,
        либо в текстовую консоль интерфейса.
        """
        self.clear_console()

        # Проверка: пользователем указан путь к каталогу
        target_path_str = self.target_dir_var.get().strip()
        if not target_path_str:
            self.write_console("[ОШИБКА] Укажите путь к каталогу!")
            return

        target_directory = Path(target_path_str)
        if not target_directory.exists() or not target_directory.is_dir():
            self.write_console(f"[ОШИБКА] Путь '{target_path_str}' не найден!")
            return

        # Проверка: введён ли список ожидаемых файлов
        raw_files_text = self.files_text.get("1.0", tk.END).strip()
        if not raw_files_text:
            self.write_console("[ОШИБКА] Список файлов пуст!")
            return

        # Разбор: строки со списком файлов на отдельные элементы
        file_items = re.split(r'[,\n]', raw_files_text)
        expected_files = []

        # Сборка: объектов ExpectedFile из пользовательского ввода
        for item in file_items:
            item = item.strip()
            if not item:
                continue

            p = Path(item)
            stem = p.stem
            ext = p.suffix

            if not ext:
                self.write_console(f"[ОШИБКА] Файл '{item}' без расширения!")
                return

            try:
                expected_files.append(ExpectedFile(name=stem, allowed_extensions=[ext], required=True))
            except Exception as e:
                self.write_console(f"[ОШИБКА] Ошибка: {e}")
                return

        # Формирование: настроек проверки из пользовательских флагов
        settings = ValidationSettings(
            recursive=self.recursive_var.get(),
            check_empty_files=self.empty_files_var.get(),
            detect_extra_files=self.extra_files_var.get()
        )

        log_handler = None
        start_time = None

        # Подготовка: режима отладки и логирования
        # Подключение: обработчика логов к текстовой области интерфейса
        if self.debug_var.get():
            start_time = time.monotonic()
            root_logger = logging.getLogger()
            log_handler = TkinterLogHandler(self.console_area)
            log_handler.setFormatter(logging.Formatter("[DEBUG] %(asctime)s - %(message)s", datefmt="%H:%M:%S"))
            log_handler.setLevel(logging.DEBUG)
            root_logger.addHandler(log_handler)
            root_logger.setLevel(logging.DEBUG)

            logging.getLogger("doc_validator.config_logger").setLevel(logging.DEBUG)
            for name in logging.root.manager.loggerDict:
                logging.getLogger(name).setLevel(logging.DEBUG)

            logger.info("Включен режим отладки")
            logger.debug(f"Текущая рабочая директория: {Path.cwd()}")
            logger.debug(f"Настройки GUI: target={target_directory}, файлов требований={len(expected_files)}")
            logger.debug(
                f"Конфигурация поиска: рекурсивно={settings.recursive}, пустые={settings.check_empty_files}, лишние={settings.detect_extra_files}")

        # Выполнение: сканирования каталога и валидации файлов
        try:
            scanned_files = scan_directory(target_directory, settings.recursive)

            if self.debug_var.get():
                logger.debug(f"Сканирование завершено: в каталоге физически найдено {len(scanned_files)} файлов")

            validation_result = validate_files(expected_files, scanned_files, settings)

            if self.debug_var.get():
                logger.debug(
                    f"Результаты сопоставления: корректных={len(validation_result.found_files)}, отсутствующих={len(validation_result.missing_files)}, пустых={len(validation_result.empty_files)}, лишних={len(validation_result.extra_files)}")

            # Вывод: результата либо в файл, либо в консоль интерфейса
            output_path_str = self.output_file_var.get().strip() if self.use_output_var.get() else None

            if output_path_str:
                fmt = self.format_cb.get()
                report_builder = ReportBuilder(validation_result, settings, Path(output_path_str), ReportFormat(fmt))
                report_builder.save_report()
                self.write_console(f"\n[ИНФО] Отчет сохранен: {output_path_str}")
            else:
                f = io.StringIO()
                with contextlib.redirect_stdout(f):
                    print_summary(validation_result, show_details=True)
                self.write_console(f.getvalue())

            if self.debug_var.get() and start_time is not None:
                duration = time.monotonic() - start_time
                logger.debug(f"Общее время выполнения пайплайна: {duration:.3f} секунд")

        except Exception as exc:
            self.write_console(f"\n[КРИТИЧЕСКАЯ ОШИБКА]: {exc}")
        finally:
            # Очистка: обработчика логов после завершения проверки
            if log_handler:
                logging.getLogger().removeHandler(log_handler)


if __name__ == "__main__":
    root = tk.Tk()
    root.option_add("*Button.foreground", FG_BTN)
    app = DocValidatorGUI(root)
    app.btn_run.config(fg=FG_BTN)
    root.mainloop()