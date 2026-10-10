import subprocess
import sys
import threading
import xml.etree.ElementTree as ET
from pathlib import Path
from unittest.mock import Mock

import pytest

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, DependencyMissingError
from converters.pdf.libreoffice_to_pdf import LibreOfficeToPdfConverter


@pytest.fixture
def converter(tmp_path):
    executable = tmp_path / "soffice.com"
    executable.touch()
    return LibreOfficeToPdfConverter(AppSettings(libreoffice_path=str(executable)))


@pytest.mark.parametrize(
    ("extension", "export_filter"),
    [(".docx", "writer_pdf_Export"), (".xlsx", "calc_pdf_Export"), (".csv", "calc_pdf_Export"), (".pptx", "impress_pdf_Export")],
)
def test_conversion_uses_isolated_profile_and_copies_pdf(converter, tmp_path, monkeypatch, extension, export_filter):
    source = tmp_path / ("한글 공백" + extension)
    source.write_bytes(b"document")
    target = tmp_path / "output" / "renamed.pdf"
    commands = []

    def run(command, cancel_event):
        commands.append(command)
        directory = Path(command[command.index("--outdir") + 1])
        (directory / (source.stem + ".pdf")).write_bytes(b"%PDF-1.7\ntest")
        return ""

    monkeypatch.setattr(converter, "_run", run)
    converter.convert(source, target, Mock(), threading.Event())
    assert target.read_bytes() == b"%PDF-1.7\ntest"
    command = commands[0]
    assert f"pdf:{export_filter}" in command
    assert str(source.resolve()) == command[-1]
    assert any(argument.startswith("-env:UserInstallation=file:") for argument in command)
    assert not Path(command[command.index("--outdir") + 1]).exists()
    assert source.read_bytes() == b"document"


def test_existing_pdf_is_not_mistaken_for_success(converter, tmp_path, monkeypatch):
    source = tmp_path / "document.docx"
    source.touch()
    target = tmp_path / "out.pdf"
    target.write_bytes(b"old result")
    monkeypatch.setattr(converter, "_run", Mock(return_value=""))
    with pytest.raises(ConversionError, match="PDF"):
        converter.convert(source, target, Mock(), threading.Event())
    assert target.read_bytes() == b"old result"


def test_invalid_pdf_is_rejected(converter, tmp_path, monkeypatch):
    source = tmp_path / "document.docx"
    source.touch()

    def run(command, cancel_event):
        directory = Path(command[command.index("--outdir") + 1])
        (directory / "document.pdf").write_bytes(b"not a PDF")
        return ""

    monkeypatch.setattr(converter, "_run", run)
    with pytest.raises(ConversionError, match="PDF"):
        converter.convert(source, tmp_path / "out.pdf", Mock(), threading.Event())
    assert not (tmp_path / "out.pdf").exists()


def test_pre_cancelled_conversion_does_not_start_process(converter, tmp_path, monkeypatch):
    source = tmp_path / "document.docx"
    source.touch()
    event = threading.Event()
    event.set()
    runner = Mock()
    monkeypatch.setattr(converter, "_run", runner)
    with pytest.raises(ConversionCancelled):
        converter.convert(source, tmp_path / "out.pdf", Mock(), event)
    runner.assert_not_called()


def test_missing_runtime_is_actionable(tmp_path):
    converter = LibreOfficeToPdfConverter(AppSettings(libreoffice_path=str(tmp_path / "missing.exe")))
    with pytest.raises(DependencyMissingError, match="libreOfficePath"):
        converter._find_executable()


def test_exe_path_prefers_console_launcher(tmp_path):
    exe = tmp_path / "soffice.exe"
    com = tmp_path / "soffice.com"
    exe.touch()
    com.touch()
    converter = LibreOfficeToPdfConverter(AppSettings(libreoffice_path=str(exe)))
    assert converter._find_executable() == com.resolve()


def test_hwp_requires_configured_profile(converter, tmp_path, monkeypatch):
    monkeypatch.delenv("POSID_LIBREOFFICE_HWP_PROFILE", raising=False)
    with pytest.raises(DependencyMissingError, match="H2Orestart"):
        converter._prepare_profile(tmp_path / "profile", True)


def test_hwp_profile_is_copied_and_macros_are_disabled(tmp_path):
    source = tmp_path / "hwp-profile"
    user = source / "user"
    user.mkdir(parents=True)
    config = user / "registrymodifications.xcu"
    original = '<oor:items xmlns:oor="http://openoffice.org/2001/registry"><item oor:path="/org.openoffice.Office.Common/Security/Scripting"><prop oor:name="MacroSecurityLevel"><value>0</value></prop></item></oor:items>'
    config.write_text(original, encoding="utf-8")
    converter = LibreOfficeToPdfConverter(AppSettings(libreoffice_hwp_profile=str(source)))
    profile = tmp_path / "isolated"
    converter._prepare_profile(profile, True)
    assert config.read_text(encoding="utf-8") == original
    root = ET.parse(profile / "user" / "registrymodifications.xcu").getroot()
    properties = {prop.get("{http://openoffice.org/2001/registry}name"): prop.findtext("value") for prop in root.iter("prop")}
    assert properties["MacroSecurityLevel"] == "3"
    assert properties["DisableMacrosExecution"] == "true"


