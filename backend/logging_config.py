from __future__ import annotations

import logging
import sys
from datetime import date
from pathlib import Path

from PySide6.QtCore import QtMsgType, qInstallMessageHandler

LOG_FILE_NAME = "docconv.log"

_qt_handler_installed = False


class DailyLogFileHandler(logging.FileHandler):
    def __init__(self, path: Path) -> None:
        self._date = date.today()
        mode = "w" if path.exists() and date.fromtimestamp(path.stat().st_mtime) < self._date else "a"
        super().__init__(path, mode=mode, encoding="utf-8")

    def emit(self, record: logging.LogRecord) -> None:
        today = date.today()
        if today != self._date:
            self.acquire()
            try:
                self.close()
                Path(self.baseFilename).write_text("", encoding="utf-8")
                self.stream = self._open()
                self._date = today
            finally:
                self.release()
        super().emit(record)


def _qt_message_handler(mode, context, message: str) -> None:
    level = {
        QtMsgType.QtDebugMsg: logging.DEBUG,
        QtMsgType.QtInfoMsg: logging.INFO,
        QtMsgType.QtWarningMsg: logging.WARNING,
        QtMsgType.QtCriticalMsg: logging.ERROR,
        QtMsgType.QtFatalMsg: logging.CRITICAL,
    }.get(mode, logging.WARNING)
    logging.getLogger("qt").log(level, "%s", message)


def _excepthook(exc_type, exc, tb) -> None:
    logging.getLogger(__name__).critical("처리되지 않은 예외가 발생했습니다.", exc_info=(exc_type, exc, tb))


def setup_logging(app_data: Path) -> Path:
    global _qt_handler_installed
    log_dir = app_data / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    log_path = log_dir / LOG_FILE_NAME
    root = logging.getLogger()
    if not any(isinstance(handler, DailyLogFileHandler) for handler in root.handlers):
        handler = DailyLogFileHandler(log_path)
        handler.setFormatter(logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s"))
        root.addHandler(handler)
    root.setLevel(logging.INFO)
    if not _qt_handler_installed:
        qInstallMessageHandler(_qt_message_handler)
        sys.excepthook = _excepthook
        _qt_handler_installed = True
    return log_path
