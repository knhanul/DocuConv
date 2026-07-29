import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Item {
    id: root

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 14
        spacing: 10

        RowLayout {
            Layout.fillWidth: true
            Label {
                text: "작업 이력"
                color: "#17243A"
                font.pixelSize: 18
                font.bold: true
            }
            Item { Layout.fillWidth: true }
            Button { text: "출력 폴더 열기"; onClicked: appController.openOutputFolder() }
            Button { text: "이력 지우기"; onClicked: appController.clearHistory() }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.fillHeight: true
            color: "#FFFFFF"
            radius: 6
            border.color: "#D8E0EC"

            ColumnLayout {
                anchors.fill: parent
                spacing: 0
                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 42
                    color: "#F7F9FC"
                    RowLayout {
                        anchors.fill: parent
                        anchors.leftMargin: 14
                        anchors.rightMargin: 14
                        spacing: 10
                        Label { text: "파일 이름"; Layout.fillWidth: true; color: "#53657D"; font.bold: true }
                        Label { text: "변환 대상"; Layout.preferredWidth: 100; color: "#53657D"; font.bold: true }
                        Label { text: "상태"; Layout.preferredWidth: 90; color: "#53657D"; font.bold: true }
                        Label { text: "완료 시각"; Layout.preferredWidth: 155; color: "#53657D"; font.bold: true }
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
                        color: historyMouse.containsMouse ? "#F4F8FE" : "#FFFFFF"
                        border.color: "#E9EEF5"
                        RowLayout {
                            anchors.fill: parent
                            anchors.leftMargin: 14
                            anchors.rightMargin: 14
                            spacing: 10
                            ColumnLayout {
                                Layout.fillWidth: true
                                spacing: 2
                                Label { text: historyRow.fileName; Layout.fillWidth: true; elide: Text.ElideRight; color: "#213148" }
                                Label { text: historyRow.outputPath; Layout.fillWidth: true; elide: Text.ElideMiddle; color: "#8794A5"; font.pixelSize: 10 }
                            }
                            Label { text: historyRow.targetLabel; Layout.preferredWidth: 100; color: "#52647D"; font.bold: true }
                            Label { text: historyRow.status; Layout.preferredWidth: 90; color: historyRow.status === "완료" ? "#169A5D" : "#DE4242" }
                            Label { text: historyRow.finishedAt; Layout.preferredWidth: 155; color: "#687991"; font.pixelSize: 11 }
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
                        color: "#8290A4"
                    }
                }
            }
        }
    }
}
