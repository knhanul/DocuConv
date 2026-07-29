from __future__ import annotations

HWP_EXTENSIONS = {".hwp", ".hwpx"}
WORD_EXTENSIONS = {".doc", ".docx", ".docm", ".dot", ".dotx", ".rtf", ".odt"}
EXCEL_EXTENSIONS = {".xls", ".xlsx", ".xlsm", ".xlsb", ".csv"}
POWERPOINT_EXTENSIONS = {".ppt", ".pptx", ".pptm", ".pps", ".ppsx"}
PDF_EXTENSIONS = {".pdf"}

HWPX_INPUT_EXTENSIONS = {".hwp"}
PDF_INPUT_EXTENSIONS = HWP_EXTENSIONS | WORD_EXTENSIONS | EXCEL_EXTENSIONS | POWERPOINT_EXTENSIONS
IMAGE_INPUT_EXTENSIONS = PDF_INPUT_EXTENSIONS | PDF_EXTENSIONS
ALL_VISIBLE_EXTENSIONS = IMAGE_INPUT_EXTENSIONS


def normalize_extension(path: str) -> str:
    from pathlib import Path

    return Path(path).suffix.lower()


def target_extensions(mode: str) -> set[str]:
    if mode == "hwpx":
        return HWPX_INPUT_EXTENSIONS
    if mode == "pdf":
        return PDF_INPUT_EXTENSIONS
    if mode == "image":
        return IMAGE_INPUT_EXTENSIONS
    return set()


def type_label(path: str) -> str:
    ext = normalize_extension(path)
    if ext in HWP_EXTENSIONS:
        return "한글"
    if ext in WORD_EXTENSIONS:
        return "Word"
    if ext in EXCEL_EXTENSIONS:
        return "Excel"
    if ext in POWERPOINT_EXTENSIONS:
        return "PowerPoint"
    if ext == ".pdf":
        return "PDF"
    return ext.upper().lstrip(".") or "파일"
