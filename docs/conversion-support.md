# 변환 지원 범위와 제약

## HWP/HWPX

- COM ProgID: `HWPFrame.HwpObject`
- HWPX 저장 형식: `HWPX`
- PDF 저장 형식: `PDF`
- 한글 버전과 사내 보안 정책에 따라 `RegisterModule` 설정이 필요할 수 있습니다.

## Microsoft Office

- Word: `Word.Application` + `Document.ExportAsFixedFormat(..., 17)`
- Excel: `Excel.Application` + `Workbook.ExportAsFixedFormat(0, ...)`
- PowerPoint: `PowerPoint.Application` + `Presentation.SaveAs(..., 32)`

각 Office 프로그램이 실제로 설치되어 있어야 합니다. Microsoft 365 웹 버전만으로는 COM 자동화를 실행할 수 없습니다.

## 진행률

Office와 한글 COM 저장은 페이지 단위 진행률을 일반적으로 제공하지 않으므로 열기·저장·완료 단계의 추정 진행률을 표시합니다. 이미지 렌더링은 전체 페이지 수를 알 수 있어 페이지별 실제 진행률을 표시합니다.
