# 빌드 가이드 — POSID_DocConv

## 준비 사항

- Windows 10/11 x64
- Python 3.10~3.14 (3.12 권장)
- 프로젝트 가상환경 `.venv`

가상환경이 없다면:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

빌드 도구 설치:

```powershell
.\.venv\Scripts\python.exe -m pip install "PyInstaller==6.16.0" "pytest==8.4.2"
```

## 빌드 방법

### 방법 1: 빌드 스크립트 (권장)

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\build.ps1
```

버전과 빌드 날짜를 영어로 입력받습니다. 날짜를 비워 두면 오늘 날짜가 자동 입력됩니다.

```
Enter version (e.g. 1.0.0): 1.0.1
Enter build date (e.g. 2026-10-12, Enter for today):
```

인자로 바로 지정할 수도 있습니다.

```powershell
.\scripts\build.ps1 -Version "1.0.1" -BuildDate "2026-10-12"
```

스크립트 수행 순서:

1. `backend/version.py`에 `APP_VERSION`, `BUILD_DATE` 기록
2. 전체 테스트(`pytest`) 실행 — 실패 시 빌드 중단
3. `posid_document_converter_onefile.spec`으로 PyInstaller 빌드

### 방법 2: 스펙 파일로 직접 빌드

버전 기록과 테스트 없이 스펙만으로 빌드합니다.

```powershell
# 단일 EXE
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean posid_document_converter_onefile.spec

# 폴더형 배포
.\.venv\Scripts\python.exe -m PyInstaller --noconfirm --clean posid_document_converter.spec
```

> 이 방법은 `backend/version.py`를 갱신하지 않으므로, 앱에 표시되는 버전/빌드 날짜는 마지막으로 기록된 값이 그대로 사용됩니다. 배포 빌드에는 방법 1을 사용하세요.

## 결과물

| 스펙 파일 | 결과 | 용도 |
|---|---|---|
| `posid_document_converter_onefile.spec` | `dist\POSID_DocConv.exe` | 단일 실행 파일 배포 |
| `posid_document_converter.spec` | `dist\POSID_DocConv\` 폴더 | 폴더형 배포 (시작 속도 빠름) |

스펙 파일에는 QML, `assets`, `appsettings.json`이 포함되어 있어 별도 리소스 파일 없이 동작합니다. 단일 EXE는 EXE 옆의 `appsettings.json`이 있으면 내장 설정 대신 그 파일을 사용합니다.

### 배포 ZIP 생성 (폴더형)

```powershell
.\scripts\create-portable-zip.ps1
```

결과: `artifacts\POSID_DocumentConverter_v<버전>_win-x64.zip`

## 실행 환경 요구사항

- 배포 PC에 Python은 필요 없습니다.
- 문서 변환에는 원본 프로그램이 필요합니다 — HWP/HWPX는 한컴오피스 한글, Office 문서는 해당 Microsoft Office 데스크톱 앱이 설치되어 있어야 합니다. 미설치 시 프로그램명과 설치 필요 안내가 표시됩니다.

## 문제 해결

- **스크립트 실행 정책 오류**: `Set-ExecutionPolicy -Scope Process Bypass` 후 다시 실행
- **`.venv not found` 오류**: 준비 사항의 가상환경 생성을 먼저 수행
- **테스트 실패로 빌드 중단**: `.\.venv\Scripts\python.exe -m pytest`로 실패 원인을 먼저 해결하거나, 방법 2로 스펙만 빌드
- **UPX 관련 경고/오류**: UPX 미설치 시 PyInstaller가 자동으로 건너뜁니다. 안티바이러스 오진이 있다면 스펙 파일에서 `upx=False`로 변경
