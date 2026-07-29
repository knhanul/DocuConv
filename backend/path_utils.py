from __future__ import annotations

import os
import shutil
from pathlib import Path


def normalize_path(path: str | Path) -> str:
    return os.path.normcase(os.path.abspath(os.fspath(path)))


def is_same_or_child(path: str | Path, parent: str | Path) -> bool:
    path_norm = normalize_path(path)
    parent_norm = normalize_path(parent)
    try:
        return os.path.commonpath([path_norm, parent_norm]) == parent_norm
    except ValueError:
        return False


def unique_file_path(path: Path, overwrite: bool) -> Path:
    if overwrite or not path.exists():
        return path
    for index in range(1, 10_000):
        candidate = path.with_name(f"{path.stem} ({index}){path.suffix}")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"중복 파일명을 만들 수 없습니다: {path}")


def unique_directory_path(path: Path, overwrite: bool) -> Path:
    if overwrite:
        if path.exists():
            shutil.rmtree(path)
        return path
    if not path.exists():
        return path
    for index in range(1, 10_000):
        candidate = path.with_name(f"{path.name} ({index})")
        if not candidate.exists():
            return candidate
    raise RuntimeError(f"중복 폴더명을 만들 수 없습니다: {path}")


def relative_parent(input_path: Path, source_root: Path, preserve_structure: bool) -> Path:
    if not preserve_structure:
        return Path()
    try:
        rel = input_path.parent.resolve().relative_to(source_root.resolve())
        return rel
    except (ValueError, OSError):
        return Path()


def output_file_path(
    input_path: Path,
    source_root: Path,
    output_root: Path,
    suffix: str,
    preserve_structure: bool,
    overwrite: bool,
) -> Path:
    parent = output_root / relative_parent(input_path, source_root, preserve_structure)
    parent.mkdir(parents=True, exist_ok=True)
    destination = parent / f"{input_path.stem}{suffix}"
    return unique_file_path(destination, overwrite)



def reserve_batch_file_path(destination: Path, reserved: set[str]) -> Path:
    """동일 작업 목록 안에서 아직 생성되지 않은 출력 경로 충돌도 방지합니다."""
    key = normalize_path(destination)
    if key not in reserved:
        return destination
    for index in range(1, 10_000):
        candidate = destination.with_name(f"{destination.stem} ({index}){destination.suffix}")
        candidate_key = normalize_path(candidate)
        if candidate_key not in reserved and not candidate.exists():
            return candidate
    raise RuntimeError(f"작업 내 중복 출력 파일명을 만들 수 없습니다: {destination}")

def output_image_directory(
    input_path: Path,
    source_root: Path,
    output_root: Path,
    preserve_structure: bool,
    overwrite: bool,
) -> Path:
    parent = output_root / relative_parent(input_path, source_root, preserve_structure)
    parent.mkdir(parents=True, exist_ok=True)
    return unique_directory_path(parent / input_path.stem, overwrite)
