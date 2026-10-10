from PySide6.QtCore import QFileInfo, QSize, QStandardPaths
from PySide6.QtQuick import QQuickImageProvider
from PySide6.QtWidgets import QFileIconProvider


class FileIconProvider(QQuickImageProvider):
    def __init__(self) -> None:
        super().__init__(QQuickImageProvider.ImageType.Pixmap)
        self._provider = QFileIconProvider()
        self._provider.setOptions(QFileIconProvider.Option.DontUseCustomDirectoryIcons)

    def requestPixmap(self, identifier, size, requested_size):
        locations = {
            "desktop": QStandardPaths.StandardLocation.DesktopLocation,
            "downloads": QStandardPaths.StandardLocation.DownloadLocation,
            "documents": QStandardPaths.StandardLocation.DocumentsLocation,
        }
        if identifier in locations:
            icon = self._provider.icon(QFileInfo(QStandardPaths.writableLocation(locations[identifier])))
        else:
            icon_type = QFileIconProvider.IconType.Drive if identifier == "drive" else QFileIconProvider.IconType.Folder
            icon = self._provider.icon(icon_type)
        dimensions = requested_size if requested_size.isValid() else QSize(24, 24)
        pixmap = icon.pixmap(dimensions)
        size.setWidth(pixmap.width())
        size.setHeight(pixmap.height())
        return pixmap