def test_locked_hwp_profile_is_not_used(tmp_path):
    source = tmp_path / "hwp-profile"
    (source / "user").mkdir(parents=True)
    (source / ".lock").touch()
    converter = LibreOfficeToPdfConverter(AppSettings(libreoffice_hwp_profile=str(source)))
    with pytest.raises(ConversionError, match="사용 중"):
        converter._prepare_profile(tmp_path / "isolated", True)


@pytest.mark.parametrize("extension", [".hwp", ".hwpx"])
def test_hwp_extension_is_checked_before_conversion(tmp_path, monkeypatch, extension):
    executable = tmp_path / "soffice.com"
    executable.touch()
    (tmp_path / ("unopkg.com" if sys.platform == "win32" else "unopkg")).touch()
    profile = tmp_path / "hwp-profile"
    (profile / "user").mkdir(parents=True)
    converter = LibreOfficeToPdfConverter(AppSettings(libreoffice_path=str(executable), libreoffice_hwp_profile=str(profile)))
    source = tmp_path / ("document" + extension)
    source.touch()
    runner = Mock(return_value="no extensions")
    monkeypatch.setattr(converter, "_run", runner)
    with pytest.raises(DependencyMissingError, match="H2Orestart"):
        converter.convert(source, tmp_path / "out.pdf", Mock(), threading.Event())
    assert runner.call_count == 1
    assert "list" in runner.call_args.args[0]


@pytest.mark.parametrize("extension", [".hwp", ".hwpx"])
def test_hwp_uses_registered_extension_filter(tmp_path, monkeypatch, extension):
    executable = tmp_path / "soffice.com"
    executable.touch()
    (tmp_path / ("unopkg.com" if sys.platform == "win32" else "unopkg")).touch()
    profile = tmp_path / "hwp-profile"
    (profile / "user").mkdir(parents=True)
    converter = LibreOfficeToPdfConverter(AppSettings(libreoffice_path=str(executable), libreoffice_hwp_profile=str(profile)))
    source = tmp_path / ("document" + extension)
    source.touch()
    commands = []

    def run(command, cancel_event):
        commands.append(command)
        if "list" in command:
            return "Identifier: ebandal.libreoffice.H2Orestart"
        directory = Path(command[command.index("--outdir") + 1])
        (directory / "document.pdf").write_bytes(b"%PDF-1.7\ntest")
        return ""

    monkeypatch.setattr(converter, "_run", run)
    target = tmp_path / "out.pdf"
    converter.convert(source, target, Mock(), threading.Event())
    assert len(commands) == 2
    assert "--infilter=Hwp2002_Reader" in commands[1]
    assert target.read_bytes().startswith(b"%PDF-")


def test_process_failure_is_reported(converter):
    with pytest.raises(ConversionError, match="LibreOffice"):
        converter._run([sys.executable, "-c", "raise SystemExit(2)"], threading.Event())


def test_process_timeout_terminates_process(converter, monkeypatch):
    monkeypatch.setattr(converter, "PROCESS_TIMEOUT", 0.1)
    original_popen = subprocess.Popen
    children = []

    def popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        if "-c" in args[0]:
            children.append(process)
        return process

    monkeypatch.setattr("converters.pdf.libreoffice_to_pdf.subprocess.Popen", popen)
    with pytest.raises(ConversionError, match="120"):
        converter._run([sys.executable, "-c", "import time; time.sleep(30)"], threading.Event())
    assert len(children) == 1
    assert children[0].poll() is not None


def test_process_cancellation_terminates_process(converter, monkeypatch):
    event = threading.Event()
    original_popen = subprocess.Popen
    children = []

    def popen(*args, **kwargs):
        process = original_popen(*args, **kwargs)
        if "-c" in args[0]:
            children.append(process)
            event.set()
        return process

    monkeypatch.setattr("converters.pdf.libreoffice_to_pdf.subprocess.Popen", popen)
    with pytest.raises(ConversionCancelled):
        converter._run([sys.executable, "-c", "import time; time.sleep(30)"], event)
    assert len(children) == 1
    assert children[0].poll() is not None


def test_fallback_settings_load(tmp_path):
    config = tmp_path / "appsettings.json"
    config.write_text('{"libreOfficePath": "C:/LO/soffice.com", "libreOfficeHwpProfile": "C:/Profiles/HWP"}')
    settings = AppSettings.load(config)
    assert settings.libreoffice_path == "C:/LO/soffice.com"
    assert settings.libreoffice_hwp_profile == "C:/Profiles/HWP"
