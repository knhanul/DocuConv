# 아키텍처

```text
QML UI
  └─ AppController (QObject)
      ├─ FolderTreeModel
      ├─ FileListModel
      ├─ JobListModel
      ├─ HistoryModel
      ├─ SelectionManager
      └─ ConversionWorker (QThread)
          └─ ConverterRegistry
              ├─ HWP → HWPX
              ├─ HWP/HWPX → PDF
              ├─ Word → PDF
              ├─ Excel → PDF
              ├─ PowerPoint → PDF
              └─ PDF → 페이지 이미지
```

## 스레드 원칙

- UI 스레드는 파일 목록과 작업 상태 표시만 처리합니다.
- 변환 큐는 `ConversionWorker(QThread)`에서 순차 처리합니다.
- Worker 진입 시 `pythoncom.CoInitialize()`를 호출하고 종료 시 `CoUninitialize()`를 호출합니다.
- COM 객체는 Worker 내부에서 생성하며 UI 스레드와 공유하지 않습니다.

## 이미지 변환

1. 선택 문서가 PDF가 아니면 문서 종류에 맞는 PDF 변환기를 실행합니다.
2. 임시 PDF를 pypdfium2/PDFium로 열어 페이지를 렌더링합니다.
3. `출력폴더/문서명/page_001.png` 형식으로 저장합니다.
4. 임시 PDF와 임시 폴더를 정리합니다.
