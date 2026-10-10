from pathlib import Path
from unittest.mock import Mock

import pytest
from PySide6.QtCore import QCoreApplication, QEvent, QPoint, QPointF, QSize, Qt, QUrl
from PySide6.QtQml import QQmlApplicationEngine
from PySide6.QtQuick import QQuickView
from PySide6.QtTest import QAbstractItemModelTester, QTest
from PySide6.QtWidgets import QApplication

import backend.app_controller as controller_module
from backend.app_controller import AppController
from backend.file_icon_provider import FileIconProvider
from backend.folder_tree_model import FolderTreeModel
from backend.history_model import HistoryModel
from backend.selection_manager import SelectionManager


@pytest.fixture(scope="module")
def application():
    app = QApplication.instance() or QApplication([])
    yield app


def tree_row(model, path) -> int:
    target = str(Path(path))
    for row in range(model.rowCount()):
        if model.data(model.index(row), model.PathRole) == target:
            return row
    return -1


@pytest.fixture
def tree(tmp_path, monkeypatch, application):
    monkeypatch.setattr(FolderTreeModel, "_build_roots", lambda self: [])
    model = FolderTreeModel()
    tester = QAbstractItemModelTester(model, QAbstractItemModelTester.FailureReportingMode.Warning)
    model.add_root(tmp_path)
    model._tester = tester
    return model


def test_tree_has_no_file_selection_api(tree):
    assert b"checked" not in tree.roleNames().values()
    assert not hasattr(tree, "toggle_checked")
    assert not hasattr(tree, "_selection")


def test_tree_contains_only_folders_and_counts_immediate_items(tree, tmp_path):
    (tmp_path / "empty").mkdir()
    (tmp_path / "nested").mkdir()
    (tmp_path / "nested" / "child").mkdir()
    (tmp_path / "document.docx").write_text("document")
    (tmp_path / ".hidden").mkdir()
    tree.refresh()
    root_row = tree_row(tree, tmp_path)
    assert tree.data(tree.index(root_row), tree.ChildCountRole) == 3
    tree.toggle_expanded(root_row)
    assert tree.rowCount() == 5
    children = [tree.index(root_row + 1), tree.index(root_row + 2)]
    assert [tree.data(row, tree.NameRole) for row in children] == ["empty", "nested"]
    assert all(Path(tree.data(tree.index(row), tree.PathRole)).is_dir() for row in range(tree.rowCount()) if tree.data(tree.index(row), tree.PathRole))
    assert tree.data(children[0], tree.ChildCountRole) == 0
    assert tree.data(children[0], tree.DepthRole) == 2


def test_chevron_changes_expansion_without_navigation(tree, tmp_path):
    (tmp_path / "nested").mkdir()
    tree.refresh()
    activated = Mock()
    tree.folderActivated.connect(activated)
    tree.set_current_path(tmp_path)
    root_row = tree_row(tree, tmp_path)
    tree.toggle_expanded(root_row)
    assert tree.data(tree.index(root_row), tree.ExpandedRole)
    assert tree.data(tree.index(root_row), tree.ActiveRole)
    tree.toggle_expanded(root_row)
    assert tree.rowCount() == 3
    activated.assert_not_called()


def test_empty_folder_activation_does_not_expand(tree, tmp_path):
    activated = Mock()
    tree.folderActivated.connect(activated)
    root_row = tree_row(tree, tmp_path)
    tree.activate(root_row)
    activated.assert_called_once_with(str(tmp_path))
    assert not tree.data(tree.index(root_row), tree.ExpandedRole)
    assert tree.data(tree.index(root_row), tree.ChildCountRole) == 0


def test_section_activation_does_not_navigate(tree):
    activated = Mock()
    tree.folderActivated.connect(activated)
    tree.activate(0)
    activated.assert_not_called()
    assert tree.data(tree.index(0), tree.KindRole) == "section"


