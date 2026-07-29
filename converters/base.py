from __future__ import annotations

import sys
from collections.abc import Callable
from pathlib import Path

ProgressCallback = Callable[[int, str], None]


class ConversionError(RuntimeError):
    pass


class DependencyMissingError(ConversionError):
    pass


class UnsupportedFormatError(ConversionError):
    pass


class ConversionCancelled(ConversionError):
    pass


def require_windows(feature: str) -> None:
    if sys.platform != "win32":
        raise DependencyMissingError(f"{feature} 기능은 Windows에서만 사용할 수 있습니다.")


def require_input_file(path: Path) -> None:
    if not path.exists() or not path.is_file():
        raise ConversionError(f"입력 파일을 찾을 수 없습니다: {path}")
