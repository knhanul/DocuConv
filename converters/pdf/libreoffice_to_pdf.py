from __future__ import annotations

import os
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import xml.etree.ElementTree as ET
from pathlib import Path

from backend.file_types import EXCEL_EXTENSIONS, HWP_EXTENSIONS, POWERPOINT_EXTENSIONS
from backend.settings import AppSettings
from converters.base import (
    ConversionCancelled,
    ConversionError,
    DependencyMissingError,
    ProgressCallback,
    require_input_file,
)


class LibreOfficeToPdfConverter:
    PROCESS_TIMEOUT = 120

    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def _find_executable(self) -> Path:
        configured = self._settings.libreoffice_path or os.environ.get("POSID_LIBREOFFICE_PATH", "")
        candidates = [Path(os.path.expandvars(configured)).expanduser()] if configured else []
        if not configured:
            for name in ("soffice.com", "soffice", "soffice.exe"):
                found = shutil.which(name)
                if found:
                    candidates.append(Path(found))
            for variable in ("ProgramW6432", "ProgramFiles", "ProgramFiles(x86)"):
                root = os.environ.get(variable)
                if root:
                    candidates.append(Path(root) / "LibreOffice" / "program" / "soffice.com")
        for candidate in candidates:
            if candidate.suffix.lower() == ".exe" and candidate.with_suffix(".com").is_file():
                candidate = candidate.with_suffix(".com")
            if candidate.is_file():
                return candidate.resolve()
        raise DependencyMissingError(
            "원본 문서 프로그램을 사용할 수 없고 LibreOffice도 찾지 못했습니다. "
            "LibreOffice를 설치하거나 libreOfficePath에 soffice 실행 파일 경로를 지정해 주세요."
        )

    def _prepare_profile(self, profile: Path, is_hwp: bool) -> None:
        if is_hwp:
            configured = self._settings.libreoffice_hwp_profile or os.environ.get("POSID_LIBREOFFICE_HWP_PROFILE", "")
            if not configured:
                raise DependencyMissingError(
                    "한글 미설치 환경의 HWP/HWPX 변환에는 LibreOffice + H2Orestart + Java가 필요합니다. "
                    "H2Orestart와 Java를 설정한 전용 프로필을 libreOfficeHwpProfile에 지정해 주세요."
                )
            source = Path(os.path.expandvars(configured)).expanduser().resolve()
            if not (source / "user").is_dir():
                raise DependencyMissingError("libreOfficeHwpProfile에는 user 폴더를 포함하는 LibreOffice 프로필 경로를 지정해 주세요.")
            if (source / ".lock").exists():
                raise ConversionError("HWP 대체 변환용 LibreOffice 프로필이 사용 중입니다. 해당 LibreOffice를 닫고 다시 시도해 주세요.")
            shutil.copytree(source, profile)
        user = profile / "user"
        user.mkdir(parents=True, exist_ok=True)
        config = user / "registrymodifications.xcu"
        namespace = "http://openoffice.org/2001/registry"
        root = ET.parse(config).getroot() if config.exists() else ET.Element(f"{{{namespace}}}items")
        property_names = {"MacroSecurityLevel", "DisableMacrosExecution"}
        for item in root.findall("item"):
            if item.get(f"{{{namespace}}}path") == "/org.openoffice.Office.Common/Security/Scripting":
                for prop in list(item):
                    if prop.get(f"{{{namespace}}}name") in property_names:
                        item.remove(prop)
        item = ET.SubElement(root, "item", {f"{{{namespace}}}path": "/org.openoffice.Office.Common/Security/Scripting"})
        for name, value in (("MacroSecurityLevel", "3"), ("DisableMacrosExecution", "true")):
            prop = ET.SubElement(item, "prop", {f"{{{namespace}}}name": name, f"{{{namespace}}}op": "fuse"})
            ET.SubElement(prop, "value").text = value
        ET.ElementTree(root).write(config, encoding="utf-8", xml_declaration=True)

    def _run(self, command: list[str], cancel_event: threading.Event) -> str:
        if cancel_event.is_set():
            raise ConversionCancelled("변환이 취소되었습니다.")
        flags = subprocess.CREATE_NO_WINDOW if sys.platform == "win32" else 0
        with tempfile.TemporaryFile() as log:
            process = subprocess.Popen(command, stdout=log, stderr=subprocess.STDOUT, creationflags=flags)
            deadline = time.monotonic() + self.PROCESS_TIMEOUT
            try:
                while process.poll() is None:
                    if cancel_event.wait(0.1):
                        raise ConversionCancelled("변환이 취소되었습니다.")
                    if time.monotonic() >= deadline:
                        raise ConversionError("LibreOffice 변환 제한 시간(120초)을 초과했습니다.")
            finally:
                if process.poll() is None:
                    try:
                        if sys.platform == "win32":
                            subprocess.run(
                                ["taskkill", "/PID", str(process.pid), "/T", "/F"],
                                stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, creationflags=flags, check=False, timeout=10,
                            )
                    finally:
                        if process.poll() is None:
                            process.kill()
                        process.wait(timeout=10)
            log.seek(0)
            output = log.read().decode("utf-8", errors="replace")
        if process.returncode:
            raise ConversionError("LibreOffice 실행에 실패했습니다. 런타임, 문서 형식 및 확장 설치 상태를 확인해 주세요.")
        return output

    def convert(self, input_path: Path, output_path: Path, progress: ProgressCallback, cancel_event: threading.Event) -> None:
        require_input_file(input_path)
        if cancel_event.is_set():
            raise ConversionCancelled("변환이 취소되었습니다.")
        executable = self._find_executable()
        extension = input_path.suffix.lower()
        is_hwp = extension in HWP_EXTENSIONS
        progress(10, "LibreOffice 대체 엔진을 준비하고 있습니다.")
        try:
            with tempfile.TemporaryDirectory(prefix="posid_libreoffice_") as temporary:
                workspace = Path(temporary)
                profile = workspace / "profile"
                self._prepare_profile(profile, is_hwp)
                profile_option = f"-env:UserInstallation={profile.as_uri()}"
                if is_hwp:
                    names = ("unopkg.com", "unopkg.exe") if sys.platform == "win32" else ("unopkg",)
                    unopkg = next((executable.parent / name for name in names if (executable.parent / name).is_file()), None)
                    if unopkg is None:
                        raise DependencyMissingError("LibreOffice의 unopkg 실행 파일을 찾지 못했습니다. 전체 LibreOffice 런타임이 필요합니다.")
                    extensions = self._run([str(unopkg), profile_option, "list"], cancel_event)
                    if "h2orestart" not in extensions.lower():
                        raise DependencyMissingError("대체 변환용 프로필에 H2Orestart 확장이 없습니다. 확장을 설치하고 Java를 설정해 주세요.")
                export_filter = "writer_pdf_Export"
                if extension in EXCEL_EXTENSIONS:
                    export_filter = "calc_pdf_Export"
                elif extension in POWERPOINT_EXTENSIONS:
                    export_filter = "impress_pdf_Export"
                progress(30, "LibreOffice로 문서를 PDF로 변환하고 있습니다.")
                self._run([
                    str(executable), profile_option, "--headless", "--nologo", "--nodefault", "--norestore",
                    *(["--infilter=Hwp2002_Reader"] if is_hwp else []),
                    "--convert-to", f"pdf:{export_filter}", "--outdir", str(workspace), str(input_path.resolve()),
                ], cancel_event)
                if cancel_event.is_set():
                    raise ConversionCancelled("변환이 취소되었습니다.")
                generated = workspace / f"{input_path.stem}.pdf"
                if not generated.is_file():
                    raise ConversionError(
                        "LibreOffice가 PDF를 생성하지 못했습니다. 문서 지원 여부를 확인해 주세요. "
                        "HWP/HWPX는 H2Orestart와 Java 설정도 확인해 주세요."
                    )
                with generated.open("rb") as pdf:
                    if pdf.read(5) != b"%PDF-":
                        raise ConversionError("LibreOffice 출력이 올바른 PDF가 아닙니다.")
                output_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copyfile(generated, output_path)
                progress(95, "LibreOffice PDF 변환을 완료했습니다.")
        except (OSError, ET.ParseError) as exc:
            raise ConversionError("LibreOffice 실행 파일, 프로필 또는 출력 경로를 확인해 주세요.") from exc
