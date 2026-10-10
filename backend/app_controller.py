from __future__ import annotations

import sys
from dataclasses import replace
from pathlib import Path

from PySide6.QtCore import Property, QObject, QSettings, QUrl, Signal, Slot
from PySide6.QtGui import QDesktopServices
from PySide6.QtWidgets import QFileDialog

from backend.file_list_model import FileListModel
from backend.file_types import target_extensions
from backend.folder_tree_model import FolderTreeModel
from backend.job_model import ConversionJob, JobListModel
from backend.path_utils import (
    normalize_path,
    output_file_path,
    reserve_batch_file_path,
)
from backend.selection_manager import SelectionManager
from backend.settings import AppSettings
from backend.version import APP_VERSION, BUILD_DATE
from backend.worker import ConversionWorker


class AppController(QObject):
    outputFolderChanged = Signal()
    conversionModeChanged = Signal()
    imageFormatChanged = Signal()
    pdfConversionMethodChanged = Signal()
    overwriteChanged = Signal()
    busyChanged = Signal()
    currentFolderChanged = Signal()
    quickAccessChanged = Signal()
    columnOrderChanged = Signal()
    selectionSummaryChanged = Signal()
    jobSummaryChanged = Signal()
    statusTextChanged = Signal()
    notify = Signal(str, str, str)

    def __init__(self, app_dir: Path, parent=None) -> None:
        super().__init__(parent)
        self._app_dir = app_dir
        settings_path = app_dir / "appsettings.json"
        if getattr(sys, "frozen", False):
            external_settings = Path(sys.executable).parent / "appsettings.json"
            if external_settings.is_file():
                settings_path = external_settings
        self._app_settings = AppSettings.load(settings_path)
        self._preferences = QSettings()
        saved_pins = self._preferences.value("pinnedFolders", [], list)
        self._pinned_folders = list(dict.fromkeys(str(path) for path in saved_pins if path)) if isinstance(saved_pins, list) else []
        self._selection = SelectionManager()
        self._folder_tree = FolderTreeModel(self)
        self._file_list = FileListModel(self._selection, self)
        self._job_list = JobListModel(self)

        default_output = Path.home() / "Documents" / "POSID 변환결과"
        saved_output = self._preferences.value("outputFolder", str(default_output), str)
        self._output_folder = str(Path(saved_output))
        self._conversion_mode = "pdf"
        self._image_format = self._preferences.value("imageFormat", "png", str)
        self._pdf_conversion_method = self._preferences.value("pdfConversionMethod", "original", str)
        if self._pdf_conversion_method not in {"original", "libreoffice"}:
            self._pdf_conversion_method = "original"
        self._overwrite = self._preferences.value("overwrite", False, bool)
        default_columns = ["modified", "size", "type"]
        saved_columns = self._preferences.value("fileListColumnOrder", default_columns, list)
        self._column_order = [str(column) for column in saved_columns] if isinstance(saved_columns, list) else default_columns
        if sorted(self._column_order) != sorted(default_columns):
            self._column_order = default_columns
        default_widths = {"name": 240, "type": 86, "size": 76, "modified": 130}
        saved_widths = self._preferences.value("fileListColumnWidths", default_widths)
        self._column_widths = dict(default_widths)
        if isinstance(saved_widths, dict):
            for column, width in saved_widths.items():
                if column in self._column_widths:
                    try:
                        self._column_widths[column] = min(600, max(50, int(width)))
                    except (TypeError, ValueError):
                        continue
        self._busy = False
        self._status_text = "대기 중"
        self._worker: ConversionWorker | None = None

        self._folder_tree.folderActivated.connect(self._on_folder_activated)
        self._file_list.folderActivated.connect(self._on_folder_activated)
        self._folder_tree.set_quick_access(self._quick_access_entries())
        self._folder_tree.set_current_path(self._file_list.folder)
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

    # --------------------------- Properties -----------------------------
    @Property(str, notify=outputFolderChanged)
    def outputFolder(self) -> str:
        return self._output_folder

    @Property("QVariantList", notify=quickAccessChanged)
    def quickAccessFolders(self) -> list[dict]:
        return self._quick_access_entries()

    def _quick_access_entries(self) -> list[dict]:
        folders = [{**entry, "canUnpin": False} for entry in FolderTreeModel.quick_access_folders()]
        seen = {normalize_path(entry["path"]) for entry in folders if entry["path"]}
        for path in self._pinned_folders:
            key = normalize_path(path)
            if key not in seen:
                folders.append({
                    "label": Path(path).name or path,
                    "path": path,
                    "icon": "folder",
                    "iconSource": "image://filesystem/folder",
                    "canUnpin": True,
                })
                seen.add(key)
        return folders

    @Property("QVariantList", notify=columnOrderChanged)
    def fileListColumnOrder(self) -> list[str]:
        return list(self._column_order)

    @Property("QVariantMap", notify=columnOrderChanged)
    def fileListColumnWidths(self) -> dict[str, int]:
        return dict(self._column_widths)

    @Property("QVariantList", notify=currentFolderChanged)
    def currentBreadcrumbs(self) -> list[dict[str, str]]:
        path = self._file_list.folder.absolute()
        return [
            {"label": ancestor.name or ancestor.anchor.rstrip("\\/") or ancestor.anchor, "path": str(ancestor)}
            for ancestor in [*reversed(path.parents), path]
        ]

    @Property(str, notify=conversionModeChanged)
    def conversionMode(self) -> str:
        return self._conversion_mode

    @Property(str, notify=imageFormatChanged)
    def imageFormat(self) -> str:
        return self._image_format

    @Property(str, notify=pdfConversionMethodChanged)
    def pdfConversionMethod(self) -> str:
        return self._pdf_conversion_method

    @Property(bool, notify=overwriteChanged)
    def overwrite(self) -> bool:
        return self._overwrite

    @Property(bool, notify=busyChanged)
    def busy(self) -> bool:
        return self._busy

    @Property(str, notify=currentFolderChanged)
    def currentFolder(self) -> str:
        return str(self._file_list.folder)

    @Property(str, notify=currentFolderChanged)
    def currentFolderSummary(self) -> str:
        return f"폴더 {self._file_list.folder_count}개 · 문서 파일 {self._file_list.count}개"

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
    def signaturePath(self) -> str:
        return QUrl.fromLocalFile(str(self._app_dir / "assets" / "posid_signature.png")).toString()

    @Property(str, constant=True)
    def signatureWhitePath(self) -> str:
        return QUrl.fromLocalFile(str(self._app_dir / "assets" / "posid_signature_white.png")).toString()

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

    @Slot(str)
    def navigateToFolder(self, path: str) -> None:
        if path and Path(path).is_dir():
            self._folder_tree.select_path(path)
        else:
            self.notify.emit("폴더 없음", "탐색할 폴더가 없습니다. 경로를 확인해 주세요.", "warning")

    @Slot(str, str, result=bool)
    def sameFolderPath(self, first: str, second: str) -> bool:
        return bool(first and second) and normalize_path(first) == normalize_path(second)

    @Slot(str)
    def pinFolder(self, path: str) -> None:
        if not path or not Path(path).is_dir():
            return
        if any(self.sameFolderPath(path, entry["path"]) for entry in self.quickAccessFolders):
            return
        self._pinned_folders.append(str(Path(path).absolute()))
        self._preferences.setValue("pinnedFolders", self._pinned_folders)
        self._folder_tree.set_quick_access(self._quick_access_entries())
        self.quickAccessChanged.emit()

    @Slot(str)
    def unpinFolder(self, path: str) -> None:
        remaining = [folder for folder in self._pinned_folders if not self.sameFolderPath(folder, path)]
        if remaining != self._pinned_folders:
            self._pinned_folders = remaining
            self._preferences.setValue("pinnedFolders", self._pinned_folders)
            self._folder_tree.set_quick_access(self._quick_access_entries())
            self.quickAccessChanged.emit()

    @Slot(int)
    def openListedFolder(self, row: int) -> None:
        self._file_list.activate_folder(row)

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
        self._file_list.refresh_checks()
        self.selectionSummaryChanged.emit()

    @Slot()
    def refreshCurrentFolder(self) -> None:
        self._folder_tree.refresh()
        self._file_list.reload()
        self.currentFolderChanged.emit()

    @Slot()
    def chooseSourceFolder(self) -> None:
        folder = QFileDialog.getExistingDirectory(None, "탐색할 폴더 선택", self.currentFolder)
        if folder:
            self.pinFolder(folder)
            self._folder_tree.select_path(folder)

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
        if mode != "pdf" or self._busy:
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

    @Slot(str)
    def setPdfConversionMethod(self, method: str) -> None:
        if method not in {"original", "libreoffice"} or self._busy or method == self._pdf_conversion_method:
            return
        self._pdf_conversion_method = method
        self._preferences.setValue("pdfConversionMethod", method)
        self.pdfConversionMethodChanged.emit()

    @Slot("QVariantList")
    def setFileListColumnOrder(self, order: list) -> None:
        columns = [str(column) for column in order]
        if sorted(columns) != ["modified", "size", "type"] or columns == self._column_order:
            return
        self._column_order = columns
        self._preferences.setValue("fileListColumnOrder", columns)
        self.columnOrderChanged.emit()

    @Slot(str, int)
    def setFileListColumnWidth(self, column: str, width: int) -> None:
        if column not in self._column_widths:
            return
        clamped = min(600, max(50, width))
        if clamped == self._column_widths[column]:
            return
        self._column_widths[column] = clamped
        self._preferences.setValue("fileListColumnWidths", self._column_widths)
        self.columnOrderChanged.emit()

    @Slot(bool)
    def setOverwrite(self, value: bool) -> None:
        if self._overwrite != value:
            self._overwrite = value
            self._preferences.setValue("overwrite", value)
            self.overwriteChanged.emit()

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

        sources = self._selection.enumerate_sources(target_extensions("pdf"))
        if not sources:
            self.notify.emit("변환할 파일 없음", "PDF로 변환할 문서를 선택해 주세요.", "warning")
            return

        jobs: list[ConversionJob] = []
        reserved_destinations: set[str] = set()
        for source in sources:
            destination = output_file_path(
                source.path,
                source.source_root,
                output_root,
                ".pdf",
                False,
                self._overwrite,
            )
            destination = reserve_batch_file_path(destination, reserved_destinations)
            reserved_destinations.add(normalize_path(destination))
            jobs.append(
                ConversionJob(
                    input_path=source.path,
                    output_path=destination,
                    source_root=source.source_root,
                    mode="pdf",
                    image_format=self._image_format,
                )
            )

        self._job_list.set_jobs(jobs)
        self._set_busy(True)
        self._set_status("변환 작업 진행 중")
        settings = replace(self._app_settings, prefer_libreoffice_pdf=self._pdf_conversion_method == "libreoffice")
        self._worker = ConversionWorker(jobs, settings, self)
        self._worker.jobChanged.connect(self._on_job_changed)
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
        self._folder_tree.set_current_path(self._file_list.folder)
        self.currentFolderChanged.emit()

    def _on_job_changed(self, job_id: str, status: str, progress: int, message: str) -> None:
        self._job_list.update(job_id, status=status, progress=progress, message=message)

    def _on_all_finished(self, was_cancelled: bool) -> None:
        self._set_busy(False)
        self._set_status("취소됨" if was_cancelled else "작업 완료")
        self._worker = None
        _, completed, failed, cancelled = self._job_list.counts()
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
