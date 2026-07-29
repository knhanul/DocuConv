from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QStandardPaths, QStorageInfo, Qt, Signal

from backend.path_utils import normalize_path
from backend.selection_manager import SelectionManager


@dataclass
class FolderNode:
    path: Path
    name: str
    depth: int
    expanded: bool = False
    has_children: bool = True
    is_virtual: bool = False
    virtual_children: list = field(default_factory=list)


class FolderTreeModel(QAbstractListModel):
    PathRole = Qt.UserRole + 1
    NameRole = Qt.UserRole + 2
    DepthRole = Qt.UserRole + 3
    ExpandedRole = Qt.UserRole + 4
    HasChildrenRole = Qt.UserRole + 5
    CheckedRole = Qt.UserRole + 6
    IsVirtualRole = Qt.UserRole + 7

    folderActivated = Signal(str)

    def __init__(self, selection: SelectionManager, parent=None) -> None:
        super().__init__(parent)
        self._selection = selection
        self._nodes: list[FolderNode] = self._build_roots()

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.PathRole: b"folderPath",
            self.NameRole: b"folderName",
            self.DepthRole: b"depth",
            self.ExpandedRole: b"expanded",
            self.HasChildrenRole: b"hasChildren",
            self.CheckedRole: b"checked",
            self.IsVirtualRole: b"isVirtual",
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._nodes)

    def data(self, index: QModelIndex, role=Qt.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None
        node = self._nodes[index.row()]
        if role == self.PathRole:
            return "" if node.is_virtual else str(node.path)
        if role in (self.NameRole, Qt.DisplayRole):
            return node.name
        if role == self.DepthRole:
            return node.depth
        if role == self.ExpandedRole:
            return node.expanded
        if role == self.HasChildrenRole:
            return node.has_children
        if role == self.CheckedRole:
            return False if node.is_virtual else self._selection.is_folder_selected(node.path)
        if role == self.IsVirtualRole:
            return node.is_virtual
        return None

    def _build_roots(self) -> list[FolderNode]:
        # --- 빠른 액세스 ---
        quick_items: list[tuple[str, QStandardPaths.StandardLocation]] = [
            ("바탕 화면", QStandardPaths.StandardLocation.DesktopLocation),
            ("다운로드", QStandardPaths.StandardLocation.DownloadLocation),
            ("문서", QStandardPaths.StandardLocation.DocumentsLocation),
            ("그림", QStandardPaths.StandardLocation.PicturesLocation),
        ]
        quick_children: list[FolderNode] = []
        seen: set[str] = set()
        for label, loc in quick_items:
            path_str = QStandardPaths.writableLocation(loc)
            if not path_str:
                continue
            path = Path(path_str)
            if not path.exists():
                continue
            key = normalize_path(path)
            if key in seen:
                continue
            seen.add(key)
            quick_children.append(
                FolderNode(path=path, name=label, depth=1, has_children=self._has_children(path))
            )

        # --- 내 PC ---
        pc_children: list[FolderNode] = []
        if os.name == "nt":
            for volume in QStorageInfo.mountedVolumes():
                if not volume.isReady() or not volume.isValid():
                    continue
                root = volume.rootPath()
                if not root:
                    continue
                path = Path(root)
                key = normalize_path(path)
                if key in seen:
                    continue
                seen.add(key)
                name = volume.displayName() or f"로컬 디스크 ({path.drive})"
                pc_children.append(
                    FolderNode(path=path, name=name, depth=1, has_children=self._has_children(path))
                )
        else:
            pc_children.append(
                FolderNode(path=Path("/"), name="파일 시스템", depth=1, has_children=self._has_children(Path("/")))
            )

        quick_access = FolderNode(
            path=Path(""), name="빠른 액세스", depth=0, is_virtual=True,
            has_children=bool(quick_children), virtual_children=quick_children,
        )
        this_pc = FolderNode(
            path=Path(""), name="내 PC", depth=0, is_virtual=True,
            has_children=bool(pc_children), virtual_children=pc_children,
        )
        return [quick_access, this_pc]

    @staticmethod
    def _has_children(path: Path) -> bool:
        try:
            with os.scandir(path) as entries:
                return any(entry.is_dir(follow_symlinks=False) and not entry.name.startswith(".") for entry in entries)
        except (OSError, PermissionError):
            return False

    @staticmethod
    def _children(path: Path, depth: int) -> list[FolderNode]:
        result: list[FolderNode] = []
        try:
            entries = [entry for entry in os.scandir(path) if entry.is_dir(follow_symlinks=False) and not entry.name.startswith(".")]
        except (OSError, PermissionError):
            return result
        for entry in sorted(entries, key=lambda item: item.name.casefold()):
            child = Path(entry.path)
            result.append(FolderNode(child, entry.name, depth, False, FolderTreeModel._has_children(child)))
        return result

    def toggle_expanded(self, row: int) -> None:
        if not 0 <= row < len(self._nodes):
            return
        node = self._nodes[row]
        if not node.has_children:
            return
        if node.expanded:
            end = row + 1
            while end < len(self._nodes) and self._nodes[end].depth > node.depth:
                end += 1
            if end > row + 1:
                self.beginRemoveRows(QModelIndex(), row + 1, end - 1)
                del self._nodes[row + 1:end]
                self.endRemoveRows()
            node.expanded = False
        else:
            if node.is_virtual:
                children = list(node.virtual_children)
            else:
                children = self._children(node.path, node.depth + 1)
            if children:
                self.beginInsertRows(QModelIndex(), row + 1, row + len(children))
                self._nodes[row + 1:row + 1] = children
                self.endInsertRows()
            node.expanded = True
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, [self.ExpandedRole])

    def activate(self, row: int) -> None:
        if not 0 <= row < len(self._nodes):
            return
        node = self._nodes[row]
        if node.is_virtual:
            return
        self.folderActivated.emit(str(node.path))

    def toggle_checked(self, row: int) -> None:
        if not 0 <= row < len(self._nodes):
            return
        node = self._nodes[row]
        if node.is_virtual:
            return
        self._selection.toggle_folder(node.path)
        self.refresh_checks()

    def refresh_checks(self) -> None:
        if not self._nodes:
            return
        self.dataChanged.emit(self.index(0, 0), self.index(len(self._nodes) - 1, 0), [self.CheckedRole])

    def select_path(self, path: str | Path) -> None:
        key = normalize_path(path)
        for row, node in enumerate(self._nodes):
            if not node.is_virtual and normalize_path(node.path) == key:
                self.activate(row)
                return
        self.folderActivated.emit(str(path))
