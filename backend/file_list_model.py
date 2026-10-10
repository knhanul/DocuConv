from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import Property, QAbstractListModel, QModelIndex, Qt, Signal, Slot

from backend.file_types import ALL_VISIBLE_EXTENSIONS, type_label
from backend.selection_manager import SelectionManager


@dataclass(frozen=True)
class FileEntry:
    path: Path
    size: int
    modified: float
    is_folder: bool = False


class FileListModel(QAbstractListModel):
    PathRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    SizeRole = Qt.ItemDataRole.UserRole + 3
    ModifiedRole = Qt.ItemDataRole.UserRole + 4
    CheckedRole = Qt.ItemDataRole.UserRole + 5
    TypeRole = Qt.ItemDataRole.UserRole + 6
    ExtensionRole = Qt.ItemDataRole.UserRole + 7
    IsFolderRole = Qt.ItemDataRole.UserRole + 8

    SORT_COLUMNS = {"name", "type", "size", "modified"}

    folderActivated = Signal(str)
    sortChanged = Signal()

    def __init__(self, selection: SelectionManager, parent=None) -> None:
        super().__init__(parent)
        self._selection = selection
        self._folder = Path.home() / "Documents"
        if not self._folder.exists():
            self._folder = Path.home()
        self._items: list[FileEntry] = []
        self._sort_column = "name"
        self._sort_ascending = True
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
            self.IsFolderRole: b"isFolder",
        }

    def rowCount(self, parent=None) -> int:
        return 0 if parent is not None and parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        if role == self.PathRole:
            return str(item.path)
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return item.path.name
        if role == self.SizeRole:
            return "" if item.is_folder else self._format_size(item.size)
        if role == self.ModifiedRole:
            return datetime.fromtimestamp(item.modified).strftime("%Y-%m-%d %H:%M")
        if role == self.CheckedRole:
            return not item.is_folder and self._selection.is_file_selected(item.path)
        if role == self.TypeRole:
            return "파일 폴더" if item.is_folder else type_label(str(item.path))
        if role == self.ExtensionRole:
            return "" if item.is_folder else item.path.suffix.lower().lstrip(".").upper()
        if role == self.IsFolderRole:
            return item.is_folder
        return None

    @property
    def folder(self) -> Path:
        return self._folder

    def set_folder(self, folder: str | Path) -> None:
        path = Path(folder)
        if not path.exists() or not path.is_dir():
            return
        self._folder = path.absolute()
        self.reload()

    def reload(self) -> None:
        entries: list[FileEntry] = []
        try:
            for path in self._folder.iterdir():
                try:
                    is_folder = path.is_dir()
                    if is_folder and path.name.startswith("."):
                        continue
                    if not is_folder and (not path.is_file() or path.suffix.lower() not in ALL_VISIBLE_EXTENSIONS):
                        continue
                    stat = path.stat()
                except OSError:
                    continue
                entries.append(FileEntry(path=path, size=stat.st_size, modified=stat.st_mtime, is_folder=is_folder))
        except (OSError, PermissionError):
            entries = []
        self.beginResetModel()
        self._items = self._sorted(entries)
        self.endResetModel()

    def _sort_key(self, item: FileEntry):
        name = item.path.name.casefold()
        if self._sort_column == "size":
            primary = item.size
        elif self._sort_column == "modified":
            primary = item.modified
        elif self._sort_column == "type":
            primary = "" if item.is_folder else item.path.suffix.lower()
        else:
            primary = name
        return (primary, name)

    def _sorted(self, entries: list[FileEntry]) -> list[FileEntry]:
        folders = [item for item in entries if item.is_folder]
        files = [item for item in entries if not item.is_folder]
        folders.sort(key=self._sort_key, reverse=not self._sort_ascending)
        files.sort(key=self._sort_key, reverse=not self._sort_ascending)
        return files + folders

    @Slot(str)
    def setSort(self, column: str) -> None:
        if column not in self.SORT_COLUMNS:
            return
        if self._sort_column == column:
            self._sort_ascending = not self._sort_ascending
        else:
            self._sort_column = column
            self._sort_ascending = True
        self.layoutAboutToBeChanged.emit()
        self._items = self._sorted(self._items)
        self.layoutChanged.emit()
        self.sortChanged.emit()

    @property
    def sort_column(self) -> str:
        return self._sort_column

    @property
    def sort_ascending(self) -> bool:
        return self._sort_ascending

    @Property(str, notify=sortChanged)
    def sortColumn(self) -> str:
        return self._sort_column

    @Property(bool, notify=sortChanged)
    def sortAscending(self) -> bool:
        return self._sort_ascending

    def activate_folder(self, row: int) -> None:
        if 0 <= row < len(self._items) and self._items[row].is_folder and self._items[row].path.is_dir():
            self.folderActivated.emit(str(self._items[row].path))

    def toggle(self, row: int) -> None:
        if not 0 <= row < len(self._items) or self._items[row].is_folder:
            return
        self._selection.toggle_file(self._items[row].path)
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, [self.CheckedRole])

    def set_all(self, selected: bool) -> None:
        for item in self._items:
            if not item.is_folder:
                self._selection.set_file_selected(item.path, selected)
        self.refresh_checks()

    def refresh_checks(self) -> None:
        if self._items:
            self.dataChanged.emit(self.index(0, 0), self.index(len(self._items) - 1, 0), [self.CheckedRole])

    @property
    def count(self) -> int:
        return sum(not item.is_folder for item in self._items)

    @property
    def folder_count(self) -> int:
        return sum(item.is_folder for item in self._items)

    @property
    def total_size(self) -> int:
        return sum(item.size for item in self._items if not item.is_folder)

    @staticmethod
    def _format_size(size: int) -> str:
        units = ["B", "KB", "MB", "GB", "TB"]
        value = float(size)
        for unit in units:
            if value < 1024 or unit == units[-1]:
                return f"{value:.0f} {unit}" if unit == "B" else f"{value:.1f} {unit}"
            value /= 1024
        return f"{size} B"
