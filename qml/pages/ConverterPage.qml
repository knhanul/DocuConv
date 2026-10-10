import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "../components"

Item {
    id: root

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        Item {
            SplitView.preferredWidth: parent.width * 0.53
            SplitView.minimumWidth: 620

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 30
                    clip: true

                    Row {
                        id: breadcrumbRow
                        x: Math.min(0, parent.width - implicitWidth)
                        height: 30
                        spacing: 0
                        Repeater {
                            model: appController.currentBreadcrumbs
                            delegate: Row {
                                required property int index
                                required property var modelData
                                Label {
                                    height: 30
                                    width: 16
                                    visible: parent.index > 0
                                    text: "›"
                                    color: "#8A9099"
                                    font.pixelSize: 14
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Button {
                                    id: crumbButton
                                    objectName: "breadcrumbButton"
                                    property string crumbPath: parent.modelData.path
                                    height: 30
                                    leftPadding: 6
                                    rightPadding: 6
                                    text: parent.modelData.label
                                    font.pixelSize: 14
                                    font.bold: true
                                    flat: true
                                    Accessible.name: text
                                    ToolTip.visible: hovered
                                    ToolTip.text: crumbPath
                                    onClicked: appController.navigateToFolder(crumbPath)
                                }
                            }
                        }
                    }
                }

                SplitView {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    orientation: Qt.Horizontal

                    FolderTreePanel {
                        SplitView.preferredWidth: 290
                        SplitView.minimumWidth: 230
                    }
                    FileListPanel {
                        SplitView.fillWidth: true
                        SplitView.minimumWidth: 360
                    }
                }
            }
        }

        Item {
            SplitView.fillWidth: true
            SplitView.minimumWidth: 650

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 10
                spacing: 8

                SectionCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 294
                    title: "변환 설정"

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        RowLayout {
                            Layout.fillWidth: true
                            Layout.preferredHeight: 146
                            Layout.maximumHeight: 146
                            spacing: 9

                            TargetCard {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                title: "HWPX 변환"
                                subtitle: "HWP → HWPX"
                                iconText: "H"
                                accentColor: "#2F74E8"
                                selected: appController.conversionMode === "hwpx"
                                notice: "HWPX 변환은 한글 프로그램이 설치된 Windows 환경에서만 사용할 수 있습니다."
                                onClicked: appController.setConversionMode("hwpx")
                            }
                            TargetCard {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                title: "PDF 변환"
                                subtitle: "HWP/HWPX · Word · Excel · PowerPoint → PDF"
                                iconText: "PDF"
                                accentColor: "#EE4D4D"
                                selected: appController.conversionMode === "pdf"
                                chips: ["HWP", "HWPX", "DOCX", "XLSX", "PPTX"]
                                onClicked: appController.setConversionMode("pdf")
                            }
                            TargetCard {
                                Layout.fillWidth: true
                                Layout.fillHeight: true
                                title: "이미지 변환"
                                subtitle: "PDF 1개 → 페이지별 이미지"
                                iconText: "IMG"
                                accentColor: "#20A66A"
                                selected: appController.conversionMode === "image"
                                chips: ["PNG", "JPG", "TIFF"]
                                notice: "이미지 변환은 한 번에 문서 한 개만 선택할 수 있습니다."
                                onClicked: appController.setConversionMode("image")
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label { text: "출력 폴더"; color: "#26364D"; font.bold: true; Layout.preferredWidth: 74 }
                            TextField {
                                Layout.fillWidth: true
                                text: appController.outputFolder
                                readOnly: true
                                selectByMouse: true
                            }
                            Button { text: "찾아보기"; onClicked: appController.chooseOutputFolder() }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14
                            Label { text: "옵션"; color: "#26364D"; font.bold: true; Layout.preferredWidth: 74 }
                            RowLayout {
                                visible: appController.conversionMode === "pdf"
                                spacing: 8
                                Label { text: "변환 방식"; color: "#53657C" }
                                ComboBox {
                                    objectName: "pdfConversionMethodCombo"
                                    model: ["원본 프로그램으로 변환", "LibreOffice로 변환"]
                                    currentIndex: appController.pdfConversionMethod === "libreoffice" ? 1 : 0
                                    enabled: !appController.busy
                                    onActivated: appController.setPdfConversionMethod(currentIndex === 1 ? "libreoffice" : "original")
                                    ToolTip.visible: hovered
                                    ToolTip.text: "LibreOffice 방식은 별도 설치가 필요하며 문서 레이아웃이 달라질 수 있습니다. HWP/HWPX는 H2Orestart와 Java 설정도 필요합니다."
                                }
                            }
                            RowLayout {
                                visible: appController.conversionMode === "image"
                                spacing: 8
                                Label { text: "이미지 형식"; color: "#53657C" }
                                ComboBox {
                                    model: ["PNG", "JPG", "TIFF"]
                                    currentIndex: appController.imageFormat === "png" ? 0 : appController.imageFormat === "jpg" ? 1 : 2
                                    onActivated: appController.setImageFormat(currentText.toLowerCase())
                                }
                            }
                            CheckBox {
                                text: "동일 파일 덮어쓰기"
                                checked: appController.overwrite
                                onToggled: appController.setOverwrite(checked)
                            }
                            Button { text: "출력 폴더 열기"; onClicked: appController.openOutputFolder() }
                            Item { Layout.fillWidth: true }
                        }
                    }
                }

                JobQueuePanel {
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 92
                    color: "#FFFFFF"
                    radius: 5
                    border.color: "#D8E0EC"
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 12
                        spacing: 14

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 5
                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: "전체 진행률"; color: "#26364D"; font.bold: true }
                                Item { Layout.fillWidth: true }
                                Label { text: appController.overallProgress + "%"; color: "#3B4D65" }
                            }
                            ProgressBar {
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: appController.overallProgress
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label { text: "작업 상태: " + appController.statusText; color: "#65758B"; font.pixelSize: 11 }
                                Item { Layout.fillWidth: true }
                                Label { text: appController.jobCountSummary; color: "#65758B"; font.pixelSize: 11 }
                            }
                        }

                        Button {
                            id: startButton
                            visible: !appController.busy
                            Layout.preferredWidth: 160
                            Layout.fillHeight: true
                            text: "▷  변환 시작"
                            font.pixelSize: 15
                            font.bold: true
                            onClicked: appController.startConversion()
                            background: Rectangle { color: startButton.hovered ? "#2868D2" : "#2F74E8"; radius: 5 }
                            contentItem: Text { text: startButton.text; color: "white"; font: startButton.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                        Button {
                            id: cancelButton
                            visible: appController.busy
                            Layout.preferredWidth: 160
                            Layout.fillHeight: true
                            text: "■  작업 취소"
                            font.pixelSize: 15
                            font.bold: true
                            onClicked: appController.cancelConversion()
                            background: Rectangle { color: cancelButton.hovered ? "#C73B3B" : "#E34B4B"; radius: 5 }
                            contentItem: Text { text: cancelButton.text; color: "white"; font: cancelButton.font; horizontalAlignment: Text.AlignHCenter; verticalAlignment: Text.AlignVCenter }
                        }
                    }
                }
            }
        }
    }
}
