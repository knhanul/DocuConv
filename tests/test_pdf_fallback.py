import sys
import threading
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from backend.file_types import target_extensions
from backend.settings import AppSettings
from converters.base import ConversionError, DependencyMissingError, UnsupportedFormatError
from converters.registry import ConverterRegistry, is_com_application_installed


@pytest.mark.parametrize(
    ("extension", "attribute", "progid"),
    [
        (".hwp", "_hwp_to_pdf", "HWPFrame.HwpObject"),
        (".hwpx", "_hwp_to_pdf", "HWPFrame.HwpObject"),
        (".docx", "_word_to_pdf", "Word.Application"),
        (".xlsx", "_excel_to_pdf", "Excel.Application"),
        (".pptx", "_powerpoint_to_pdf", "PowerPoint.Application"),
    ],
)
def test_native_application_preferred(monkeypatch, extension, attribute, progid):
    registry = ConverterRegistry(AppSettings())
    native = Mock()
    fallback = Mock()
    detector = Mock(return_value=True)
    setattr(registry, attribute, native)
    registry._libreoffice_to_pdf = fallback
    monkeypatch.setattr("converters.registry.is_com_application_installed", detector)
    args = (Path("document" + extension), Path("out.pdf"), Mock(), threading.Event())
    registry.convert_to_pdf(*args)
    detector.assert_called_once_with(progid)
    native.convert.assert_called_once_with(*args)
    fallback.convert.assert_not_called()


@pytest.mark.parametrize("extension", [".hwp", ".hwpx", ".docx", ".xlsx", ".pptx", ".csv"])
def test_missing_application_uses_fallback(monkeypatch, extension):
    registry = ConverterRegistry(AppSettings())
    fallback = Mock()
    registry._libreoffice_to_pdf = fallback
    monkeypatch.setattr("converters.registry.is_com_application_installed", lambda _: False)
    args = (Path("document" + extension), Path("out.pdf"), Mock(), threading.Event())
    registry.convert_to_pdf(*args)
    fallback.convert.assert_called_once_with(*args)


@pytest.mark.parametrize("extension", [".hwp", ".hwpx", ".docx", ".xlsx", ".pptx"])
def test_libreoffice_option_skips_native_application(monkeypatch, extension):
    registry = ConverterRegistry(AppSettings(prefer_libreoffice_pdf=True))
    registry._libreoffice_to_pdf = Mock()
    for name in ("_hwp_to_pdf", "_word_to_pdf", "_excel_to_pdf", "_powerpoint_to_pdf"):
        setattr(registry, name, Mock())
    detector = Mock(return_value=True)
    monkeypatch.setattr("converters.registry.is_com_application_installed", detector)
    args = (Path("document" + extension), Path("out.pdf"), Mock(), threading.Event())
    registry.convert_to_pdf(*args)
    registry._libreoffice_to_pdf.convert.assert_called_once_with(*args)
    detector.assert_not_called()
    for name in ("_hwp_to_pdf", "_word_to_pdf", "_excel_to_pdf", "_powerpoint_to_pdf"):
        getattr(registry, name).convert.assert_not_called()


def test_libreoffice_option_does_not_open_native_when_missing(monkeypatch):
    registry = ConverterRegistry(AppSettings(prefer_libreoffice_pdf=True))
    registry._libreoffice_to_pdf = Mock()
    registry._libreoffice_to_pdf.convert.side_effect = DependencyMissingError("LibreOffice가 없습니다")
    registry._excel_to_pdf = Mock()
    detector = Mock(return_value=True)
    monkeypatch.setattr("converters.registry.is_com_application_installed", detector)
    with pytest.raises(DependencyMissingError, match="LibreOffice"):
        registry.convert_to_pdf(Path("document.xlsx"), Path("out.pdf"), Mock(), threading.Event())
    registry._excel_to_pdf.convert.assert_not_called()
    detector.assert_not_called()


def test_registered_but_unavailable_application_uses_fallback(monkeypatch):
    registry = ConverterRegistry(AppSettings())
    registry._word_to_pdf = Mock()
    registry._word_to_pdf.convert.side_effect = DependencyMissingError("unavailable")
    registry._libreoffice_to_pdf = Mock()
    monkeypatch.setattr("converters.registry.is_com_application_installed", lambda _: True)
    args = (Path("document.docx"), Path("out.pdf"), Mock(), threading.Event())
    registry.convert_to_pdf(*args)
    registry._libreoffice_to_pdf.convert.assert_called_once_with(*args)


