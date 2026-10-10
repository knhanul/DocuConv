from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from uuid import uuid4

from PySide6.QtCore import QAbstractListModel, QModelIndex, Qt, Signal


@dataclass
class ConversionJob:
    input_path: Path
    output_path: Path
    source_root: Path
    mode: str
    image_format: str = "png"
    id: str = field(default_factory=lambda: uuid4().hex)
    status: str = "대기 중"
    progress: int = 0
    message: str = ""
    selected: bool = False

    @property
    def target_label(self) -> str:
        if self.mode == "hwpx":
            return "HWPX"
        if self.mode == "pdf":
            return "PDF"
        return self.image_format.upper()


class JobListModel(QAbstractListModel):
    IdRole = Qt.ItemDataRole.UserRole + 1
    SequenceRole = Qt.ItemDataRole.UserRole + 2
    FileNameRole = Qt.ItemDataRole.UserRole + 3
    InputPathRole = Qt.ItemDataRole.UserRole + 4
    OutputPathRole = Qt.ItemDataRole.UserRole + 5
    TargetRole = Qt.ItemDataRole.UserRole + 6
    StatusRole = Qt.ItemDataRole.UserRole + 7
    ProgressRole = Qt.ItemDataRole.UserRole + 8
    MessageRole = Qt.ItemDataRole.UserRole + 9
    SelectedRole = Qt.ItemDataRole.UserRole + 10

    overallChanged = Signal()

    def __init__(self, parent=None) -> None:
        super().__init__(parent)
        self._jobs: list[ConversionJob] = []

    def roleNames(self) -> dict[int, bytes]:
        return {
            self.IdRole: b"jobId",
            self.SequenceRole: b"sequence",
            self.FileNameRole: b"fileName",
            self.InputPathRole: b"inputPath",
            self.OutputPathRole: b"outputPath",
            self.TargetRole: b"targetLabel",
            self.StatusRole: b"status",
            self.ProgressRole: b"progress",
            self.MessageRole: b"message",
            self.SelectedRole: b"selected",
        }

    def rowCount(self, parent=QModelIndex()) -> int:
        return 0 if parent.isValid() else len(self._jobs)

    def data(self, index: QModelIndex, role=Qt.ItemDataRole.DisplayRole):
        if not index.isValid() or not 0 <= index.row() < len(self._jobs):
            return None
        job = self._jobs[index.row()]
        if role == self.IdRole:
            return job.id
        if role == self.SequenceRole:
            return index.row() + 1
        if role in (self.FileNameRole, Qt.ItemDataRole.DisplayRole):
            return job.input_path.name
        if role == self.InputPathRole:
            return str(job.input_path)
        if role == self.OutputPathRole:
            return str(job.output_path)
        if role == self.TargetRole:
            return job.target_label
        if role == self.StatusRole:
            return job.status
        if role == self.ProgressRole:
            return job.progress
        if role == self.MessageRole:
            return job.message
        if role == self.SelectedRole:
            return job.selected
        return None

    @property
    def jobs(self) -> list[ConversionJob]:
        return list(self._jobs)

    def set_jobs(self, jobs: list[ConversionJob]) -> None:
        self.beginResetModel()
        self._jobs = jobs
        self.endResetModel()
        self.overallChanged.emit()

    def clear(self) -> None:
        self.set_jobs([])

    def find(self, job_id: str) -> tuple[int, ConversionJob] | None:
        for row, job in enumerate(self._jobs):
            if job.id == job_id:
                return row, job
        return None

    def update(self, job_id: str, *, status: str | None = None, progress: int | None = None, message: str | None = None) -> None:
        found = self.find(job_id)
        if found is None:
            return
        row, job = found
        roles: list[int] = []
        if status is not None:
            job.status = status
            roles.append(self.StatusRole)
        if progress is not None:
            job.progress = max(0, min(100, int(progress)))
            roles.append(self.ProgressRole)
        if message is not None:
            job.message = message
            roles.append(self.MessageRole)
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, roles)
        self.overallChanged.emit()

    def toggle_selected(self, row: int) -> None:
        if not 0 <= row < len(self._jobs):
            return
        self._jobs[row].selected = not self._jobs[row].selected
        idx = self.index(row, 0)
        self.dataChanged.emit(idx, idx, [self.SelectedRole])

    def remove_selected(self) -> None:
        remaining = [job for job in self._jobs if not job.selected]
        self.set_jobs(remaining)

    def overall_progress(self) -> int:
        if not self._jobs:
            return 0
        return round(sum(job.progress for job in self._jobs) / len(self._jobs))

    def counts(self) -> tuple[int, int, int, int]:
        waiting = sum(job.status in {"대기 중", "변환 중", "취소 요청"} for job in self._jobs)
        completed = sum(job.status == "완료" for job in self._jobs)
        failed = sum(job.status == "실패" for job in self._jobs)
        cancelled = sum(job.status == "취소됨" for job in self._jobs)
        return waiting, completed, failed, cancelled