def test_refresh_preserves_expansion_and_active_path(tree, tmp_path):
    child = tmp_path / "nested"
    child.mkdir()
    tree.refresh()
    root_row = tree_row(tree, tmp_path)
    tree.toggle_expanded(root_row)
    tree.set_current_path(child)
    (tmp_path / "new").mkdir()
    tree.refresh()
    assert tree.rowCount() == 5
    root_row = tree_row(tree, tmp_path)
    assert tree.data(tree.index(root_row), tree.ExpandedRole)
    assert tree.data(tree.index(root_row + 1), tree.ActiveRole)
    assert not tree.data(tree.index(root_row + 2), tree.ActiveRole)


def test_add_root_is_navigation_only_and_deduplicated(tree, tmp_path):
    other = tmp_path / "other"
    other.mkdir()
    activated = Mock()
    tree.folderActivated.connect(activated)
    tree.add_root(other)
    tree.add_root(other / ".")
    assert tree.rowCount() == 4
    assert tree.data(tree.index(tree_row(tree, other)), tree.DepthRole) == 1
    activated.assert_not_called()


def test_invalid_root_and_file_are_not_added(tree, tmp_path):
    document = tmp_path / "a.docx"
    document.touch()
    tree.add_root(document)
    tree.add_root(tmp_path / "missing")
    assert tree.rowCount() == 3


@pytest.fixture
def controller(tmp_path, monkeypatch, application):
    preferences = Mock()
    preferences.value.side_effect = lambda key, default, value_type=None: default
    monkeypatch.setattr(controller_module, "QSettings", lambda: preferences)
    monkeypatch.setattr(controller_module, "HistoryModel", lambda path, max_items, parent: HistoryModel(tmp_path / "history.json", max_items, parent))
    monkeypatch.setattr(FolderTreeModel, "_build_roots", lambda self: [])
    instance = AppController(tmp_path)
    instance._output_folder = str(tmp_path / "out")
    instance._conversion_mode = "pdf"
    return instance


def test_navigation_preserves_file_selection_and_updates_path(controller, tmp_path):
    first = tmp_path / "first"
    second = tmp_path / "empty"
    first.mkdir()
    second.mkdir()
    document = first / "a.docx"
    document.touch()
    controller._folder_tree.add_root(first)
    controller._folder_tree.add_root(second)
    first_row = tree_row(controller._folder_tree, first)
    second_row = tree_row(controller._folder_tree, second)
    controller.activateFolder(first_row)
    controller.toggleFileSelected(0)
    changed = Mock()
    controller.currentFolderChanged.connect(changed)
    controller.activateFolder(second_row)
    assert controller.currentFolder == str(second)
    assert controller._file_list.count == 0
    assert controller._selection.is_file_selected(document)
    assert controller._selection.selected_folder_count == 0
    assert controller._folder_tree.data(controller._folder_tree.index(second_row), FolderTreeModel.ActiveRole)
    controller.activateFolder(first_row)
    assert controller._file_list.data(controller._file_list.index(0), controller._file_list.CheckedRole)
    assert changed.call_count == 2


def test_quick_access_contains_standard_and_pinned_folders_only(controller, tmp_path):
    assert [entry["label"] for entry in controller.quickAccessFolders] == ["바탕 화면", "다운로드", "문서"]
    controller.pinFolder(str(tmp_path))
    controller.pinFolder(str(tmp_path / "."))
    assert len(controller.quickAccessFolders) == 4
    assert controller.quickAccessFolders[-1]["path"] == str(tmp_path)
    assert controller.quickAccessFolders[-1]["canUnpin"]
    controller.navigateToFolder(str(tmp_path))
    assert controller.currentFolder == str(tmp_path)
    quick_row = tree_row(controller._folder_tree, tmp_path)
    assert quick_row > 0
    assert controller._folder_tree.data(controller._folder_tree.index(quick_row), FolderTreeModel.IsQuickRole)
    assert controller._folder_tree.data(controller._folder_tree.index(quick_row), FolderTreeModel.CanUnpinRole)
    assert controller.sameFolderPath(str(tmp_path), str(tmp_path / "."))
    assert controller._selection.explicit_file_count == 0
    controller.unpinFolder(str(tmp_path))
    assert len(controller.quickAccessFolders) == 3
    assert tree_row(controller._folder_tree, tmp_path) == -1
    assert controller.currentFolder == str(tmp_path)


