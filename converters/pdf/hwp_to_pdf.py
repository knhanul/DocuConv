from __future__ import annotations

import threading
from pathlib import Path

from converters.base import ProgressCallback
from converters.hwpx.hwp_automation import HwpAutomationManager


class HwpToPdfConverter:
    def __init__(self, hwp_manager: HwpAutomationManager) -> None:
        self._manager = hwp_manager

    def convert(self, input_path: Path, output_path: Path, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        self._manager.convert(input_path, output_path, "PDF", progress, cancel_event)
