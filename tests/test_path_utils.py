from pathlib import Path

from backend.path_utils import is_same_or_child, normalize_path, output_file_path, relative_parent, reserve_batch_file_path, unique_file_path


def test_same_or_child(tmp_path: Path) -> None:
    parent = tmp_path / "a"
    child = parent / "b" / "file.docx"
    assert is_same_or_child(child, parent)
    assert not is_same_or_child(tmp_path / "other", parent)


def test_relative_parent(tmp_path: Path) -> None:
    root = tmp_path / "root"
    source = root / "dept" / "file.docx"
    assert relative_parent(source, root, True) == Path("dept")
    assert relative_parent(source, root, False) == Path()


def test_unique_file_path(tmp_path: Path) -> None:
    target = tmp_path / "file.pdf"
    target.write_text("x")
    assert unique_file_path(target, False).name == "file (1).pdf"
    assert unique_file_path(target, True) == target


def test_output_file_path_preserves_folder(tmp_path: Path) -> None:
    source_root = tmp_path / "source"
    source = source_root / "reports" / "a.docx"
    source.parent.mkdir(parents=True)
    source.write_text("x")
    output = output_file_path(source, source_root, tmp_path / "out", ".pdf", True, False)
    assert output == tmp_path / "out" / "reports" / "a.pdf"


def test_reserve_batch_file_path(tmp_path: Path) -> None:
    destination = tmp_path / "same.pdf"
    reserved = {normalize_path(destination)}
    candidate = reserve_batch_file_path(destination, reserved)
    assert candidate.name == "same (1).pdf"
