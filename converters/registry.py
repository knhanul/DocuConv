from __future__ import annotations

import threading
from pathlib import Path

from backend.file_types import EXCEL_EXTENSIONS, HWP_EXTENSIONS, POWERPOINT_EXTENSIONS, WORD_EXTENSIONS
from backend.job_model import ConversionJob
from backend.settings import AppSettings
from converters.base import ProgressCallback, UnsupportedFormatError
from converters.hwpx.hwp_to_hwpx import HwpToHwpxConverter
from converters.image.document_to_image import DocumentToImageConverter
from converters.pdf.excel_to_pdf import ExcelToPdfConverter
from converters.pdf.hwp_to_pdf import HwpToPdfConverter
from converters.pdf.powerpoint_to_pdf import PowerPointToPdfConverter
from converters.pdf.word_to_pdf import WordToPdfConverter


class ConverterRegistry:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._hwp_to_hwpx = HwpToHwpxConverter(settings)
        self._hwp_to_pdf = HwpToPdfConverter(settings)
        self._word_to_pdf = WordToPdfConverter(settings)
        self._excel_to_pdf = ExcelToPdfConverter(settings)
        self._powerpoint_to_pdf = PowerPointToPdfConverter(settings)
        self._image = DocumentToImageConverter(settings, self.convert_to_pdf)

    def convert(self, job: ConversionJob, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        if job.mode == "hwpx":
            self._hwp_to_hwpx.convert(job.input_path, job.output_path, progress, cancel_event)
            return
        if job.mode == "pdf":
            self.convert_to_pdf(job.input_path, job.output_path, progress, cancel_event)
            return
        if job.mode == "image":
            self._image.convert(job.input_path, job.output_path, job.image_format, progress, cancel_event)
            return
        raise UnsupportedFormatError(f"지원하지 않는 변환 모드입니다: {job.mode}")

    def convert_to_pdf(
        self,
        input_path: Path,
        output_path: Path,
        progress: ProgressCallback,
        cancel_event: threading.Event,
    ) -> None:
        ext = input_path.suffix.lower()
        if ext in HWP_EXTENSIONS:
            self._hwp_to_pdf.convert(input_path, output_path, progress, cancel_event)
        elif ext in WORD_EXTENSIONS:
            self._word_to_pdf.convert(input_path, output_path, progress, cancel_event)
        elif ext in EXCEL_EXTENSIONS:
            self._excel_to_pdf.convert(input_path, output_path, progress, cancel_event)
        elif ext in POWERPOINT_EXTENSIONS:
            self._powerpoint_to_pdf.convert(input_path, output_path, progress, cancel_event)
        else:
            raise UnsupportedFormatError(f"PDF 변환을 지원하지 않는 형식입니다: {ext}")
