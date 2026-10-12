from pathlib import Path

from PySide6.QtCore import QFileInfo, QSize, QStandardPaths, QUrl
from PySide6.QtGui import QIcon
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QFileIconProvider


DOCUMENT_ICONS = {
    **dict.fromkeys({"hwp", "hwpx"}, "hwp"),
    **dict.fromkeys({"doc", "docx", "docm", "dot", "dotx", "rtf", "odt"}, "word"),
    **dict.fromkeys({"xls", "xlsx", "xlsm", "xlsb", "csv"}, "excel"),
    **dict.fromkeys({"ppt", "pptx", "pptm", "pps", "ppsx"}, "powerpoint"),
    "pdf": "pdf",
}


class FileIconProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Pixmap)
        self._provider = QFileIconProvider()
        self._provider.setOptions(QFileIconProvider.Option.DontUseCustomDirectoryIcons)
        self._cache: dict[tuple[str, int, int], object] = {}

    def requestPixmap(self, identifier, size, requested_size):
        dimensions = requested_size if requested_size.isValid() else QSize(24, 24)
        key = (identifier, dimensions.width(), dimensions.height())
        pixmap = self._cache.get(key)
        if pixmap is None:
            pixmap = self._icon_for(identifier).pixmap(dimensions)
            self._cache[key] = pixmap
        size.setWidth(pixmap.width())
        size.setHeight(pixmap.height())
        return pixmap

    def _icon_for(self, identifier):
        if identifier.startswith("document/"):
            extension = identifier[len("document/"):].lower()
            icon_name = DOCUMENT_ICONS.get(extension, "pdf")
            icon_path = Path(__file__).resolve().parent.parent / "assets" / f"icon_{icon_name}.svg"
            return QIcon(str(icon_path))
        if identifier.startswith("file/"):
            raw = identifier[len("file/"):]
            path = QUrl.fromPercentEncoding(raw.encode("utf-8"))
            if not Path(path).exists():
                path = raw
            return self._provider.icon(QFileInfo(path))
        locations = {
            "desktop": QStandardPaths.StandardLocation.DesktopLocation,
            "downloads": QStandardPaths.StandardLocation.DownloadLocation,
            "documents": QStandardPaths.StandardLocation.DocumentsLocation,
        }
        if identifier in locations:
            return self._provider.icon(QFileInfo(QStandardPaths.writableLocation(locations[identifier])))
        icon_type = QFileIconProvider.IconType.Drive if identifier == "drive" else QFileIconProvider.IconType.Folder
        return self._provider.icon(icon_type)
