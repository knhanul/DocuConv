import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../components"
import "../theme"

Item {
    id: root

    function statusColor(status) {
        return status === "완료" ? Theme.success : Theme.danger
    }
    function statusFill(status) {
        return status === "완료" ? Theme.successSoft : Theme.dangerSoft
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 16
        spacing: 12

        RowLayout {
            Layout.fillWidth: true
            spacing: 8
            Rectangle {
                Layout.preferredWidth: 3
                Layout.preferredHeight: 16
                radius: 1
                color: Theme.red
            }
            Label {
                text: "작업 이력"
                color: Theme.ink
                font.pixelSize: 18
                font.bold: true
                font.family: Theme.fontFamily
            }
            Item { Layout.fillWidth: true }
            AppButton { text: "출력 폴더 열기"; onClicked: appController.openOutputFolder() }
            AppButton { text: "이력 지우기"; variant: "danger"; onClicked: appController.clearHistory() }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: Theme.surface
            radius: Theme.radius
            border.color: Theme.line
            border.width: 1

            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 40
                    color: Theme.surfaceMuted
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 16
                        anchors.rightMargin: 16
                        spacing: 10
                        Label { text: "파일 이름"; Layout.fillWidth: true; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                        Label { text: "변환 대상"; Layout.preferredWidth: 100; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                        Label { text: "상태"; Layout.preferredWidth: 78; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                        Label { text: "완료 시각"; Layout.preferredWidth: 155; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                    }
                }

                ListView {
                    id: historyView
                    Layout.fillWidth: true
                    Layout.fillHeight: true
                    clip: true
                    model: appController.historyModel
                    ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

                    delegate: Rectangle {
                        id: historyRow
                        required property int index
                        required property string fileName
                        required property string outputPath
                        required property string targetLabel
                        required property string status
                        required property string finishedAt
                        required property string message
                        width: historyView.width
                        height: 58
                        color: historyMouse.containsMouse ? Theme.accentSoft : Theme.surface

                        Rectangle {
                            anchors.left: parent.left
                            anchors.right: parent.right
                            anchors.bottom: parent.bottom
                            height: 1
                            color: Theme.line
                        }

                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 16
                            anchors.rightMargin: 16
                            spacing: 10
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label {
                                    text: historyRow.fileName
                                    Layout.fillWidth: true
                                    elide: Text.ElideRight
                                    color: Theme.ink
                                    font.family: Theme.fontFamily
                                }
                                Label {
                                    text: historyRow.outputPath
                                    Layout.fillWidth: true
                                    elide: Text.ElideMiddle
                                    color: Theme.muted
                                    font.pixelSize: 11
                                    font.family: Theme.fontFamily
                                }
                            }
                            Label {
                                text: historyRow.targetLabel
                                Layout.preferredWidth: 100
                                color: Theme.inkSecondary
                                font.bold: true
                                font.family: Theme.fontFamily
                            }
                            Rectangle {
                                Layout.preferredWidth: 78
                                Layout.preferredHeight: 24
                                radius: 12
                                color: root.statusFill(historyRow.status)
                                Label {
                                    anchors.centerIn: parent
                                    text: historyRow.status
                                    color: root.statusColor(historyRow.status)
                                    font.pixelSize: 11
                                    font.bold: true
                                    font.family: Theme.fontFamily
                                }
                            }
                            Label {
                                text: historyRow.finishedAt
                                Layout.preferredWidth: 155
                                color: Theme.inkSecondary
                                font.pixelSize: 12
                                font.family: Theme.fontFamily
                            }
                        }
                        MouseArea {
                            id: historyMouse
                            anchors.fill: parent
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            onDoubleClicked: appController.openPath(historyRow.outputPath)
                        }
                        ToolTip.visible: historyMouse.containsMouse
                        ToolTip.text: "더블클릭하여 결과 폴더 열기\n" + historyRow.message
                    }

                    Label {
                        anchors.centerIn: parent
                        visible: historyView.count === 0
                        text: "아직 저장된 변환 이력이 없습니다."
                        color: Theme.muted
                        font.family: Theme.fontFamily
                    }
                }
            }
        }
    }
}