def test_document_errors_do_not_use_fallback(monkeypatch):
    registry = ConverterRegistry(AppSettings())
    registry._word_to_pdf = Mock()
    registry._word_to_pdf.convert.side_effect = ConversionError("invalid document")
    registry._libreoffice_to_pdf = Mock()
    monkeypatch.setattr("converters.registry.is_com_application_installed", lambda _: True)
    with pytest.raises(ConversionError, match="invalid document"):
        registry.convert_to_pdf(Path("document.docx"), Path("out.pdf"), Mock(), threading.Event())
    registry._libreoffice_to_pdf.convert.assert_not_called()


def test_unsupported_format_does_not_use_fallback():
    registry = ConverterRegistry(AppSettings())
    registry._libreoffice_to_pdf = Mock()
    with pytest.raises(UnsupportedFormatError):
        registry.convert_to_pdf(Path("document.zip"), Path("out.pdf"), Mock(), threading.Event())
    registry._libreoffice_to_pdf.convert.assert_not_called()


def test_image_mode_accepts_only_pdf():
    assert target_extensions("image") == {".pdf"}


def test_image_conversion_rejects_documents(tmp_path):
    from converters.image.document_to_image import DocumentToImageConverter

    document = tmp_path / "a.docx"
    document.touch()
    converter = DocumentToImageConverter(AppSettings())
    with pytest.raises(ConversionError, match="PDF"):
        converter.convert(document, tmp_path / "out", "png", Mock(), threading.Event())


def test_image_job_does_not_touch_pdf_fallback():
    registry = ConverterRegistry(AppSettings())
    registry._image = Mock()
    registry._libreoffice_to_pdf = Mock()
    job = SimpleNamespace(mode="image", input_path=Path("a.pdf"), output_path=Path("out"), image_format="png")
    progress = Mock()
    event = threading.Event()
    registry.convert(job, progress, event)
    registry._image.convert.assert_called_once_with(job.input_path, job.output_path, "png", progress, event)
    registry._libreoffice_to_pdf.convert.assert_not_called()


@pytest.mark.parametrize("registered_view", [64, 32, None])
def test_com_detection_checks_both_registry_views(monkeypatch, registered_view):
    key = MagicMock()
    key.__enter__.return_value = key
    calls = []

    def open_key(root, path, reserved, access):
        calls.append((path, access))
        if access != registered_view:
            raise FileNotFoundError(path)
        return key

    fake_registry = SimpleNamespace(
        HKEY_CLASSES_ROOT=0, KEY_READ=0, KEY_WOW64_64KEY=64, KEY_WOW64_32KEY=32,
        OpenKey=open_key, QueryValueEx=Mock(side_effect=[("{CLSID}", 1), ("application.exe", 1)]),
    )
    monkeypatch.setitem(sys.modules, "winreg", fake_registry)
    monkeypatch.setattr("converters.registry.sys", SimpleNamespace(platform="win32"))
    assert is_com_application_installed("Word.Application") is (registered_view is not None)
    assert calls[0] == ("Word.Application\\CLSID", 64)
    if registered_view != 64:
        assert ("Word.Application\\CLSID", 32) in calls
    if registered_view is not None:
        assert ("CLSID\\{CLSID}\\LocalServer32", registered_view) in calls


def test_com_detection_is_unavailable_outside_windows(monkeypatch):
    monkeypatch.setattr("converters.registry.sys", SimpleNamespace(platform="linux"))
    assert not is_com_application_installed("Word.Application")


def test_hwpx_conversion_remains_native_only():
    registry = ConverterRegistry(AppSettings())
    registry._hwp_to_hwpx = Mock()
    registry._libreoffice_to_pdf = Mock()
    job = SimpleNamespace(mode="hwpx", input_path=Path("document.hwp"), output_path=Path("out.hwpx"))
    progress = Mock()
    event = threading.Event()
    registry.convert(job, progress, event)
    registry._hwp_to_hwpx.convert.assert_called_once_with(job.input_path, job.output_path, progress, event)
    registry._libreoffice_to_pdf.convert.assert_not_called()
