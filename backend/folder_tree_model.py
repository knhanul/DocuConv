from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, QStandardPaths, QStorageInfo, Qt, Signal

from backend.path_utils import normalize_path


@dataclass
class FolderNode:
    path: Path | None
    name: str
    depth: int
    kind: str = "folder"  # "section" or "folder"
    expanded: bool = False
    has_children: bool = False
    child_count: int = 0
    icon: str = "folder"
    is_quick: bool = False
    can_unpin: bool = False

    @property
    def key(self) -> str:
        if self.kind == "section":
            return f"section:{self.name}"
        return normalize_path(self.path)


class FolderTreeModel(QAbstractListModel):
    PathRole = Qt.ItemDataRole.UserRole + 1
    NameRole = Qt.ItemDataRole.UserRole + 2
    DepthRole = Qt.ItemDataRole.UserRole + 3
    ExpandedRole = Qt.ItemDataRole.UserRole + 4
    HasChildrenRole = Qt.ItemDataRole.UserRole + 5
    ChildCountRole = Qt.ItemDataRole.UserRole + 6
    ActiveRole = Qt.ItemDataRole.UserRole + 7
    IsDriveRole = Qt.ItemDataRole.UserRole + 8
    KindRole = Qt.ItemDataRole.UserRole + 9
    IconRole = Qt.ItemDataRole.UserRole + 10
    IsQuickRole = Qt.ItemDataRole.UserRole + 11
    CanUnpinRole = Qt.ItemDataRole.UserRole + 12

    QUICK_SECTION = "빠른 액세스"
    PC_SECTION = "내 PC"

    folderActivated = Signal(str)

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._current_path = ""
        self._quick_entries: list[dict] = []
        self._added_roots: list[Path] = []
        self._nodes: list[FolderNode] = []
        self._rebuild()

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.PathRole: b"folderPath",
            self.NameRole: b"folderName",
            self.DepthRole: b"depth",
            self.ExpandedRole: b"expanded",
            self.HasChildrenRole: b"hasChildren",
            self.ChildCountRole: b"childCount",
            self.ActiveRole: b"activeFolder",
            self.IsDriveRole: b"isDrive",
            self.KindRole: b"kind",
            self.IconRole: b"icon",
            self.IsQuickRole: b"isQuick",
            self.CanUnpinRole: b"canUnpin",
        }

    def rowCount(self, parent=None) -> int:
        return 0 if parent is not None and parent.isValid() else len(self._nodes)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._nodes):
            return None
        node = self._nodes[index.row()]
        if role == self.PathRole:
            return str(node.path) if node.path else ""
        if role in (self.NameRole, Qt.ItemDataRole.DisplayRole):
            return node.name
        if role == self.DepthRole:
            return node.depth
        if role == self.ExpandedRole:
            return node.expanded
        if role == self.HasChildrenRole:
            return node.has_children
        if role == self.ChildCountRole:
            return node.child_count
        if role == self.ActiveRole:
            return node.path is not None and normalize_path(node.path) == self._current_path
        if role == self.IsDriveRole:
            return node.path is not None and node.path == node.path.parent
        if role == self.KindRole:
            return node.kind
        if role == self.IconRole:
            return node.icon
        if role == self.IsQuickRole:
            return node.is_quick
        if role == self.CanUnpinRole:
            return node.can_unpin
        return None

    @staticmethod
    def quick_access_folders() -> list[dict[str, str]]:
        return [
            {
                "label": label,
                "path": QStandardPaths.writableLocation(location),
                "icon": icon,
                "iconSource": f"image://filesystem/{icon}",
            }
            for label, location, icon in (
                ("바탕 화면", QStandardPaths.StandardLocation.DesktopLocation, "desktop"),
                ("다운로드", QStandardPaths.StandardLocation.DownloadLocation, "downloads"),
                ("문서", QStandardPaths.StandardLocation.DocumentsLocation, "documents"),
            )
        ]

    def set_quick_access(self, entries: list[dict]) -> None:
        self._quick_entries = list(entries)
        self.refresh()

    def _build_roots(self) -> list[FolderNode]:
        roots: list[FolderNode] = []
        seen: set[str] = set()
        if os.name == "nt":
            for volume in QStorageInfo.mountedVolumes():
                if not volume.isReady() or not volume.isValid() or not volume.rootPath():
                    continue
                path = Path(volume.rootPath())
                key = normalize_path(path)
                if key in seen:
                    continue
                seen.add(key)
                name = f"{volume.name() or '로컬 디스크'} ({path.drive})" if path.drive else volume.displayName()
                node = self._node(path, name, 0)
                node.icon = "drive"
                roots.append(node)
        else:
            roots.append(self._node(Path("/"), "파일 시스템", 0))
        return roots

    def _pc_nodes(self) -> list[FolderNode]:
        children = self._build_roots()
        seen = {normalize_path(node.path) for node in children}
        for path in self._added_roots:
            if path.is_dir() and normalize_path(path) not in seen:
                children.append(self._node(path, path.name or str(path), 1))
                seen.add(normalize_path(path))
        return children

    def _quick_nodes(self) -> list[FolderNode]:
        nodes: list[FolderNode] = []
        for entry in self._quick_entries:
            path = Path(entry.get("path") or "")
            if not path.is_dir():
                continue
            node = self._node(path, entry.get("label") or path.name or str(path), 1)
            node.icon = entry.get("icon", "folder")
            node.is_quick = True
            node.can_unpin = bool(entry.get("canUnpin"))
            nodes.append(node)
        return nodes

    @staticmethod
    def _visible_entries(path: Path) -> list[os.DirEntry]:
        with os.scandir(path) as entries:
            return [entry for entry in entries if not entry.name.startswith(".")]

    @classmethod
    def _node(cls, path: Path, name: str, depth: int) -> FolderNode:
        try:
            entries = cls._visible_entries(path)
            has_children = any(entry.is_dir(follow_symlinks=False) for entry in entries)
            count = len(entries)
        except OSError:
            has_children, count = False, -1
        return FolderNode(path, name, depth, has_children=has_children, child_count=count)

    @classmethod
    def _children(cls, path: Path, depth: int) -> list[FolderNode]:
        try:
            entries = [entry for entry in cls._visible_entries(path) if entry.is_dir(follow_symlinks=False)]
        except OSError:
            return []
        return [cls._node(Path(entry.path), entry.name, depth) for entry in sorted(entries, key=lambda item: item.name.casefold())]

    def _child_nodes(self, node: FolderNode) -> list[FolderNode]:
        if node.kind == "section":
            children = self._quick_nodes() if node.name == self.QUICK_SECTION else self._pc_nodes()
            node.child_count = len(children)
        else:
            children = self._children(node.path, node.depth + 1)
        node.has_children = bool(children)
        for child in children:
            child.depth = node.depth + 1
        return children

    def _rebuild(self, expanded: set[str] | None = None) -> None:
        sections = [
            FolderNode(None, self.QUICK_SECTION, 0, kind="section", icon="quick"),
            FolderNode(None, self.PC_SECTION, 0, kind="section", icon="pc"),
        ]
        nodes: list[FolderNode] = []
        pending = list(reversed(sections))
        while pending:
            node = pending.pop()
            node.expanded = node.kind == "section" if expanded is None else node.key in expanded
            nodes.append(node)
            children = self._child_nodes(node) if node.kind == "section" or (node.expanded and node.has_children) else []
            if children:
                pending.extend(reversed(children))
        self._nodes = nodes

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
            children = self._child_nodes(node)
            if children:
                self.beginInsertRows(QModelIndex(), row + 1, row + len(children))
                self._nodes[row + 1:row + 1] = children
                self.endInsertRows()
            node.expanded = bool(children)
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, [self.ExpandedRole, self.HasChildrenRole])

    def activate(self, row: int) -> None:
        if 0 <= row < len(self._nodes):
            node = self._nodes[row]
            if node.kind == "folder" and node.path is not None:
                self.select_path(node.path)

    def select_path(self, path: str | Path) -> None:
        folder = Path(path)
        if folder.is_dir():
            self.folderActivated.emit(str(folder))

    def set_current_path(self, path: str | Path) -> None:
        key = normalize_path(path)
        if key == self._current_path:
            return
        self._current_path = key
        if self._nodes:
            self.dataChanged.emit(self.index(0), self.index(len(self._nodes) - 1), [self.ActiveRole])

    def add_root(self, path: str | Path) -> None:
        folder = Path(path)
        if not folder.is_dir():
            return
        key = normalize_path(folder.absolute())
        if key in self._added_root_keys():
            return
        self._added_roots.append(folder.absolute())
        self.refresh()

    def _added_root_keys(self) -> set[str]:
        pc_nodes = [node for node in self._nodes if node.depth == 1 and node.kind == "folder" and not node.is_quick]
        keys = {normalize_path(node.path) for node in pc_nodes if node.path}
        keys.update(normalize_path(path) for path in self._added_roots)
        return keys

    def refresh(self) -> None:
        expanded = {node.key for node in self._nodes if node.expanded}
        self.beginResetModel()
        self._rebuild(expanded)
        self.endResetModel()
