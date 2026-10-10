from __future__ import annotations

import threading
from pathlib import Path

from backend.settings import AppSettings
from converters.base import ConversionCancelled, ConversionError, ProgressCallback, require_input_file


class DocumentToImageConverter:
    def __init__(self, settings: AppSettings) -> None:
        self._settings = settings

    def convert(
        self,
        input_path: Path,
        output_directory: Path,
        image_format: str,
        progress: ProgressCallback,
        cancel_event: threading.Event,
    ) -> None:
        require_input_file(input_path)
        if input_path.suffix.lower() != ".pdf":
            raise ConversionError("이미지 변환은 PDF 파일만 지원합니다.")
        fmt = image_format.lower()
        if fmt not in {"png", "jpg", "tiff"}:
            raise ConversionError(f"지원하지 않는 이미지 형식입니다: {image_format}")

        output_directory.mkdir(parents=True, exist_ok=True)
        progress(10, "PDF 문서를 열 준비를 하고 있습니다.")

        try:
            import pypdfium2 as pdfium
        except ImportError as exc:
            raise ConversionError("pypdfium2가 설치되어 있지 않습니다.") from exc

        try:
            from PIL import Image
        except ImportError as exc:
            raise ConversionError("이미지 저장에 필요한 Pillow가 설치되어 있지 않습니다.") from exc

        document = pdfium.PdfDocument(str(input_path))
        try:
            page_count = len(document)
            if page_count < 1:
                raise ConversionError("이미지로 변환할 페이지가 없습니다.")
            scale = self._settings.image_dpi / 72.0

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

                value = 10 + round(((page_index + 1) / page_count) * 89)
                progress(value, f"{page_index + 1}/{page_count} 페이지를 이미지로 변환했습니다.")
        finally:
            document.close()
