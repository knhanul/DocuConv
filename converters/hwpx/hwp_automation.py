from __future__ import annotations

import gc
import threading
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, DependencyMissingError, ProgressCallback, require_input_file, require_windows


class HwpAutomation:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def save_as(
        self,
        input_path: Path,
        output_path: Path,
        format_name: str,
        progress: ProgressCallback,
        cancel_event: threading.Event,
    ) -> None:
        require_windows("한글 문서 변환")
        require_input_file(input_path)
        if cancel_event.is_set():
            raise ConversionCancelled("변환이 취소되었습니다.")

        try:
            import win32com.client
        except ImportError as exc:
            raise DependencyMissingError("pywin32가 설치되어 있지 않습니다.") from exc

        hwp = None
        output_path.parent.mkdir(parents=True, exist_ok=True)
        try:
            progress(10, "한글 프로그램을 실행하고 있습니다.")
            try:
                hwp = win32com.client.DispatchEx("HWPFrame.HwpObject")
            except Exception as exc:
                raise DependencyMissingError(
                    "한글 프로그램을 실행할 수 없습니다. 한컴오피스 한글 설치 여부를 확인해 주세요."
                ) from exc

            module_name = self._settings.hwp_security_module_name.strip()
            if module_name:
                registered = hwp.RegisterModule(self._settings.hwp_security_module_type, module_name)
                if registered is False:
                    raise ConversionError("한글 파일 경로 보안 모듈을 등록하지 못했습니다.")

            try:
                hwp.XHwpWindows.Item(0).Visible = self._settings.hwp_visible
            except Exception:
                pass

            progress(30, "한글 문서를 열고 있습니다.")
            opened = hwp.Open(str(input_path.resolve()))
            if opened is False:
                raise ConversionError(f"한글 문서를 열지 못했습니다: {input_path.name}")

            if cancel_event.is_set():
                raise ConversionCancelled("변환이 취소되었습니다.")

            progress(70, f"{format_name} 형식으로 저장하고 있습니다.")
            result = hwp.SaveAs(str(output_path.resolve()), format_name, "")
            if result is False or not output_path.exists():
                raise ConversionError(f"{format_name} 파일 저장에 실패했습니다.")
            progress(95, "한글 문서를 닫고 있습니다.")
        finally:
            if hwp is not None:
                try:
                    hwp.Clear(1)
                except Exception:
                    pass
                try:
                    hwp.Quit()
                except Exception:
                    pass
                del hwp
                gc.collect()
