import logging
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest

from backend.logging_config import LOG_FILE_NAME, DailyLogFileHandler, setup_logging


def make_record(message: str) -> logging.LogRecord:
    return logging.LogRecord("test", logging.INFO, __file__, 1, message, (), None)


def test_log_appends_within_same_day(tmp_path):
    path = tmp_path / "app.log"
    handler = DailyLogFileHandler(path)
    try:
        handler.emit(make_record("first"))
        handler.emit(make_record("second"))
    finally:
        handler.close()
    text = path.read_text(encoding="utf-8")
    assert "first" in text
    assert "second" in text


def test_log_truncates_stale_file_on_open(tmp_path):
    path = tmp_path / "app.log"
    path.write_text("old contents", encoding="utf-8")
    old = datetime(2020, 1, 1).timestamp()
    os.utime(path, (old, old))
    handler = DailyLogFileHandler(path)
    try:
        handler.emit(make_record("new entry"))
    finally:
        handler.close()
    text = path.read_text(encoding="utf-8")
    assert "old contents" not in text
    assert "new entry" in text


def test_log_truncates_when_day_changes(tmp_path, monkeypatch):
    path = tmp_path / "app.log"
    handler = DailyLogFileHandler(path)
    tomorrow = date.today() + timedelta(days=1)

    class FakeDate(date):
        @classmethod
        def today(cls):
            return tomorrow

    try:
        handler.emit(make_record("before midnight"))
        monkeypatch.setattr("backend.logging_config.date", FakeDate)
        handler.emit(make_record("after midnight"))
    finally:
        handler.close()
    text = path.read_text(encoding="utf-8")
    assert "before midnight" not in text
    assert "after midnight" in text


def test_setup_logging_creates_daily_file_and_is_idempotent(tmp_path):
    root = logging.getLogger()
    added = []
    try:
        first = setup_logging(tmp_path / "a")
        added = [handler for handler in root.handlers if isinstance(handler, DailyLogFileHandler)]
        second = setup_logging(tmp_path / "a")
        assert first == second == tmp_path / "a" / "logs" / LOG_FILE_NAME
        assert len([handler for handler in root.handlers if isinstance(handler, DailyLogFileHandler)]) == 1
        logging.getLogger("test").info("hello log")
        assert "hello log" in first.read_text(encoding="utf-8")
    finally:
        for handler in added:
            root.removeHandler(handler)
            handler.close()


def test_setup_logging_clears_previous_day_file(tmp_path):
    log_dir = tmp_path / "b" / "logs"
    log_dir.mkdir(parents=True)
    log_path = log_dir / LOG_FILE_NAME
    log_path.write_text("yesterday", encoding="utf-8")
    old = datetime(2020, 1, 1).timestamp()
    os.utime(log_path, (old, old))
    root = logging.getLogger()
    added = []
    try:
        setup_logging(tmp_path / "b")
        added = [handler for handler in root.handlers if isinstance(handler, DailyLogFileHandler)]
        logging.getLogger("test").info("today only")
        text = log_path.read_text(encoding="utf-8")
        assert "yesterday" not in text
        assert "today only" in text
    finally:
        for handler in added:
            root.removeHandler(handler)
            handler.close()
