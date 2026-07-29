from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from backend.file_types import ALL_VISIBLE_EXTENSIONS, type_label
from backend.selection_manager import SelectionManager


@dataclass(frozen=True)
class FileEntry:
    path: Path
    size: int
    modified: float


class FileListModel(QAbstractListModel):
    PathRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    SizeRole = Qt.UserRole + 3
    ModifiedRole = Qt.UserRole + 4
    CheckedRole = Qt.UserRole + 5
    TypeRole = Qt.UserRole + 6
    ExtensionRole = Qt.UserRole + 7

    def __init__(self, selection: SelectionManager, parent=None) -> None:
        super().__init__(parent)
        self._selection = selection
        self._folder = Path.home() / "Documents"
        if not self._folder.exists():
            self._folder = Path.home()
        self._items: list[FileEntry] = []
        self.reload()

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.PathRole: b"filePath",
            self.NameRole: b"fileName",
            self.SizeRole: b"sizeText",
            self.ModifiedRole: b"modifiedText",
            self.CheckedRole: b"checked",
            self.TypeRole: b"typeLabel",
            self.ExtensionRole: b"extension",
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == self.PathRole:
            return str(item.path)
        if role in (self.NameRole, Qt.DisplayRole):
            return item.path.name
        if role == self.SizeRole:
            return self._format_size(item.size)
        if role == self.ModifiedRole:
            return datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M")
        if role == self.CheckedRole:
            return self._selection.is_file_selected(item.path)
        if role == self.TypeRole:
            return type_label(str(item.path))
        if role == self.ExtensionRole:
            return item.path.suffix.lower().lstrip(".").upper()
        return None

    @property
    def folder(self) -> Path:
        return self._folder

    def set_folder(self, folder: str | Path) -> None:
        path = Path(folder)
        if not path.exists() or not path.is_dir():
            return
        self._folder = path
        self.reload()

    def reload(self) -> None:
        entries: list[FileEntry] = []
        try:
            for path in self._folder.iterdir():
                if not path.is_file() or path.suffix.lower() not in ALL_VISIBLE_EXTENSIONS:
                    continue
                try:
                    stat = path.stat()
                except OSError:
                    continue
                entries.append(FileEntry(path=path, size=stat.st_size, modified=stat.st_mtime))
        except (OSError, PermissionError):
            entries = []
        entries.sort(key=lambda item: item.path.name.casefold())
        self.beginResetModel()
        self._items = entries
        self.endResetModel()

    def toggle(self, row: int) -> None:
        if not 0 <= row < len(self._items):
            return
        self._selection.toggle_file(self._items[row].path)
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, [self.CheckedRole])

    def set_all(self, selected: bool) -> None:
        for item in self._items:
            self._selection.set_file_selected(item.path, selected)
        self.refresh_checks()

    def refresh_checks(self) -> None:
        if self._items:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._items) - 1, 0), [self.CheckedRole])

    @property
    def count(self) -> int:
        return len(self._items)

    @property
    def total_size(self) -> int:
        return sum(item.size for item in self._items)

    @staticmethod
    def _format_size(size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{size} B"
