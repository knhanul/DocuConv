import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root

    SplitView {
        anchors.fill: parent
        orientation: Qt.Horizontal

        Item {
            SplitView.preferredWidth: Math.round(parent.width * 0.48)
            SplitView.minimumWidth: 560

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 8

                Item {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 32
                    clip: true

                    Row {
                        id: breadcrumbRow
                        x: Math.min(0, parent.width - implicitWidth)
                        height: 32
                        spacing: 0
                        Repeater {
                            model: appController.currentBreadcrumbs
                            delegate: Row {
                                required property int index
                                required property var modelData
                                Label {
                                    height: 32
                                    width: 14
                                    visible: parent.index > 0
                                    text: "/"
                                    color: Theme.muted
                                    font.pixelSize: 12
                                    font.family: Theme.fontFamily
                                    verticalAlignment: Text.AlignVCenter
                                    horizontalAlignment: Text.AlignHCenter
                                }
                                Basic.Button {
                                    id: crumbButton
                                    objectName: "breadcrumbButton"
                                    property string crumbPath: parent.modelData.path
                                    property string crumbLabel: parent.modelData.label
                                    height: 32
                                    leftPadding: 6
                                    rightPadding: 6
                                    font.pixelSize: 13
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                    flat: true
                                    Accessible.name: crumbLabel
                                    ToolTip.visible: hovered
                                    ToolTip.text: crumbPath
                                    onClicked: appController.navigateToFolder(crumbPath)

                                    background: Rectangle {
                                        color: crumbButton.hovered ? Theme.accentSoft : "transparent"
                                        radius: 4
                                    }
                                    contentItem: Text {
                                        text: crumbButton.crumbLabel
                                        color: crumbButton.hovered ? Theme.red : Theme.ink
                                        font: crumbButton.font
                                        horizontalAlignment: Text.AlignHCenter
                                        verticalAlignment: Text.AlignVCenter
                                    }
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
            SplitView.minimumWidth: 560
            clip: true

            ColumnLayout {
                anchors.fill: parent
                anchors.margins: 12
                spacing: 10

                SectionCard {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 148
                    title: "PDF 생성"

                    ColumnLayout {
                        anchors.fill: parent
                        spacing: 10

                        Label {
                            Layout.fillWidth: true
                            text: "HWP/HWPX · Word · Excel · PowerPoint 문서를 PDF로 변환합니다."
                            color: Theme.inkSecondary
                            font.pixelSize: 12
                            font.family: Theme.fontFamily
                            wrapMode: Text.WordWrap
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 8
                            Label {
                                text: "출력 폴더"
                                color: Theme.ink
                                font.bold: true
                                font.family: Theme.fontFamily
                                Layout.preferredWidth: 74
                            }
                            Basic.TextField {
                                Layout.fillWidth: true
                                implicitWidth: 80
                                text: appController.outputFolder
                                readOnly: true
                                selectByMouse: true
                                color: Theme.ink
                                font.pixelSize: 13
                                font.family: Theme.fontFamily
                                leftPadding: 10
                                rightPadding: 10
                                implicitHeight: 34
                                background: Rectangle {
                                    radius: Theme.radiusSm
                                    color: Theme.surfaceMuted
                                    border.color: Theme.lineStrong
                                    border.width: 1
                                }
                            }
                            AppButton {
                                text: "찾아보기"
                                onClicked: appController.chooseOutputFolder()
                            }
                        }

                        RowLayout {
                            Layout.fillWidth: true
                            spacing: 14
                            Label {
                                text: "옵션"
                                color: Theme.ink
                                font.bold: true
                                font.family: Theme.fontFamily
                                Layout.preferredWidth: 74
                            }
                            RowLayout {
                                spacing: 8
                                Label { text: "변환 방식"; color: Theme.inkSecondary; font.family: Theme.fontFamily }
                                ComboBox {
                                    id: pdfMethodCombo
                                    objectName: "pdfConversionMethodCombo"
                                    Layout.fillWidth: true
                                    Layout.minimumWidth: 120
                                    implicitWidth: 160
                                    model: ["원본 프로그램으로 변환", "LibreOffice로 변환"]
                                    currentIndex: appController.pdfConversionMethod === "libreoffice" ? 1 : 0
                                    enabled: !appController.busy
                                    onActivated: appController.setPdfConversionMethod(currentIndex === 1 ? "libreoffice" : "original")
                                    ToolTip.visible: hovered
                                    ToolTip.text: "LibreOffice 방식은 별도 설치가 필요하며 문서 레이아웃이 달라질 수 있습니다. HWP/HWPX는 H2Orestart와 Java 설정도 필요합니다."
                                    font.family: Theme.fontFamily
                                    contentItem: Text {
                                        text: pdfMethodCombo.displayText
                                        font: pdfMethodCombo.font
                                        color: pdfMethodCombo.enabled ? Theme.ink : Theme.muted
                                        leftPadding: 10
                                        rightPadding: pdfMethodCombo.indicator ? pdfMethodCombo.indicator.width + 6 : 24
                                        verticalAlignment: Text.AlignVCenter
                                        elide: Text.ElideRight
                                    }
                                }
                            }
                            CheckBox {
                                text: "동일 파일 덮어쓰기"
                                checked: appController.overwrite
                                font.family: Theme.fontFamily
                                onToggled: appController.setOverwrite(checked)
                            }
                            AppButton { text: "출력 폴더 열기"; onClicked: appController.openOutputFolder() }
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
                    Layout.preferredHeight: 88
                    color: Theme.surface
                    radius: Theme.radius
                    border.color: Theme.line
                    border.width: 1

                    RowLayout {
                        anchors.fill: parent
                        anchors.margins: 14
                        spacing: 16

                        ColumnLayout {
                            Layout.fillWidth: true
                            spacing: 6
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: "전체 진행률"
                                    color: Theme.ink
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: appController.overallProgress + "%"
                                    color: Theme.red
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                }
                            }
                            AppProgress {
                                Layout.fillWidth: true
                                from: 0
                                to: 100
                                value: appController.overallProgress
                            }
                            RowLayout {
                                Layout.fillWidth: true
                                Label {
                                    text: appController.statusText
                                    color: Theme.inkSecondary
                                    font.pixelSize: 12
                                    font.family: Theme.fontFamily
                                }
                                Item { Layout.fillWidth: true }
                                Label {
                                    text: appController.jobCountSummary
                                    color: Theme.muted
                                    font.pixelSize: 11
                                    font.family: Theme.fontFamily
                                }
                            }
                        }

                        AppButton {
                            id: startButton
                            visible: !appController.busy
                            variant: "primary"
                            Layout.preferredWidth: 156
                            Layout.fillHeight: true
                            text: "PDF 생성 시작"
                            font.pixelSize: 15
                            onClicked: appController.startConversion()
                        }
                        AppButton {
                            id: cancelButton
                            visible: appController.busy
                            variant: "dangerSolid"
                            Layout.preferredWidth: 156
                            Layout.fillHeight: true
                            text: "작업 취소"
                            font.pixelSize: 15
                            onClicked: appController.cancelConversion()
                        }
                    }
                }
            }
        }
    }
}
