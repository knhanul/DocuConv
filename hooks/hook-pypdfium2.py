from PyInstaller.utils.hooks import collect_all

# pypdfium2는 ctypes로 PDFium 네이티브 라이브러리를 로드하므로
# Python 모듈뿐 아니라 pypdfium2_raw의 DLL/데이터도 함께 수집합니다.
datas, binaries, hiddenimports = collect_all("pypdfium2")
raw_datas, raw_binaries, raw_hiddenimports = collect_all("pypdfium2_raw")
datas += raw_datas
binaries += raw_binaries
hiddenimports += raw_hiddenimports
