from __future__ import annotations

import logging
import threading
import traceback
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from backend.job_model import ConversionJob
from backend.settings import AppSettings
from converters.base import ConversionCancelled, DependencyMissingError
from converters.registry import ConverterRegistry

logger = logging.getLogger(__name__)


class ConversionWorker(QThread):
    jobChanged = Signal(str, str, int, str)
    jobFinished = Signal(str)
    dependencyMissing = Signal(str)
    allFinished = Signal(bool)

    def __init__(self, jobs: list[ConversionJob], settings: AppSettings, parent=None) -> None:
        super().__init__(parent)
        self._jobs = jobs
        self._settings = settings
        self._cancel_event = threading.Event()

    def request_cancel(self) -> None:
        self._cancel_event.set()

    def run(self) -> None:
        com_initialized = False
        try:
            if __import__("sys").platform == "win32":
                import pythoncom

                pythoncom.CoInitialize()
                com_initialized = True

            registry = ConverterRegistry(self._settings)
            logger.info("변환 작업 시작: %d개 파일", len(self._jobs))
            for job in self._jobs:
                if self._cancel_event.is_set():
                    self.jobChanged.emit(job.id, "취소됨", job.progress, "사용자가 작업을 취소했습니다.")
                    logger.info("작업 취소됨(미처리): %s", job.input_path)
                    self.jobFinished.emit(job.id)
                    continue

                logger.info("작업 시작: %s -> %s (모드=%s)", job.input_path, job.output_path, job.mode)
                self.jobChanged.emit(job.id, "변환 중", 1, "변환을 준비하고 있습니다.")

                def progress(value: int, message: str = "") -> None:
                    if self._cancel_event.is_set():
                        raise ConversionCancelled("사용자가 작업을 취소했습니다.")
                    if message:
                        logger.info("[%s] %s (%d%%)", job.input_path.name, message, value)
                    self.jobChanged.emit(job.id, "변환 중", value, message)

                try:
                    registry.convert(job, progress, self._cancel_event)
                    self.jobChanged.emit(job.id, "완료", 100, "변환이 완료되었습니다.")
                    logger.info("작업 완료: %s", job.output_path)
                except ConversionCancelled as exc:
                    self.jobChanged.emit(job.id, "취소됨", job.progress, str(exc))
                    logger.info("작업 취소됨: %s", job.input_path)
                except DependencyMissingError as exc:
                    self.jobChanged.emit(job.id, "실패", job.progress, str(exc))
                    self.dependencyMissing.emit(str(exc))
                    logger.warning("필수 프로그램 미설치: %s — %s", job.input_path.name, exc)
                except Exception as exc:  # 각 파일 실패 후 다음 파일을 계속 처리합니다.
                    detail = f"{type(exc).__name__}: {exc}"
                    self.jobChanged.emit(job.id, "실패", job.progress, detail)
                    logger.exception("변환 실패: %s", job.input_path)
                    # 디버그 빌드에서 확인할 수 있도록 stderr에도 상세 스택을 남깁니다.
                    traceback.print_exc()
                self.jobFinished.emit(job.id)
            registry.shutdown()
            logger.info("변환 작업 종료: 취소 여부=%s", self._cancel_event.is_set())
        finally:
            if com_initialized:
                import pythoncom

                pythoncom.CoUninitialize()
            self.allFinished.emit(self._cancel_event.is_set())