def test_choose_source_folder_pins_without_selecting_files(controller, tmp_path, monkeypatch):
    document = tmp_path / "a.docx"
    document.touch()
    monkeypatch.setattr(controller_module.QFileDialog, "getExistingDirectory", lambda *args: str(tmp_path))
    controller.chooseSourceFolder()
    assert controller.quickAccessFolders[-1]["path"] == str(tmp_path)
    assert tree_row(controller._folder_tree, tmp_path) > 0
    assert controller.currentFolder == str(tmp_path)
    assert controller.selectionSummary == "선택된 항목 없음"


def test_select_all_deselect_and_clear_do_not_change_navigation(controller, tmp_path):
    for name in ("a.docx", "b.docx"):
        (tmp_path / name).touch()
    controller._folder_tree.add_root(tmp_path)
    root_row = tree_row(controller._folder_tree, tmp_path)
    controller.activateFolder(root_row)
    controller.selectAllVisibleFiles(True)
    assert controller._selection.explicit_file_count == 2
    controller.selectAllVisibleFiles(False)
    assert controller._selection.explicit_file_count == 0
    controller.toggleFileSelected(0)
    controller.clearSelection()
    assert controller.currentFolder == str(tmp_path)
    assert controller._folder_tree.data(controller._folder_tree.index(root_row), FolderTreeModel.ActiveRole)
    assert controller._selection.enumerate_sources({".docx"}) == []


def test_conversion_queue_contains_checked_files_only_after_navigation(controller, tmp_path, monkeypatch):
    source = tmp_path / "source"
    source.mkdir()
    selected = source / "a.docx"
    selected.touch()
    (source / "b.docx").touch()
    empty = tmp_path / "empty"
    empty.mkdir()
    controller.navigateToFolder(str(source))
    controller.toggleFileSelected(0)
    controller.navigateToFolder(str(empty))
    worker = Mock()
    factory = Mock(return_value=worker)
    monkeypatch.setattr(controller_module, "ConversionWorker", factory)
    controller.startConversion()
    jobs = factory.call_args.args[0]
    assert [job.input_path for job in jobs] == [selected]
    assert jobs[0].source_root == source
    assert controller._selection.selected_folder_count == 0
    worker.start.assert_called_once()


def test_pdf_conversion_method_is_saved_and_passed_to_worker(controller, tmp_path, monkeypatch):
    assert controller.pdfConversionMethod == "original"
    controller.setPdfConversionMethod("libreoffice")
    controller._preferences.setValue.assert_called_with("pdfConversionMethod", "libreoffice")
    controller.setPdfConversionMethod("invalid")
    assert controller.pdfConversionMethod == "libreoffice"
    controller._preferences.value.side_effect = lambda key, default, value_type=None: "libreoffice" if key == "pdfConversionMethod" else default
    restored = AppController(tmp_path)
    assert restored.pdfConversionMethod == "libreoffice"

    document = tmp_path / "input.docx"
    document.touch()
    restored.navigateToFolder(str(tmp_path))
    file_row = next(row for row in range(restored._file_list.rowCount()) if restored._file_list.data(restored._file_list.index(row), restored._file_list.PathRole) == str(document))
    restored.toggleFileSelected(file_row)
    worker = Mock()
    factory = Mock(return_value=worker)
    monkeypatch.setattr(controller_module, "ConversionWorker", factory)
    restored.startConversion()
    assert factory.call_args.args[1].prefer_libreoffice_pdf is True
    worker.start.assert_called_once()


def test_invalid_saved_pdf_conversion_method_defaults_to_original(controller, tmp_path):
    controller._preferences.value.side_effect = lambda key, default, value_type=None: "invalid" if key == "pdfConversionMethod" else default
    assert AppController(tmp_path).pdfConversionMethod == "original"


