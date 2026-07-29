from __future__ import annotations

import gc
import threading
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, DependencyMissingError, ProgressCallback, require_input_file, require_windows


class PowerPointToPdfConverter:
    PP_SAVE_AS_PDF = 32

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def convert(self, input_path: Path, output_path: Path, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        require_windows("PowerPoint PDF 변환")
        require_input_file(input_path)
        try:
            import win32com.client
        except ImportError as exc:
            raise DependencyMissingError("pywin32가 설치되어 있지 않습니다.") from exc

        app = None
        presentation = None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            progress(10, "Microsoft PowerPoint를 실행하고 있습니다.")
            try:
                app = win32com.client.DispatchEx("PowerPoint.Application")
            except Exception as exc:
                raise DependencyMissingError("Microsoft PowerPoint 데스크톱 앱을 실행할 수 없습니다.") from exc
            if self._settings.office_visible:
                app.Visible = True
            progress(35, "PowerPoint 문서를 열고 있습니다.")
            presentation = app.Presentations.Open(str(input_path.resolve()), ReadOnly=True, Untitled=False, WithWindow=False)
            if cancel_event.is_set():
                raise ConversionCancelled("변환이 취소되었습니다.")
            progress(75, "PowerPoint 문서를 PDF로 저장하고 있습니다.")
            presentation.SaveAs(str(output_path.resolve()), self.PP_SAVE_AS_PDF)
            if not output_path.exists():
                raise ConversionError("PowerPoint PDF 파일이 생성되지 않았습니다.")
            progress(95, "PowerPoint 문서를 닫고 있습니다.")
        finally:
            if presentation is not None:
                try:
                    presentation.Close()
                except Exception:
                    pass
            if app is not None:
                try:
                    app.Quit()
                except Exception:
                    pass
            del presentation, app
            gc.collect()
