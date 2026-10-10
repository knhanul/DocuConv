from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt

from backend.job_model import ConversionJob


class HistoryModel(QAbstractListModel):
    FileNameRole = Qt.ItemDataRole.UserRole + 1
    InputPathRole = Qt.ItemDataRole.UserRole + 2
    OutputPathRole = Qt.ItemDataRole.UserRole + 3
    TargetRole = Qt.ItemDataRole.UserRole + 4
    StatusRole = Qt.ItemDataRole.UserRole + 5
    FinishedAtRole = Qt.ItemDataRole.UserRole + 6
    MessageRole = Qt.ItemDataRole.UserRole + 7

    def __init__(self, storage_path: Path, max_items: int, parent=None) -> None:
        super().__init__(parent)
        self._storage_path = storage_path
        self._max_items = max_items
        self._items: list[dict] = []
        self._load()

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.FileNameRole: b"fileName",
            self.InputPathRole: b"inputPath",
            self.OutputPathRole: b"outputPath",
            self.TargetRole: b"targetLabel",
            self.StatusRole: b"status",
            self.FinishedAtRole: b"finishedAt",
            self.MessageRole: b"message",
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._items)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._items):
            return None
        item = self._items[index.row()]
        mapping = {
            self.FileNameRole: "fileName",
            self.InputPathRole: "inputPath",
            self.OutputPathRole: "outputPath",
            self.TargetRole: "targetLabel",
            self.StatusRole: "status",
            self.FinishedAtRole: "finishedAt",
            self.MessageRole: "message",
        }
        if role == Qt.ItemDataRole.DisplayRole:
            return item.get("fileName", "")
        key = mapping.get(role)
        return item.get(key, "") if key else None

    def _load(self) -> None:
        try:
            raw = json.loads(self._storage_path.read_text(encoding="utf-8"))
            if isinstance(raw, list):
                self._items = raw[: self._max_items]
        except (OSError, json.JSONDecodeError):
            self._items = []

    def _save(self) -> None:
        try:
            self._storage_path.parent.mkdir(parents=True, exist_ok=True)
            self._storage_path.write_text(json.dumps(self._items, ensure_ascii=False, indent=2), encoding="utf-8")
        except OSError:
            pass

    def append_job(self, job: ConversionJob) -> None:
        item = {
            "fileName": job.input_path.name,
            "inputPath": str(job.input_path),
            "outputPath": str(job.output_path),
            "targetLabel": job.target_label,
            "status": job.status,
            "finishedAt": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            "message": job.message,
        }
        self.beginInsertRows(QModelIndex(), 0, 0)
        self._items.insert(0, item)
        self.endInsertRows()
        if len(self._items) > self._max_items:
            self.beginRemoveRows(QModelIndex(), self._max_items, len(self._items) - 1)
            del self._items[self._max_items :]
            self.endRemoveRows()
        self._save()

    def clear(self) -> None:
        self.beginResetModel()
        self._items = []
        self.endResetModel()
        self._save()