def test_file_list_sort_by_column_and_direction(controller, tmp_path):
    folder = tmp_path / "sorted"
    folder.mkdir()
    (folder / "b.docx").write_bytes(b"bb")
    (folder / "a.hwp").write_bytes(b"aaaa")
    controller.navigateToFolder(str(folder))
    model = controller._file_list

    def names():
        return [model.data(model.index(row), model.NameRole) for row in range(model.rowCount())]

    assert names() == ["a.hwp", "b.docx"]

    model.setSort("size")
    assert names() == ["b.docx", "a.hwp"]
    model.setSort("size")
    assert names() == ["a.hwp", "b.docx"]

    model.setSort("type")
    assert names() == ["b.docx", "a.hwp"]


def test_file_list_sort_keeps_files_first(controller, tmp_path):
    folder = tmp_path / "mixed"
    folder.mkdir()
    (folder / "aaa").mkdir()
    (folder / "zzz.docx").touch()
    controller.navigateToFolder(str(folder))
    model = controller._file_list

    model.setSort("name")
    model.setSort("name")
    assert model.data(model.index(0), model.NameRole) == "zzz.docx"
    assert model.data(model.index(1), model.IsFolderRole)


def test_folder_navigation_does_not_create_a_folder_selection(controller):
    assert not hasattr(controller, "toggleFolderSelected")
    assert isinstance(controller._selection, SelectionManager)


def visual_items(item, name):
    result = [item] if item.objectName() == name else []
    for child in item.childItems():
        result.extend(visual_items(child, name))
    return result


def click_item(view, item, x=None):
    point = item.mapToScene(QPointF(item.width() / 2 if x is None else x, item.height() / 2))
    QTest.mouseClick(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(point.x()), round(point.y())))
    QTest.qWait(30)


@pytest.fixture
def panel(controller, tmp_path, application):
    source = tmp_path / "source"
    (source / "empty").mkdir(parents=True)
    (source / "a.docx").touch()
    other = tmp_path / "other"
    other.mkdir()
    (other / "b.docx").touch()
    controller._folder_tree.add_root(source)
    controller._folder_tree.add_root(other)
    controller._output_folder = str(other)
    controller.navigateToFolder(str(other))
    view = QQuickView()
    view.engine().addImageProvider("filesystem", FileIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(290, 480)
    view.rootContext().setContextProperty("appController", controller)
    warnings = []
    view.engine().warnings.connect(lambda messages: warnings.extend(message.toString() for message in messages))
    qml = Path(__file__).resolve().parents[1] / "qml" / "components" / "FolderTreePanel.qml"
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [error.toString() for error in view.errors()]
    view.show()
    QTest.qWait(100)
    yield view, source, other, warnings
    view.close()
    view.setSource(QUrl())


def find_tree_row(view, path):
    target = str(Path(path))
    return next(
        row for row in visual_items(view.rootObject(), "folderTreeRow")
        if row.property("folderPath") == target
    )


def test_qml_folder_icon_and_name_navigate_without_expanding_or_selecting(panel, controller):
    view, source, other, warnings = panel
    controller.toggleFileSelected(0)
    row = find_tree_row(view, source)
    assert row.height() == 32
    click_item(view, row, 48)
    assert controller.currentFolder == str(source)
    assert controller._selection.is_file_selected(other / "b.docx")
    assert controller._selection.explicit_file_count == 1
    assert controller._selection.selected_folder_count == 0
    click_item(view, row, 110)
    assert controller.currentFolder == str(source)
    assert not row.property("expanded")
    assert row.property("activeFolder")
    assert row.property("color").name().upper() == "#E9E9E9"
    assert row.property("radius") > 0
    assert warnings == []


def test_qml_chevron_only_expands_and_empty_folder_can_be_opened(panel, controller):
    view, source, other, warnings = panel
    row = find_tree_row(view, source)
    chevron = visual_items(row, "folderChevron")[0]
    click_item(view, chevron)
    assert controller.currentFolder == str(other)
    assert len(controller.quickAccessFolders) == 3
    empty_row = find_tree_row(view, source / "empty")
    assert empty_row.property("depth") == row.property("depth") + 1
    click_item(view, empty_row, 100)
    assert controller.currentFolder == str(source / "empty")
    assert controller._file_list.count == 0
    click_item(view, chevron)
    assert controller.currentFolder == str(source / "empty")
    assert not row.property("expanded")
    assert warnings == []


def test_qml_quick_access_folders_expand_in_tree(panel, controller):
    view, source, other, warnings = panel
    controller.pinFolder(str(other))
    QTest.qWait(30)
    quick_rows = [row for row in visual_items(view.rootObject(), "folderTreeRow") if row.property("isQuick")]
    assert len(quick_rows) == 4
    pinned = next(row for row in quick_rows if row.property("folderPath") == str(other))
    assert pinned.property("activeFolder")
    assert pinned.property("canUnpin")
    controller.navigateToFolder(str(source))
    QTest.qWait(30)
    assert not pinned.property("activeFolder")
    click_item(view, pinned, 80)
    assert controller.currentFolder == str(other)
    assert pinned.property("activeFolder")
    assert controller._selection.explicit_file_count == 0
    assert warnings == []


def test_qml_panel_has_no_checkbox_or_double_click_expansion(panel, controller):
    view, source, other, warnings = panel
    pending = [view.rootObject()]
    while pending:
        item = pending.pop()
        assert "CheckBox" not in item.metaObject().className()
        pending.extend(item.childItems())
    row = find_tree_row(view, source)
    point = row.mapToScene(QPointF(110, 16))
    QTest.mouseDClick(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(point.x()), round(point.y())))
    QTest.qWait(30)
    assert not row.property("expanded")
    assert warnings == []


