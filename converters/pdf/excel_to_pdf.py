from __future__ import annotations

import gc
import threading
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, DependencyMissingError, ProgressCallback, require_input_file, require_windows


class ExcelToPdfConverter:
    XL_TYPE_PDF = 0

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def convert(self, input_path: Path, output_path: Path, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        require_windows("Excel PDF 변환")
        require_input_file(input_path)
        try:
            import win32com.client
        except ImportError as exc:
            raise DependencyMissingError("pywin32가 설치되어 있지 않습니다.") from exc

        app = None
        workbook = None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            progress(10, "Microsoft Excel을 실행하고 있습니다.")
            try:
                app = win32com.client.DispatchEx("Excel.Application")
            except Exception as exc:
                raise DependencyMissingError("Microsoft Excel 데스크톱 앱을 실행할 수 없습니다.") from exc
            app.Visible = self._settings.office_visible
            app.DisplayAlerts = False
            app.AskToUpdateLinks = False
            progress(35, "Excel 문서를 열고 있습니다.")
            workbook = app.Workbooks.Open(str(input_path.resolve()), UpdateLinks=0, ReadOnly=True)
            if cancel_event.is_set():
                raise ConversionCancelled("변환이 취소되었습니다.")
            progress(75, "Excel 문서를 PDF로 내보내고 있습니다.")
            workbook.ExportAsFixedFormat(self.XL_TYPE_PDF, str(output_path.resolve()))
            if not output_path.exists():
                raise ConversionError("Excel PDF 파일이 생성되지 않았습니다.")
            progress(95, "Excel 문서를 닫고 있습니다.")
        finally:
            if workbook is not None:
                try:
                    workbook.Close(False)
                except Exception:
                    pass
            if app is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
            del workbook, app
            gc.collect()
