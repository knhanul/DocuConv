from __future__ import annotations

import gc
import logging
import platform
import sys
import threading
import time
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, DependencyMissingError, ProgressCallback, require_input_file, require_windows

logger = logging.getLogger(__name__)

_SECURITY_MODULE_NAME = "FilePathCheckerModuleExample"
_SECURITY_MODULE_DLL = "FilePathCheckerModuleExample.dll"
_REGISTRY_PATH = r"SOFTWARE\HNC\HwpAutomation\Modules"


class HwpAutomationManager:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings
        self._hwp = None
        self._started = False
        self._security_registered = False

    def start(self) -> None:
        if self._started:
            return
        logger.info("[HWP] Automation starting (Python %s-bit)", platform.architecture()[0])
        try:
            import win32com.client
        except ImportError as exc:
            raise DependencyMissingError("pywin32가 설치되어 있지 않습니다.") from exc

        try:
            self._hwp = win32com.client.DispatchEx("HWPFrame.HwpObject")
        except Exception as exc:
            logger.error("[HWP] COM creation failed: %s", exc)
            raise DependencyMissingError(
                "한글 프로그램을 실행할 수 없습니다. 한컴오피스 한글 설치 여부를 확인해 주세요."
            ) from exc

        try:
            version = self._hwp.Version
            logger.info("[HWP] HWP version: %s", version)
        except Exception:
            logger.info("[HWP] HWP version: unknown")

        try:
            self._register_security_module()
        except Exception:
            self.shutdown()
            raise

        try:
            self._hwp.XHwpWindows.Item(0).Visible = self._settings.hwp_visible
        except Exception:
            pass

        try:
            self._hwp.SetMessageBoxMode(0)
        except Exception:
            pass

        self._started = True
        logger.info("[HWP] Automation started successfully")

    def _register_security_module(self) -> None:
        self._security_registered = False
        module_name = self._settings.hwp_security_module_name.strip() or _SECURITY_MODULE_NAME
        if module_name == _SECURITY_MODULE_NAME:
            dll_path = self._find_security_dll()
            if dll_path is None:
                raise DependencyMissingError(
                    f"한글 보안 모듈 DLL을 찾을 수 없습니다: {_SECURITY_MODULE_DLL}. "
                    "배포 파일의 assets 폴더와 보안 모듈 포함 여부를 확인해 주세요. 문서 열기를 중단합니다."
                )
            self._ensure_registry_entry(module_name, str(dll_path.resolve()))

        message = (
            f"한글 보안 모듈 등록에 실패했습니다: {module_name} "
            f"(유형: {self._settings.hwp_security_module_type}). "
            "문서 열기를 중단합니다. 한글 버전과 호환되는 보안 모듈 DLL, "
            "레지스트리 등록 경로 및 appsettings.json의 모듈 설정을 확인해 주세요."
        )
        try:
            result = self._hwp.RegisterModule(self._settings.hwp_security_module_type, module_name)
        except Exception as exc:
            logger.exception("[HWP] RegisterModule exception: type=%s module=%s",
                             self._settings.hwp_security_module_type, module_name)
            raise DependencyMissingError(f"{message} 오류: {exc}") from exc
        if not result:
            logger.error("[HWP] RegisterModule failed: type=%s module=%s result=%r",
                         self._settings.hwp_security_module_type, module_name, result)
            raise DependencyMissingError(message)
        self._security_registered = True
        logger.info("[HWP] RegisterModule success: type=%s module=%s",
                    self._settings.hwp_security_module_type, module_name)

    def _find_security_dll(self) -> Path | None:
        candidates = [
            Path(__file__).resolve().parent.parent.parent / "assets" / _SECURITY_MODULE_DLL,
        ]
        if getattr(sys, "frozen", False) and hasattr(sys, "_MEIPASS"):
            candidates.append(Path(sys._MEIPASS) / "assets" / _SECURITY_MODULE_DLL)
        for p in candidates:
            if p.is_file():
                logger.info("[HWP] Security DLL found: %s", p)
                return p
        logger.warning("[HWP] Security DLL not found in any candidate location")
        return None

    def _ensure_registry_entry(self, module_name: str, dll_path: str) -> None:
        try:
            import winreg

            existing = None
            try:
                with winreg.OpenKey(winreg.HKEY_CURRENT_USER, _REGISTRY_PATH, 0, winreg.KEY_READ) as key:
                    existing, _ = winreg.QueryValueEx(key, module_name)
            except FileNotFoundError:
                pass
            if existing == dll_path:
                logger.info("[HWP] Registry entry already correct: %s = %s", module_name, dll_path)
                return

            with winreg.CreateKeyEx(winreg.HKEY_CURRENT_USER, _REGISTRY_PATH, 0, winreg.KEY_SET_VALUE) as key:
                winreg.SetValueEx(key, module_name, 0, winreg.REG_SZ, dll_path)
            logger.info("[HWP] Registry entry registered: %s = %s", module_name, dll_path)
        except OSError as exc:
            logger.exception("[HWP] Registry registration failed: key=HKCU\\%s module=%s dll=%s",
                             _REGISTRY_PATH, module_name, dll_path)
            raise DependencyMissingError(
                f"한글 보안 모듈의 레지스트리 등록에 실패했습니다: {module_name}. "
                f"HKCU\\{_REGISTRY_PATH} 경로의 쓰기 권한과 보안 정책을 확인해 주세요. 오류: {exc}"
            ) from exc

    def open_document(self, input_path: Path) -> None:
        self._ensure_started()
        logger.info("[HWP] Open: %s", input_path)
        opened = False
        for attempt in range(3):
            try:
                opened = self._hwp.Open(str(input_path.resolve()), "", "")
                break
            except Exception as exc:
                logger.warning("[HWP] Open attempt %d failed: %s", attempt + 1, exc)
                if attempt < 2:
                    time.sleep(1)
                    if not self._is_alive():
                        logger.info("[HWP] COM object died, restarting...")
                        self._restart()
                else:
                    raise
        if opened is False:
            raise ConversionError(f"한글 문서를 열지 못했습니다: {input_path.name}")
        logger.info("[HWP] Open success: %s", input_path.name)

    def save_as(self, output_path: Path, format_name: str) -> None:
        self._ensure_started()
        logger.info("[HWP] SaveAs: %s -> %s", format_name, output_path)
        result = self._hwp.SaveAs(str(output_path.resolve()), format_name, "")
        if result is False or not output_path.exists():
            raise ConversionError(f"{format_name} 파일 저장에 실패했습니다.")
        logger.info("[HWP] SaveAs success: %s", output_path.name)

    def close_document(self) -> None:
        if self._hwp is None:
            return
        try:
            self._hwp.Clear(1)
            logger.info("[HWP] Document closed")
        except Exception as exc:
            logger.warning("[HWP] Close failed: %s", exc)

    def is_security_registered(self) -> bool:
        return self._security_registered

    def shutdown(self) -> None:
        if self._hwp is not None:
            logger.info("[HWP] Shutting down Automation")
            try:
                self._hwp.Clear(1)
            except Exception:
                pass
            try:
                self._hwp.Quit()
            except Exception:
                pass
            del self._hwp
            self._hwp = None
            gc.collect()
            logger.info("[HWP] Automation shut down")
        self._started = False
        self._security_registered = False

    def _ensure_started(self) -> None:
        if not self._started or self._hwp is None:
            self.start()

    def _is_alive(self) -> bool:
        if self._hwp is None:
            return False
        try:
            _ = self._hwp.Version
            return True
        except Exception:
            return False

    def _restart(self) -> None:
        logger.info("[HWP] Restarting Automation")
        self.shutdown()
        self.start()

    def convert(
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

        output_path.parent.mkdir(parents=True, exist_ok=True)

        progress(10, "한글 프로그램을 준비하고 있습니다.")
        self._ensure_started()

        if cancel_event.is_set():
            raise ConversionCancelled("변환이 취소되었습니다.")

        progress(30, "한글 문서를 열고 있습니다.")
        self.open_document(input_path)

        if cancel_event.is_set():
            raise ConversionCancelled("변환이 취소되었습니다.")

        progress(70, f"{format_name} 형식으로 저장하고 있습니다.")
        self.save_as(output_path, format_name)

        progress(95, "한글 문서를 닫고 있습니다.")
        self.close_document()