def test_qml_quick_access_rows_fit_minimum_width(panel, controller):
    view, source, other, warnings = panel
    view.resize(230, 480)
    controller.pinFolder(str(other))
    QTest.qWait(50)
    rows = [row for row in visual_items(view.rootObject(), "folderTreeRow") if row.property("isQuick")]
    assert len(rows) == 4
    for row in rows:
        position = row.mapToScene(QPointF(0, 0))
        assert position.x() >= 0
        assert position.x() + row.width() <= view.width()
    assert warnings == []


def test_breadcrumbs_navigate_to_ancestors_without_selecting_files(controller, tmp_path):
    nested = tmp_path / "a" / "b"
    nested.mkdir(parents=True)
    controller.navigateToFolder(str(nested))
    crumbs = controller.currentBreadcrumbs
    assert crumbs[-1] == {"label": "b", "path": str(nested)}
    assert crumbs[-2] == {"label": "a", "path": str(nested.parent)}
    assert crumbs[0]["path"] == nested.anchor
    controller.navigateToFolder(crumbs[-2]["path"])
    assert controller.currentFolder == str(nested.parent)
    assert controller._selection.explicit_file_count == 0


def test_folder_rows_cannot_be_checked_or_bulk_selected(controller, tmp_path):
    folder = tmp_path / "a-folder"
    folder.mkdir()
    file = tmp_path / "z.docx"
    file.touch()
    controller.navigateToFolder(str(tmp_path))
    model = controller._file_list
    assert model.rowCount() == 2
    assert model.data(model.index(1), model.IsFolderRole)
    assert model.data(model.index(1), model.SizeRole) == ""
    controller.toggleFileSelected(1)
    assert controller._selection.explicit_file_count == 0
    controller.selectAllVisibleFiles(True)
    assert controller._selection.is_file_selected(file)
    assert not model.data(model.index(1), model.CheckedRole)
    assert controller._selection.selected_folder_count == 0
    controller.openListedFolder(1)
    assert controller.currentFolder == str(folder)
    assert controller._selection.is_file_selected(file)


