from __future__ import annotations

import gc
import threading
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, DependencyMissingError, ProgressCallback, require_input_file, require_windows


class WordToPdfConverter:
    WD_EXPORT_FORMAT_PDF = 17

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def convert(self, input_path: Path, output_path: Path, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        require_windows("Word PDF 변환")
        require_input_file(input_path)
        try:
            import win32com.client
        except ImportError as exc:
            raise DependencyMissingError("pywin32가 설치되어 있지 않습니다.") from exc

        app = None
        document = None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            progress(10, "Microsoft Word를 실행하고 있습니다.")
            try:
                app = win32com.client.DispatchEx("Word.Application")
            except Exception as exc:
                raise DependencyMissingError("Microsoft Word 데스크톱 앱을 실행할 수 없습니다.") from exc
            app.Visible = self._settings.office_visible
            app.DisplayAlerts = 0
            progress(35, "Word 문서를 열고 있습니다.")
            document = app.Documents.Open(str(input_path.resolve()), ReadOnly=True, AddToRecentFiles=False)
            if cancel_event.is_set():
                raise ConversionCancelled("변환이 취소되었습니다.")
            progress(75, "Word 문서를 PDF로 내보내고 있습니다.")
            document.ExportAsFixedFormat(str(output_path.resolve()), self.WD_EXPORT_FORMAT_PDF)
            if not output_path.exists():
                raise ConversionError("Word PDF 파일이 생성되지 않았습니다.")
            progress(95, "Word 문서를 닫고 있습니다.")
        finally:
            if document is not None:
                try:
                    document.Close(False)
                except Exception:
                    pass
            if app is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
            del document, app
            gc.collect()
