from __future__ import annotations

import os
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtWidgets import QApplication

from backend.app_controller import AppController
from backend.file_icon_provider import FileIconProvider
from backend.version import APP_VERSION

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).resolve().parent


def configure_qt_environment() -> None:
    # Qt Quick 렌더링 문제가 있는 구형/가상 Windows 환경에서 아래 값을
    # "software"로 바꾸면 소프트웨어 렌더링을 강제할 수 있습니다.
    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == "win32" else "opengl")


def main() -> int:
    configure_qt_environment()

    QCoreApplication.setOrganizationName("POSID")
    QCoreApplication.setOrganizationDomain("posid.co.kr")
    QCoreApplication.setApplicationName("POSID Document Converter")
    QCoreApplication.setApplicationVersion(APP_VERSION)

    app = QApplication(sys.argv)
    app.setQuitOnLastWindowClosed(True)
    app.setWindowIcon(QIcon(str(APP_DIR / "assets" / "posid_logo.ico")))

    engine = QQmlApplicationEngine()
    engine.addImageProvider("filesystem", FileIconProvider())
    controller = AppController(app_dir=APP_DIR)
    engine.rootContext().setContextProperty("appController", controller)

    qml_file = APP_DIR / "qml" / "Main.qml"
    engine.load(QUrl.fromLocalFile(str(qml_file)))
    if not engine.rootObjects():
        return 1

    exit_code = app.exec()
    controller.shutdown()
    del engine
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