def test_pinned_folders_are_saved_and_restored(controller, tmp_path, monkeypatch):
    controller.pinFolder(str(tmp_path))
    controller._preferences.setValue.assert_called_with("pinnedFolders", [str(tmp_path)])
    controller._preferences.value.side_effect = lambda key, default, value_type=None: [str(tmp_path)] if key == "pinnedFolders" else default
    restored = AppController(tmp_path)
    assert restored.quickAccessFolders[-1]["path"] == str(tmp_path)
    restored.unpinFolder(str(tmp_path))
    restored._preferences.setValue.assert_called_with("pinnedFolders", [])


@pytest.fixture
def listing_panel(controller, tmp_path, application):
    source = tmp_path / "listing"
    (source / "empty").mkdir(parents=True)
    (source / "a.docx").touch()
    (source / "b.pdf").touch()
    controller.navigateToFolder(str(source))
    view = QQuickView()
    view.engine().addImageProvider("filesystem", FileIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(760, 480)
    view.rootContext().setContextProperty("appController", controller)
    warnings = []
    view.engine().warnings.connect(lambda messages: warnings.extend(message.toString() for message in messages))
    qml = Path(__file__).resolve().parents[1] / "qml" / "components" / "FileListPanel.qml"
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [error.toString() for error in view.errors()]
    view.show()
    QTest.qWait(100)
    yield view, source, warnings
    view.close()
    view.setSource(QUrl())


def test_qml_listing_folder_has_no_checkbox_and_requires_double_click(listing_panel, controller):
    view, source, warnings = listing_panel
    rows = visual_items(view.rootObject(), "fileListRow")
    folder = next(row for row in rows if row.property("isFolder"))
    files = [row for row in rows if not row.property("isFolder")]
    assert folder.property("index") == len(files)
    assert visual_items(folder, "fileCheckbox") == []
    assert len(files) == 2
    assert all(len(visual_items(row, "fileCheckbox")) == 1 for row in files)
    click_item(view, folder, 110)
    assert controller.currentFolder == str(source)
    assert controller._selection.explicit_file_count == 0
    click_item(view, visual_items(files[0], "fileCheckbox")[0])
    assert controller._selection.is_file_selected(source / "a.docx")
    point = folder.mapToScene(QPointF(110, 20))
    QTest.mouseDClick(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(point.x()), round(point.y())))
    QTest.qWait(30)
    assert controller.currentFolder == str(source / "empty")
    assert controller._selection.is_file_selected(source / "a.docx")
    assert controller._selection.selected_folder_count == 0
    assert warnings == []


def test_qml_column_header_drag_reorders_columns(listing_panel, controller):
    view, source, warnings = listing_panel
    headers = visual_items(view.rootObject(), "sortableColumnHeader")
    assert len(headers) == 3

    def texts(row):
        return [item.property("text") for item in visual_items(row, "dataCell")]

    first_row = visual_items(view.rootObject(), "fileListRow")[0]
    assert texts(first_row) == [first_row.property("modifiedText"), first_row.property("sizeText"), first_row.property("typeLabel")]

    headers = sorted(visual_items(view.rootObject(), "sortableColumnHeader"), key=lambda item: item.mapToScene(QPointF(0, 0)).x())
    start = headers[0].mapToScene(QPointF(headers[0].width() / 2, headers[0].height() / 2))
    end = headers[2].mapToScene(QPointF(headers[2].width() - 2, headers[2].height() / 2))
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(start.x()), round(start.y())))
    for step in range(1, 11):
        pos = start + (end - start) * (step / 10)
        QTest.mouseMove(view, QPoint(round(pos.x()), round(pos.y())))
        QTest.qWait(10)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(end.x()), round(end.y())))
    QTest.qWait(50)
    first_row = visual_items(view.rootObject(), "fileListRow")[0]
    assert texts(first_row) == [first_row.property("sizeText"), first_row.property("typeLabel"), first_row.property("modifiedText")]
    assert warnings == []


def test_column_order_is_saved_and_restored(controller, tmp_path):
    assert controller.fileListColumnOrder == ["modified", "size", "type"]
    controller.setFileListColumnOrder(["type", "modified", "size"])
    controller._preferences.setValue.assert_called_with("fileListColumnOrder", ["type", "modified", "size"])
    controller.setFileListColumnOrder(["type", "bogus", "size"])
    assert controller.fileListColumnOrder == ["type", "modified", "size"]
    controller._preferences.value.side_effect = lambda key, default, value_type=None: ["type", "modified", "size"] if key == "fileListColumnOrder" else default
    restored = AppController(tmp_path)
    assert restored.fileListColumnOrder == ["type", "modified", "size"]


