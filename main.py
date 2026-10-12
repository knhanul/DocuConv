from __future__ import annotations

import logging
import os
import sys
from pathlib import Path

from PySide6.QtCore import QCoreApplication, QStandardPaths, QUrl
from PySide6.QtGui import QColor, QFont, QIcon, QPalette
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuickControls2 import QQuickStyle
from PySide6.QtWidgets import QApplication

from backend.app_controller import AppController
from backend.file_icon_provider import FileIconProvider
from backend.logging_config import setup_logging
from backend.version import APP_VERSION, BUILD_DATE

logger = logging.getLogger(__name__)

if getattr(sys, "frozen", False):
    APP_DIR = Path(sys._MEIPASS)
else:
    APP_DIR = Path(__file__).resolve().parent


def configure_qt_environment() -> None:
    # Qt Quick 렌더링 문제가 있는 구형/가상 Windows 환경에서 아래 값을
    # "software"로 바꾸면 소프트웨어 렌더링을 강제할 수 있습니다.
    os.environ.setdefault("QSG_RHI_BACKEND", "d3d11" if sys.platform == "win32" else "opengl")
    QQuickStyle.setStyle("Basic")


def apply_brand_palette(app: QApplication) -> None:
    palette = app.palette()

    def set_role(name: str, hex_color: str) -> None:
        role = getattr(QPalette.ColorRole, name, None)
        if role is None:
            return
        palette.setColor(role, QColor(hex_color))

    set_role("Window", "#F3F1EF")
    set_role("WindowText", "#1C1C1C")
    set_role("Base", "#FFFFFF")
    set_role("AlternateBase", "#F7F5F3")
    set_role("Text", "#1C1C1C")
    set_role("Button", "#FFFFFF")
    set_role("ButtonText", "#1C1C1C")
    set_role("Highlight", "#E22A26")
    set_role("HighlightedText", "#FFFFFF")
    set_role("Accent", "#E22A26")
    set_role("PlaceholderText", "#8B8E93")
    set_role("Mid", "#E7E2DC")
    app.setPalette(palette)
    app.setFont(QFont("Malgun Gothic", 10))


def main() -> int:
    configure_qt_environment()

    QCoreApplication.setOrganizationName("POSID")
    QCoreApplication.setOrganizationDomain("posid.co.kr")
    QCoreApplication.setApplicationName("POSID Document Converter")
    QCoreApplication.setApplicationVersion(APP_VERSION)

    app = QApplication(sys.argv)
    log_path = setup_logging(Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation)))
    logger.info("앱 시작: v%s (빌드 %s), 로그 파일: %s", APP_VERSION, BUILD_DATE, log_path)
    apply_brand_palette(app)
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
    logger.info("앱 종료: exit_code=%d", exit_code)
    controller.shutdown()
    del engine
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
