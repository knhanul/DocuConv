from __future__ import annotations

import shutil
import tempfile
import threading
from collections.abc import Callable
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, ProgressCallback, require_input_file

PdfConverter = Callable[[Path, Path, ProgressCallback, threading.Event], None]


class DocumentToImageConverter:
    def __init__(self, settings: AppSettings, pdf_converter: PdfConverter) -> None:
        self._settings = settings
        self._pdf_converter = pdf_converter

    def convert(
        self,
        input_path: Path,
        output_directory: Path,
        image_format: str,
        progress: ProgressCallback,
        cancel_event: threading.Event,
    ) -> None:
        require_input_file(input_path)
        fmt = image_format.lower()
        if fmt not in {"png", "jpg", "tiff"}:
            raise ConversionError(f"지원하지 않는 이미지 형식입니다: {image_format}")

        output_directory.mkdir(parents=True, exist_ok=True)
        temp_dir: Path | None = None
        pdf_path = input_path
        try:
            if input_path.suffix.lower() != ".pdf":
                temp_dir = Path(tempfile.mkdtemp(prefix="posid_doc_convert_"))
                pdf_path = temp_dir / f"{input_path.stem}.pdf"

                def pdf_progress(value: int, message: str) -> None:
                    # 문서→PDF 단계는 전체 이미지 변환의 60%로 환산합니다.
                    progress(max(1, round(value * 0.6)), message)

                self._pdf_converter(input_path, pdf_path, pdf_progress, cancel_event)
            else:
                progress(10, "PDF 문서를 열 준비를 하고 있습니다.")

            if cancel_event.is_set():
                raise ConversionCancelled("변환이 취소되었습니다.")

            try:
                import pypdfium2 as pdfium
            except ImportError as exc:
                raise ConversionError("pypdfium2가 설치되어 있지 않습니다.") from exc

            try:
                from PIL import Image
            except ImportError as exc:
                raise ConversionError("이미지 저장에 필요한 Pillow가 설치되어 있지 않습니다.") from exc

            document = pdfium.PdfDocument(str(pdf_path))
            try:
                page_count = len(document)
                if page_count < 1:
                    raise ConversionError("이미지로 변환할 페이지가 없습니다.")
                scale = self._settings.image_dpi / 72.0
                start = 60 if input_path.suffix.lower() != ".pdf" else 10
                span = 39 if input_path.suffix.lower() != ".pdf" else 89

                for page_index in range(page_count):
                    if cancel_event.is_set():
                        raise ConversionCancelled("변환이 취소되었습니다.")

                    page = document[page_index]
                    bitmap = None
                    try:
                        bitmap = page.render(scale=scale, rev_byteorder=True)
                        image: Image.Image = bitmap.to_pil().copy()
                    finally:
                        if bitmap is not None:
                            bitmap.close()
                        page.close()

                    extension = "jpg" if fmt == "jpg" else fmt
                    output_file = output_directory / f"page_{page_index + 1:03d}.{extension}"
                    if fmt == "png":
                        image.save(output_file, format="PNG", optimize=True)
                    elif fmt == "jpg":
                        if image.mode != "RGB":
                            image = image.convert("RGB")
                        image.save(
                            output_file,
                            format="JPEG",
                            quality=self._settings.jpeg_quality,
                            optimize=True,
                        )
                    else:
                        image.save(output_file, format="TIFF", compression="tiff_lzw")
                    image.close()

                    value = start + round(((page_index + 1) / page_count) * span)
                    progress(value, f"{page_index + 1}/{page_count} 페이지를 이미지로 변환했습니다.")
            finally:
                document.close()
        finally:
            if temp_dir is not None:
                shutil.rmtree(temp_dir, ignore_errors=True)