def test_column_width_is_saved_and_restored(controller, tmp_path):
    assert controller.fileListColumnWidths == {"name": 240, "type": 86, "size": 76, "modified": 130}
    controller.setFileListColumnWidth("modified", 200)
    controller._preferences.setValue.assert_called_with("fileListColumnWidths", {"name": 240, "type": 86, "size": 76, "modified": 200})
    controller.setFileListColumnWidth("bogus", 200)
    assert "bogus" not in controller.fileListColumnWidths
    controller.setFileListColumnWidth("size", 10)
    assert controller.fileListColumnWidths["size"] == 50
    controller.setFileListColumnWidth("name", 300)
    assert controller.fileListColumnWidths["name"] == 300
    controller._preferences.value.side_effect = lambda key, default, value_type=None: {"type": 86, "size": 76, "modified": 200, "name": 300} if key == "fileListColumnWidths" else default
    restored = AppController(tmp_path)
    assert restored.fileListColumnWidths["modified"] == 200
    assert restored.fileListColumnWidths["name"] == 300


def test_qml_column_resize_handle_widens_column(listing_panel, controller):
    view, source, warnings = listing_panel
    headers = sorted(visual_items(view.rootObject(), "sortableColumnHeader"), key=lambda item: item.mapToScene(QPointF(0, 0)).x())
    handle = visual_items(headers[0], "columnResizeHandle")[0]
    start = handle.mapToScene(QPointF(handle.width() / 2, handle.height() / 2))
    end = QPointF(start.x() + 60, start.y())
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(start.x()), round(start.y())))
    for step in range(1, 11):
        pos = start + (end - start) * (step / 10)
        QTest.mouseMove(view, QPoint(round(pos.x()), round(pos.y())))
        QTest.qWait(10)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(end.x()), round(end.y())))
    QTest.qWait(50)
    assert controller.fileListColumnWidths["modified"] == 190
    assert warnings == []


def test_qml_column_titles_are_centered(listing_panel, controller):
    view, source, warnings = listing_panel
    titles = visual_items(view.rootObject(), "columnTitleRow")
    assert len(titles) == 4
    for title in titles:
        header = title.parentItem()
        title_center = title.mapToScene(QPointF(title.width() / 2, 0)).x()
        header_center = header.mapToScene(QPointF(header.width() / 2, 0)).x()
        assert abs(title_center - header_center) <= 1
    assert warnings == []


def test_qml_name_column_resize_handle_widens_column(listing_panel, controller):
    view, source, warnings = listing_panel
    name_header = visual_items(view.rootObject(), "nameColumnHeader")[0]
    handle = visual_items(name_header, "columnResizeHandle")[0]
    start_width = name_header.width()
    start = handle.mapToScene(QPointF(handle.width() / 2, handle.height() / 2))
    end = QPointF(start.x() + 40, start.y())
    QTest.mousePress(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(start.x()), round(start.y())))
    for step in range(1, 11):
        pos = start + (end - start) * (step / 10)
        QTest.mouseMove(view, QPoint(round(pos.x()), round(pos.y())))
        QTest.qWait(10)
    QTest.mouseRelease(view, Qt.LeftButton, Qt.NoModifier, QPoint(round(end.x()), round(end.y())))
    QTest.qWait(50)
    assert controller.fileListColumnWidths["name"] == round(start_width + 40)
    assert warnings == []


