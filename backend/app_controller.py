from __future__ import annotations

import sys
from pathlib import Path

from PySide6.QtCore import QObject, Property, QSettings, QStandardPaths, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from backend.file_list_model import FileListModel
from backend.file_types import target_extensions
from backend.folder_tree_model import FolderTreeModel
from backend.history_model import HistoryModel
from backend.job_model import ConversionJob, JobListModel
from backend.path_utils import normalize_path, output_file_path, output_image_directory, reserve_batch_file_path
from backend.selection_manager import SelectionManager
from backend.settings import AppSettings
from backend.version import APP_VERSION, BUILD_DATE
from backend.worker import ConversionWorker


class AppController(QObject):
    outputFolderChanged = Signal()
    conversionModeChanged = Signal()
    imageFormatChanged = Signal()
    preserveStructureChanged = Signal()
    overwriteChanged = Signal()
    openAfterCompleteChanged = Signal()
    busyChanged = Signal()
    currentFolderChanged = Signal()
    selectionSummaryChanged = Signal()
    jobSummaryChanged = Signal()
    statusTextChanged = Signal()
    notify = Signal(str, str, str)

    def __init__(self, app_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._app_dir = app_dir
        self._app_settings = AppSettings.load(app_dir / "appsettings.json")
        self._preferences = QSettings()
        self._selection = SelectionManager()
        self._folder_tree = FolderTreeModel(self._selection, self)
        self._file_list = FileListModel(self._selection, self)
        self._job_list = JobListModel(self)

        app_data = Path(QStandardPaths.writableLocation(QStandardPaths.AppLocalDataLocation))
        self._history = HistoryModel(app_data / "history.json", self._app_settings.max_history_items, self)

        default_output = Path.home() / "Documents" / "POSID 변환결과"
        saved_output = self._preferences.value("outputFolder", str(default_output), str)
        self._output_folder = str(Path(saved_output))
        self._conversion_mode = self._preferences.value("conversionMode", "pdf", str)
        self._image_format = self._preferences.value("imageFormat", "png", str)
        self._preserve_structure = self._preferences.value("preserveStructure", True, bool)
        self._overwrite = self._preferences.value("overwrite", False, bool)
        self._open_after_complete = self._preferences.value("openAfterComplete", False, bool)
        self._busy = False
        self._status_text = "대기 중"
        self._worker: ConversionWorker | None = None

        self._folder_tree.folderActivated.connect(self._on_folder_activated)
        self._job_list.overallChanged.connect(self.jobSummaryChanged)

    # --------------------------- Models ---------------------------------
    @Property(QObject, constant=True)
    def folderTreeModel(self):
        return self._folder_tree

    @Property(QObject, constant=True)
    def fileListModel(self):
        return self._file_list

    @Property(QObject, constant=True)
    def jobListModel(self):
        return self._job_list

    @Property(QObject, constant=True)
    def historyModel(self):
        return self._history

    # --------------------------- Properties -----------------------------
    @Property(str, notify=outputFolderChanged)
    def outputFolder(self) -> str:
        return self._output_folder

    @Property(str, notify=conversionModeChanged)
    def conversionMode(self) -> str:
        return self._conversion_mode

    @Property(str, notify=imageFormatChanged)
    def imageFormat(self) -> str:
        return self._image_format

    @Property(bool, notify=preserveStructureChanged)
    def preserveStructure(self) -> bool:
        return self._preserve_structure

    @Property(bool, notify=overwriteChanged)
    def overwrite(self) -> bool:
        return self._overwrite

    @Property(bool, notify=openAfterCompleteChanged)
    def openAfterComplete(self) -> bool:
        return self._open_after_complete

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=currentFolderChanged)
    def currentFolder(self) -> str:
        return str(self._file_list.folder)

    @Property(str, notify=currentFolderChanged)
    def currentFolderSummary(self) -> str:
        return f"문서 파일 {self._file_list.count}개"

    @Property(str, notify=selectionSummaryChanged)
    def selectionSummary(self) -> str:
        return self._selection.selection_summary()

    @Property(int, notify=jobSummaryChanged)
    def overallProgress(self) -> int:
        return self._job_list.overall_progress()

    @Property(str, notify=jobSummaryChanged)
    def jobCountSummary(self) -> str:
        waiting, completed, failed, cancelled = self._job_list.counts()
        return f"대기/진행: {waiting}개    완료: {completed}개    실패: {failed}개    취소: {cancelled}개"

    @Property(str, notify=statusTextChanged)
    def statusText(self) -> str:
        return self._status_text

    @Property(str, constant=True)
    def logoPath(self) -> str:
        return QUrl.fromLocalFile(str(self._app_dir / "assets" / "posid_logo.png")).toString()

    @Property(str, constant=True)
    def aiResearchImagePath(self) -> str:
        return QUrl.fromLocalFile(str(self._app_dir / "assets" / "AIResearch.png")).toString()

    @Property(str, constant=True)
    def appVersion(self) -> str:
        return APP_VERSION

    @Property(str, constant=True)
    def buildDate(self) -> str:
        return BUILD_DATE

    # --------------------------- UI actions -----------------------------
    @Slot(int)
    def toggleFolderExpanded(self, row: int) -> None:
        self._folder_tree.toggle_expanded(row)

    @Slot(int)
    def activateFolder(self, row: int) -> None:
        self._folder_tree.activate(row)

    @Slot(int)
    def toggleFolderSelected(self, row: int) -> None:
        self._folder_tree.toggle_checked(row)
        self._file_list.refresh_checks()
        self.selectionSummaryChanged.emit()

    @Slot(int)
    def toggleFileSelected(self, row: int) -> None:
        self._file_list.toggle(row)
        self.selectionSummaryChanged.emit()

    @Slot(bool)
    def selectAllVisibleFiles(self, selected: bool) -> None:
        self._file_list.set_all(selected)
        self.selectionSummaryChanged.emit()

    @Slot()
    def clearSelection(self) -> None:
        self._selection.clear()
        self._folder_tree.refresh_checks()
        self._file_list.refresh_checks()
        self.selectionSummaryChanged.emit()

    @Slot()
    def refreshCurrentFolder(self) -> None:
        self._file_list.reload()
        self.currentFolderChanged.emit()

    @Slot()
    def chooseSourceFolder(self) -> None:
        folder = QFileDialog.getExistingDirectory(None, "탐색할 폴더 선택", self.currentFolder)
        if folder:
            self._on_folder_activated(folder)

    @Slot()
    def chooseOutputFolder(self) -> None:
        dialog = QFileDialog(None, "변환 결과 폴더 선택", self._output_folder)
        dialog.setFileMode(QFileDialog.Directory)
        dialog.setOption(QFileDialog.ShowDirsOnly, False)
        dialog.setOption(QFileDialog.DontUseNativeDialog, True)
        if dialog.exec() == QFileDialog.Accepted:
            folders = dialog.selectedFiles()
            if folders:
                self._output_folder = folders[0]
                self._preferences.setValue("outputFolder", folders[0])
                self.outputFolderChanged.emit()

    @Slot(str)
    def setConversionMode(self, mode: str) -> None:
        if mode not in {"hwpx", "pdf", "image"} or self._busy:
            return
        if self._conversion_mode != mode:
            self._conversion_mode = mode
            self._preferences.setValue("conversionMode", mode)
            self.conversionModeChanged.emit()

    @Slot(str)
    def setImageFormat(self, image_format: str) -> None:
        value = image_format.lower()
        if value not in {"png", "jpg", "tiff"}:
            return
        if self._image_format != value:
            self._image_format = value
            self._preferences.setValue("imageFormat", value)
            self.imageFormatChanged.emit()

    @Slot(bool)
    def setPreserveStructure(self, value: bool) -> None:
        if self._preserve_structure != value:
            self._preserve_structure = value
            self._preferences.setValue("preserveStructure", value)
            self.preserveStructureChanged.emit()

    @Slot(bool)
    def setOverwrite(self, value: bool) -> None:
        if self._overwrite != value:
            self._overwrite = value
            self._preferences.setValue("overwrite", value)
            self.overwriteChanged.emit()

    @Slot(bool)
    def setOpenAfterComplete(self, value: bool) -> None:
        if self._open_after_complete != value:
            self._open_after_complete = value
            self._preferences.setValue("openAfterComplete", value)
            self.openAfterCompleteChanged.emit()

    @Slot()
    def startConversion(self) -> None:
        if self._busy:
            return
        output_root = Path(self._output_folder)
        try:
            output_root.mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            self.notify.emit("출력 폴더 오류", f"출력 폴더를 만들 수 없습니다.\n{exc}", "error")
            return

        sources = self._selection.enumerate_sources(target_extensions(self._conversion_mode))
        if not sources:
            self.notify.emit("변환할 파일 없음", "현재 변환 형식에 맞는 파일을 선택해 주세요.", "warning")
            return
        if self._conversion_mode == "image" and len(sources) != 1:
            self.notify.emit("이미지 변환 선택 제한", "이미지 변환은 문서 파일을 한 개만 선택할 수 있습니다.", "warning")
            return
        if self._conversion_mode == "hwpx" and sys.platform != "win32":
            self.notify.emit("Windows 환경 필요", "HWPX 변환은 한글 프로그램의 Windows COM 자동화가 필요합니다.", "error")
            return

        jobs: list[ConversionJob] = []
        reserved_destinations: set[str] = set()
        for source in sources:
            if self._conversion_mode == "image":
                destination = output_image_directory(
                    source.path,
                    source.source_root,
                    output_root,
                    self._preserve_structure,
                    self._overwrite,
                )
            else:
                suffix = ".hwpx" if self._conversion_mode == "hwpx" else ".pdf"
                destination = output_file_path(
                    source.path,
                    source.source_root,
                    output_root,
                    suffix,
                    self._preserve_structure,
                    self._overwrite,
                )
                destination = reserve_batch_file_path(destination, reserved_destinations)
            reserved_destinations.add(normalize_path(destination))
            jobs.append(
                ConversionJob(
                    input_path=source.path,
                    output_path=destination,
                    source_root=source.source_root,
                    mode=self._conversion_mode,
                    image_format=self._image_format,
                )
            )

        self._job_list.set_jobs(jobs)
        self._set_busy(True)
        self._set_status("변환 작업 진행 중")
        self._worker = ConversionWorker(jobs, self._app_settings, self)
        self._worker.jobChanged.connect(self._on_job_changed)
        self._worker.jobFinished.connect(self._on_job_finished)
        self._worker.allFinished.connect(self._on_all_finished)
        self._worker.start()

    @Slot()
    def cancelConversion(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.request_cancel()
            self._set_status("취소 요청 중")

    @Slot(int)
    def toggleJobSelected(self, row: int) -> None:
        if not self._busy:
            self._job_list.toggle_selected(row)

    @Slot()
    def removeSelectedJobs(self) -> None:
        if not self._busy:
            self._job_list.remove_selected()

    @Slot()
    def clearJobs(self) -> None:
        if not self._busy:
            self._job_list.clear()

    @Slot()
    def clearHistory(self) -> None:
        self._history.clear()

    @Slot(str)
    def openPath(self, path: str) -> None:
        if not path:
            return
        target = Path(path)
        if target.is_file():
            target = target.parent
        if target.exists():
            QDesktopServices.openUrl(QUrl.fromLocalFile(str(target)))

    @Slot()
    def openOutputFolder(self) -> None:
        self.openPath(self._output_folder)

    # --------------------------- Internal --------------------------------
    def _on_folder_activated(self, folder: str) -> None:
        self._file_list.set_folder(folder)
        self.currentFolderChanged.emit()

    def _on_job_changed(self, job_id: str, status: str, progress: int, message: str) -> None:
        self._job_list.update(job_id, status=status, progress=progress, message=message)

    def _on_job_finished(self, job_id: str) -> None:
        found = self._job_list.find(job_id)
        if found:
            _, job = found
            self._history.append_job(job)

    def _on_all_finished(self, was_cancelled: bool) -> None:
        self._set_busy(False)
        self._set_status("취소됨" if was_cancelled else "작업 완료")
        self._worker = None
        _, completed, failed, cancelled = self._job_list.counts()
        if self._open_after_complete and completed:
            self.openOutputFolder()
        if failed:
            self.notify.emit("변환 작업 완료", f"완료 {completed}개, 실패 {failed}개, 취소 {cancelled}개입니다.", "warning")
        else:
            self.notify.emit("변환 작업 완료", f"완료 {completed}개, 취소 {cancelled}개입니다.", "info")

    def _set_busy(self, value: bool) -> None:
        if self._busy != value:
            self._busy = value
            self.busyChanged.emit()

    def _set_status(self, value: str) -> None:
        if self._status_text != value:
            self._status_text = value
            self.statusTextChanged.emit()

    def shutdown(self) -> None:
        if self._worker and self._worker.isRunning():
            self._worker.request_cancel()
            self._worker.wait(5_000)
