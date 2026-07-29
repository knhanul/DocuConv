from pathlib import Path

from backend.selection_manager import SelectionManager


def test_explicit_file_selection(tmp_path: Path) -> None:
    file_path = tmp_path / "a.docx"
    file_path.write_text("x")
    manager = SelectionManager()
    assert manager.toggle_file(file_path)
    assert manager.is_file_selected(file_path)
    sources = manager.enumerate_sources({".docx"})
    assert [item.path for item in sources] == [file_path]


def test_folder_selection_and_file_exclusion(tmp_path: Path) -> None:
    folder = tmp_path / "reports"
    folder.mkdir()
    include = folder / "a.docx"
    exclude = folder / "b.docx"
    other = folder / "c.txt"
    include.write_text("a")
    exclude.write_text("b")
    other.write_text("c")

    manager = SelectionManager()
    manager.toggle_folder(folder)
    assert manager.is_file_selected(include)
    manager.set_file_selected(exclude, False)
    sources = manager.enumerate_sources({".docx"})
    assert [item.path for item in sources] == [include]
    assert sources[0].source_root == folder.parent
