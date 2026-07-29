from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

from backend.path_utils import is_same_or_child, normalize_path


@dataclass(frozen=True)
class SelectedSource:
    path: Path
    source_root: Path


class SelectionManager:
    """폴더 선택, 개별 파일 선택, 폴더 내부 파일 제외 상태를 관리합니다."""

    def __init__(self) -> None:
        self._folders: dict[str, Path] = {}
        self._files: dict[str, Path] = {}
        self._excluded_files: set[str] = set()

    @property
    def selected_folder_count(self) -> int:
        return len(self._folders)

    @property
    def explicit_file_count(self) -> int:
        return len(self._files)

    def clear(self) -> None:
        self._folders.clear()
        self._files.clear()
        self._excluded_files.clear()

    def is_folder_selected(self, path: str | Path) -> bool:
        key = normalize_path(path)
        if key in self._folders:
            return True
        return any(is_same_or_child(path, folder) for folder in self._folders.values())

    def toggle_folder(self, path: str | Path) -> bool:
        folder = Path(path)
        key = normalize_path(folder)
        if key in self._folders:
            del self._folders[key]
            self._excluded_files = {
                item for item in self._excluded_files if not is_same_or_child(item, folder)
            }
            return False

        # 상위 폴더가 이미 선택된 경우에는 중복 폴더를 추가하지 않습니다.
        for selected in self._folders.values():
            if is_same_or_child(folder, selected):
                return True

        # 새 상위 폴더 선택 시 그 아래에 있던 선택 폴더는 제거합니다.
        child_keys = [key_ for key_, value in self._folders.items() if is_same_or_child(value, folder)]
        for child_key in child_keys:
            del self._folders[child_key]
        self._folders[key] = folder
        self._excluded_files = {
            item for item in self._excluded_files if not is_same_or_child(item, folder)
        }
        return True

    def is_file_selected(self, path: str | Path) -> bool:
        key = normalize_path(path)
        if key in self._excluded_files:
            return False
        if key in self._files:
            return True
        return any(is_same_or_child(path, folder) for folder in self._folders.values())

    def set_file_selected(self, path: str | Path, selected: bool) -> None:
        file_path = Path(path)
        key = normalize_path(file_path)
        covered_by_folder = any(is_same_or_child(file_path, folder) for folder in self._folders.values())
        if selected:
            self._excluded_files.discard(key)
            if not covered_by_folder:
                self._files[key] = file_path
        else:
            self._files.pop(key, None)
            if covered_by_folder:
                self._excluded_files.add(key)
            else:
                self._excluded_files.discard(key)

    def toggle_file(self, path: str | Path) -> bool:
        selected = not self.is_file_selected(path)
        self.set_file_selected(path, selected)
        return selected

    def selection_summary(self) -> str:
        parts: list[str] = []
        if self.selected_folder_count:
            parts.append(f"폴더 {self.selected_folder_count}개")
        if self.explicit_file_count:
            parts.append(f"파일 {self.explicit_file_count}개")
        if not parts:
            return "선택된 항목 없음"
        return " · ".join(parts)

    def enumerate_sources(self, extensions: Iterable[str]) -> list[SelectedSource]:
        allowed = {ext.lower() for ext in extensions}
        result: dict[str, SelectedSource] = {}

        for folder in self._folders.values():
            source_root = folder.parent
            try:
                iterator = os.walk(folder)
                for root, dirs, files in iterator:
                    dirs[:] = [d for d in dirs if not d.startswith(".") and d not in {"$RECYCLE.BIN", "System Volume Information"}]
                    for name in files:
                        path = Path(root) / name
                        key = normalize_path(path)
                        if key in self._excluded_files or path.suffix.lower() not in allowed:
                            continue
                        result.setdefault(key, SelectedSource(path=path, source_root=source_root))
            except OSError:
                continue

        for path in self._files.values():
            if path.suffix.lower() not in allowed or not path.exists():
                continue
            key = normalize_path(path)
            if key in self._excluded_files:
                continue
            result.setdefault(key, SelectedSource(path=path, source_root=path.parent))

        return sorted(result.values(), key=lambda item: normalize_path(item.path))
