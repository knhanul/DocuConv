from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class AppSettings:
    hwp_security_module_type: str = "FilePathCheckDLL"
    hwp_security_module_name: str = ""
    hwp_visible: bool = False
    office_visible: bool = False
    image_dpi: int = 150
    jpeg_quality: int = 92
    max_history_items: int = 500
    libreoffice_path: str = ""
    libreoffice_hwp_profile: str = ""
    prefer_libreoffice_pdf: bool = False

    @classmethod
    def load(cls, path: Path) -> AppSettings:
        if not path.exists():
            return cls()
        try:
            raw: dict[str, Any] = json.loads(path.read_text(encoding="utf-8-sig"))
        except (OSError, json.JSONDecodeError):
            return cls()
        return cls(
            hwp_security_module_type=str(raw.get("hwpSecurityModuleType", "FilePathCheckDLL")),
            hwp_security_module_name=str(raw.get("hwpSecurityModuleName", "")),
            hwp_visible=bool(raw.get("hwpVisible", False)),
            office_visible=bool(raw.get("officeVisible", False)),
            image_dpi=max(72, min(600, int(raw.get("imageDpi", 150)))),
            jpeg_quality=max(50, min(100, int(raw.get("jpegQuality", 92)))),
            max_history_items=max(50, int(raw.get("maxHistoryItems", 500))),
            libreoffice_path=str(raw.get("libreOfficePath", "")),
            libreoffice_hwp_profile=str(raw.get("libreOfficeHwpProfile", "")),
        )
