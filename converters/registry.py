from __future__ import annotations

import sys
import threading
from pathlib import Path

from backend.file_types import EXCEL_EXTENSIONS, HWP_EXTENSIONS, POWERPOINT_EXTENSIONS, WORD_EXTENSIONS
from backend.job_model import ConversionJob
from backend.settings import AppSettings
from converters.base import DependencyMissingError, ProgressCallback, UnsupportedFormatError
from converters.hwpx.hwp_automation import HwpAutomationManager
from converters.hwpx.hwp_to_hwpx import HwpToHwpxConverter
from converters.image.document_to_image import DocumentToImageConverter
from converters.pdf.excel_to_pdf import ExcelToPdfConverter
from converters.pdf.hwp_to_pdf import HwpToPdfConverter
from converters.pdf.powerpoint_to_pdf import PowerPointToPdfConverter
from converters.pdf.word_to_pdf import WordToPdfConverter


def is_com_application_installed(progid: str) -> bool:
    if sys.platform != "win32":
        return False
    import winreg

    for view in (winreg.KEY_WOW64_64KEY, winreg.KEY_WOW64_32KEY):
        try:
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"{progid}\\CLSID", 0, winreg.KEY_READ | view) as key:
                clsid = winreg.QueryValueEx(key, "")[0]
            with winreg.OpenKey(winreg.HKEY_CLASSES_ROOT, f"CLSID\\{clsid}\\LocalServer32", 0, winreg.KEY_READ | view) as key:
                if winreg.QueryValueEx(key, "")[0]:
                    return True
        except OSError:
            continue
    return False


def require_application(progid: str, name: str) -> None:
    if not is_com_application_installed(progid):
        raise DependencyMissingError(
            f"{name}이(가) 설치되어 있지 않거나 COM 자동화 등록을 찾을 수 없습니다. "
            f"이 문서를 변환하려면 {name} 설치가 필요합니다. "
            "이미 설치되어 있다면 해당 프로그램의 설치 복구를 진행해 주세요."
        )


class ConverterRegistry:
    def __init__(self, settings: AppSettings) -> None:
        self._hwp_manager = HwpAutomationManager(settings)
        self._hwp_to_hwpx = HwpToHwpxConverter(self._hwp_manager)
        self._hwp_to_pdf = HwpToPdfConverter(self._hwp_manager)
        self._word_to_pdf = WordToPdfConverter(settings)
        self._excel_to_pdf = ExcelToPdfConverter(settings)
        self._powerpoint_to_pdf = PowerPointToPdfConverter(settings)
        self._image = DocumentToImageConverter(settings)

    def convert(self, job: ConversionJob, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        if job.mode == "hwpx":
            require_application("HWPFrame.HwpObject", "한컴오피스 한글")
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
            converter, progid, name = self._hwp_to_pdf, "HWPFrame.HwpObject", "한컴오피스 한글"
        elif ext in WORD_EXTENSIONS:
            converter, progid, name = self._word_to_pdf, "Word.Application", "Microsoft Word"
        elif ext in EXCEL_EXTENSIONS:
            converter, progid, name = self._excel_to_pdf, "Excel.Application", "Microsoft Excel"
        elif ext in POWERPOINT_EXTENSIONS:
            converter, progid, name = self._powerpoint_to_pdf, "PowerPoint.Application", "Microsoft PowerPoint"
        else:
            raise UnsupportedFormatError(f"PDF 변환을 지원하지 않는 형식입니다: {ext}")
        progress(1, f"{name} 설치 여부를 확인하고 있습니다.")
        require_application(progid, name)
        converter.convert(input_path, output_path, progress, cancel_event)

    def shutdown(self) -> None:
        self._hwp_manager.shutdown()
