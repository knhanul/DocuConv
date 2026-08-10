from __future__ import annotations

import threading
import traceback
from pathlib import Path

from PySide6.QtCore import QThread, Signal

from backend.job_model import ConversionJob
from backend.settings import AppSettings
from converters.base import ConversionCancelled
from converters.registry import ConverterRegistry


class ConversionWorker(QThread):
    jobChanged = Signal(str, str, int, str)
    jobFinished = Signal(str)
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
            for job in self._jobs:
                if self._cancel_event.is_set():
                    self.jobChanged.emit(job.id, "취소됨", job.progress, "사용자가 작업을 취소했습니다.")
                    self.jobFinished.emit(job.id)
                    continue

                self.jobChanged.emit(job.id, "변환 중", 1, "변환을 준비하고 있습니다.")

                def progress(value: int, message: str = "") -> None:
                    if self._cancel_event.is_set():
                        raise ConversionCancelled("사용자가 작업을 취소했습니다.")
                    self.jobChanged.emit(job.id, "변환 중", value, message)

                try:
                    registry.convert(job, progress, self._cancel_event)
                    self.jobChanged.emit(job.id, "완료", 100, "변환이 완료되었습니다.")
                except ConversionCancelled as exc:
                    self.jobChanged.emit(job.id, "취소됨", job.progress, str(exc))
                except Exception as exc:  # 각 파일 실패 후 다음 파일을 계속 처리합니다.
                    detail = f"{type(exc).__name__}: {exc}"
                    self.jobChanged.emit(job.id, "실패", job.progress, detail)
                    # 디버그 빌드에서 확인할 수 있도록 stderr에도 상세 스택을 남깁니다.
                    traceback.print_exc()
                self.jobFinished.emit(job.id)
            registry.shutdown()
        finally:
            if com_initialized:
                import pythoncom

                pythoncom.CoUninitialize()
            self.allFinished.emit(self._cancel_event.is_set())