def test_qml_file_rows_keep_minimum_width_and_scroll_horizontally(listing_panel, controller):
    view, source, warnings = listing_panel
    view.resize(400, 480)
    QTest.qWait(50)
    file_view = visual_items(view.rootObject(), "fileListView")[0]
    rows = visual_items(view.rootObject(), "fileListRow")
    expected = 80 + sum(controller.fileListColumnWidths.values())
    assert file_view.property("contentWidth") >= expected
    assert all(row.width() >= expected for row in rows)
    file_view.setProperty("contentX", 120)
    QTest.qWait(30)
    assert file_view.property("contentX") > 0
    assert warnings == []


def test_qml_select_all_targets_files_only(listing_panel, controller):
    view, source, warnings = listing_panel
    button = visual_items(view.rootObject(), "selectAllFilesButton")[0]
    click_item(view, button)
    assert controller._selection.explicit_file_count == 2
    assert controller._selection.selected_folder_count == 0
    sources = controller._selection.enumerate_sources({".docx", ".pdf"})
    assert {item.path for item in sources} == {source / "a.docx", source / "b.pdf"}
    folder = next(row for row in visual_items(view.rootObject(), "fileListRow") if row.property("isFolder"))
    assert not folder.property("checked")
    assert warnings == []


def test_qml_breadcrumb_click_navigates_without_clearing_selection(listing_panel, controller, application, tmp_path):
    _, source, _ = listing_panel
    controller.toggleFileSelected(0)
    view = QQuickView()
    view.engine().addImageProvider("filesystem", FileIconProvider())
    view.setResizeMode(QQuickView.SizeRootObjectToView)
    view.resize(1100, 700)
    view.rootContext().setContextProperty("appController", controller)
    warnings = []
    view.engine().warnings.connect(lambda messages: warnings.extend(message.toString() for message in messages))
    qml = Path(__file__).resolve().parents[1] / "qml" / "pages" / "ConverterPage.qml"
    view.setSource(QUrl.fromLocalFile(str(qml)))
    assert view.status() == QQuickView.Ready, [error.toString() for error in view.errors()]
    view.show()
    QTest.qWait(100)
    try:
        controller.navigateToFolder(str(source / "empty"))
        QTest.qWait(50)
        crumb = next(item for item in visual_items(view.rootObject(), "breadcrumbButton") if item.property("crumbPath") == str(source))
        click_item(view, crumb)
        assert controller.currentFolder == str(source)
        assert controller._selection.is_file_selected(source / "a.docx")
        assert controller._selection.selected_folder_count == 0
        assert [w for w in warnings if "does not support customization" not in w] == []
    finally:
        view.close()
        view.setSource(QUrl())


def test_system_folder_and_drive_icons_are_available(application):
    provider = FileIconProvider()
    for identifier in ("folder", "drive"):
        size = QSize()
        pixmap = provider.requestPixmap(identifier, size, QSize(24, 24))
        assert not pixmap.isNull()
        assert size == pixmap.size()


def test_full_application_qml_still_loads(controller, application):
    project = Path(__file__).resolve().parents[1]
    controller._app_dir = project
    engine = QQmlApplicationEngine()
    engine.addImageProvider("filesystem", FileIconProvider())
    engine.rootContext().setContextProperty("appController", controller)
    warnings = []
    engine.warnings.connect(lambda messages: warnings.extend(message.toString() for message in messages))
    engine.load(QUrl.fromLocalFile(str(project / "qml" / "Main.qml")))
    assert len(engine.rootObjects()) == 1
    window = engine.rootObjects()[0]
    QTest.qWait(50)
    assert len(visual_items(window.contentItem(), "folderTreeView")) == 1
    pdf_method = visual_items(window.contentItem(), "pdfConversionMethodCombo")[0]
    assert pdf_method.parentItem().property("visible")
    assert pdf_method.property("currentIndex") == 0
    controller.setPdfConversionMethod("libreoffice")
    QTest.qWait(20)
    assert pdf_method.property("currentIndex") == 1
    controller.setConversionMode("image")
    assert not pdf_method.parentItem().property("visible")
    assert not [warning for warning in warnings if "FolderTreePanel.qml" in warning or "FileListPanel.qml" in warning]
    window.close()
    window.deleteLater()
    QCoreApplication.sendPostedEvents(window, QEvent.DeferredDelete)
