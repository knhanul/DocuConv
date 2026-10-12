import sys
import threading
from types import SimpleNamespace
from unittest.mock import MagicMock, Mock

import pytest

from backend.settings import AppSettings
from converters.base import DependencyMissingError
from converters.hwpx.hwp_automation import HwpAutomationManager


@pytest.fixture
def manager():
    return HwpAutomationManager(AppSettings())


@pytest.fixture
def registry(monkeypatch):
    key = MagicMock()
    key.__enter__.return_value = key
    registry = SimpleNamespace(
        HKEY_CURRENT_USER=1, KEY_READ=2, KEY_SET_VALUE=4, REG_SZ=1,
        OpenKey=Mock(return_value=key), CreateKeyEx=Mock(return_value=key),
        QueryValueEx=Mock(side_effect=FileNotFoundError("missing value")),
        SetValueEx=Mock(), CloseKey=Mock(),
    )
    monkeypatch.setitem(sys.modules, "winreg", registry)
    return registry


def test_missing_registry_key_is_created(manager, registry):
    registry.OpenKey.side_effect = FileNotFoundError("missing key")
    manager._ensure_registry_entry("module", "C:/module.dll")
    registry.CreateKeyEx.assert_called_once_with(1, r"SOFTWARE\HNC\HwpAutomation\Modules", 0, 4)
    registry.SetValueEx.assert_called_once_with(registry.CreateKeyEx.return_value, "module", 0, 1, "C:/module.dll")


def test_matching_registry_entry_is_not_rewritten(manager, registry):
    registry.QueryValueEx.side_effect = None
    registry.QueryValueEx.return_value = ("C:/module.dll", 1)
    manager._ensure_registry_entry("module", "C:/module.dll")
    registry.CreateKeyEx.assert_not_called()
    registry.SetValueEx.assert_not_called()


def test_previous_extraction_path_is_updated(manager, registry):
    registry.QueryValueEx.side_effect = None
    registry.QueryValueEx.return_value = ("C:/old-extraction/module.dll", 1)
    manager._ensure_registry_entry("module", "C:/new-extraction/module.dll")
    registry.SetValueEx.assert_called_once_with(registry.CreateKeyEx.return_value, "module", 0, 1, "C:/new-extraction/module.dll")


@pytest.mark.parametrize("operation", ["OpenKey", "CreateKeyEx", "SetValueEx"])
def test_registry_permission_error_is_reported(manager, registry, operation):
    getattr(registry, operation).side_effect = PermissionError("access denied")
    with pytest.raises(DependencyMissingError, match="보안 모듈.*등록"):
        manager._ensure_registry_entry("module", "C:/module.dll")


@pytest.mark.parametrize("result", [False, RuntimeError("COM failure")])
def test_registration_failure_stops_document_open(manager, monkeypatch, tmp_path, result):
    hwp = Mock()
    manager._hwp = hwp
    monkeypatch.setattr(manager, "_find_security_dll", Mock(return_value=tmp_path / "module.dll"))
    monkeypatch.setattr(manager, "_ensure_registry_entry", Mock())
    if isinstance(result, Exception):
        hwp.RegisterModule.side_effect = result
    else:
        hwp.RegisterModule.return_value = result
    with pytest.raises(DependencyMissingError, match="보안 모듈"):
        manager._register_security_module()
    assert not manager.is_security_registered()
    hwp.Open.assert_not_called()


def test_default_module_requires_bundled_dll(manager, monkeypatch):
    manager._hwp = Mock()
    monkeypatch.setattr(manager, "_find_security_dll", Mock(return_value=None))
    with pytest.raises(DependencyMissingError, match="DLL"):
        manager._register_security_module()
    manager._hwp.RegisterModule.assert_not_called()


def test_custom_module_is_not_overwritten_with_bundled_dll(monkeypatch):
    manager = HwpAutomationManager(AppSettings(hwp_security_module_name="CompanyModule"))
    manager._hwp = Mock()
    manager._hwp.RegisterModule.return_value = True
    registry_update = Mock()
    monkeypatch.setattr(manager, "_ensure_registry_entry", registry_update)
    manager._register_security_module()
    registry_update.assert_not_called()
    manager._hwp.RegisterModule.assert_called_once_with("FilePathCheckDLL", "CompanyModule")
    assert manager.is_security_registered()


def test_start_failure_releases_com_instance(manager, monkeypatch):
    hwp = Mock()
    client = SimpleNamespace(DispatchEx=Mock(return_value=hwp))
    monkeypatch.setitem(sys.modules, "win32com", SimpleNamespace(client=client))
    monkeypatch.setitem(sys.modules, "win32com.client", client)
    monkeypatch.setattr(manager, "_register_security_module", Mock(side_effect=DependencyMissingError("보안 모듈 오류")))
    with pytest.raises(DependencyMissingError, match="보안 모듈 오류"):
        manager.start()
    hwp.Quit.assert_called_once()
    hwp.Open.assert_not_called()
    assert manager._hwp is None
    assert not manager._started


@pytest.mark.parametrize("format_name", ["PDF", "HWPX"])
def test_conversion_never_opens_document_after_security_failure(manager, monkeypatch, tmp_path, format_name):
    hwp = Mock()
    hwp.RegisterModule.return_value = False
    client = SimpleNamespace(DispatchEx=Mock(return_value=hwp))
    monkeypatch.setitem(sys.modules, "win32com", SimpleNamespace(client=client))
    monkeypatch.setitem(sys.modules, "win32com.client", client)
    monkeypatch.setattr("converters.hwpx.hwp_automation.require_windows", Mock())
    monkeypatch.setattr(manager, "_find_security_dll", Mock(return_value=tmp_path / "module.dll"))
    monkeypatch.setattr(manager, "_ensure_registry_entry", Mock())
    source = tmp_path / "input.hwp"
    source.touch()
    progress = Mock()
    with pytest.raises(DependencyMissingError, match="문서 열기를 중단"):
        manager.convert(source, tmp_path / f"output.{format_name.lower()}", format_name, progress, threading.Event())
    assert [call.args[0] for call in progress.call_args_list] == [10]
    hwp.Open.assert_not_called()
    hwp.SaveAs.assert_not_called()
    hwp.Quit.assert_called_once()
    assert manager._hwp is None
    assert not manager._started
