from __future__ import annotations

import threading
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ProgressCallback
from converters.hwpx.hwp_automation import HwpAutomation


class HwpToHwpxConverter:
    def __init__(self, settings: AppSettings) -> None:
        self._automation = HwpAutomation(settings)

    def convert(self, input_path: Path, output_path: Path, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        self._automation.save_as(input_path, output_path, "HWPX", progress, cancel_event)
