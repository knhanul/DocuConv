from pathlib import Path
from unittest.mock import Mock

from PySide6.QtWidgets import QApplication

from backend.job_model import ConversionJob
from backend.settings import AppSettings
from backend.worker import ConversionWorker
from converters.base import DependencyMissingError


def test_removed_settings_are_ignored(tmp_path):
    config = tmp_path / "appsettings.json"
    config.write_text('{"libreOfficePath": "C:/LO/soffice.com", "libreOfficeHwpProfile": "C:/Profiles/HWP"}')
    settings = AppSettings.load(config)
    assert not hasattr(settings, "libreoffice_path")
    assert not hasattr(settings, "libreoffice_hwp_profile")
    assert not hasattr(settings, "prefer_libreoffice_pdf")


def test_missing_program_is_reported_without_traceback_and_next_job_continues(monkeypatch, capsys):
    application = QApplication.instance() or QApplication([])
    jobs = [
        ConversionJob(Path("missing.docx"), Path("missing.pdf"), Path("."), "pdf"),
        ConversionJob(Path("available.xlsx"), Path("available.pdf"), Path("."), "pdf"),
    ]
    message = "Microsoft Word가 설치되어 있지 않습니다. Microsoft Word 설치가 필요합니다."
    registry = Mock()
    registry.convert.side_effect = [DependencyMissingError(message), None]
    monkeypatch.setattr("backend.worker.ConverterRegistry", Mock(return_value=registry))
    worker = ConversionWorker(jobs, AppSettings())
    updates = Mock()
    missing = Mock()
    finished = Mock()
    worker.jobChanged.connect(updates)
    worker.dependencyMissing.connect(missing)
    worker.jobFinished.connect(finished)
    worker.run()
    missing.assert_called_once_with(message)
    assert (jobs[0].id, "실패", 0, message) in [call.args for call in updates.call_args_list]
    assert (jobs[1].id, "완료", 100, "변환이 완료되었습니다.") in [call.args for call in updates.call_args_list]
    assert finished.call_count == 2
    assert registry.convert.call_count == 2
    registry.shutdown.assert_called_once()
    assert "Traceback" not in capsys.readouterr().err
    assert application is not None
