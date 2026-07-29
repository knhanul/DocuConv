import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#FFFFFF"
    border.color: "#D8E0EC"
    border.width: 1
    radius: 5

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.leftMargin: 12
            Layout.rightMargin: 8
            Label {
                text: "변환 작업 목록"
                color: "#17243A"
                font.pixelSize: 15
                font.bold: true
            }
            Item { Layout.fillWidth: true }
            Button {
                text: "모두 제거"
                enabled: !appController.busy
                onClicked: appController.clearJobs()
            }
            Button {
                text: "선택 제거"
                enabled: !appController.busy
                onClicked: appController.removeSelectedJobs()
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#E1E7F0" }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            color: "#F8FAFD"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 7
                Label { text: "순서"; Layout.preferredWidth: 50; horizontalAlignment: Text.AlignHCenter; color: "#52637B"; font.bold: true }
                Label { text: "파일 이름"; Layout.fillWidth: true; color: "#52637B"; font.bold: true }
                Label { text: "변환 대상"; Layout.preferredWidth: 88; color: "#52637B"; font.bold: true }
                Label { text: "상태"; Layout.preferredWidth: 90; color: "#52637B"; font.bold: true }
                Label { text: "진행률"; Layout.preferredWidth: 94; color: "#52637B"; font.bold: true }
            }
        }

        ListView {
            id: jobView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: appController.jobListModel
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                id: jobRow
                required property int index
                required property int sequence
                required property string fileName
                required property string outputPath
                required property string targetLabel
                required property string status
                required property int progress
                required property string message
                required property bool selected
                width: jobView.width
                height: 52
                color: jobRow.selected ? "#EEF5FF" : (jobMouse.containsMouse ? "#F7FAFE" : "#FFFFFF")
                border.color: "#E7EDF5"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 7
                    Label { text: jobRow.sequence; Layout.preferredWidth: 50; horizontalAlignment: Text.AlignHCenter; color: "#42536C" }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 2
                        Label { text: jobRow.fileName; Layout.fillWidth: true; elide: Text.ElideRight; color: "#1E2F46"; font.pixelSize: 12 }
                        Label { text: jobRow.message; Layout.fillWidth: true; elide: Text.ElideRight; color: "#8794A6"; font.pixelSize: 10 }
                    }
                    Label { text: jobRow.targetLabel; Layout.preferredWidth: 88; color: "#53657D"; font.bold: true }
                    Label {
                        text: jobRow.status
                        Layout.preferredWidth: 90
                        color: jobRow.status === "실패" ? "#E33636" : jobRow.status === "완료" ? "#16A060" : "#53657D"
                    }
                    ColumnLayout {
                        Layout.preferredWidth: 94
                        spacing: 2
                        ProgressBar { from: 0; to: 100; value: jobRow.progress; Layout.fillWidth: true }
                        Label { text: jobRow.progress + "%"; Layout.fillWidth: true; horizontalAlignment: Text.AlignRight; color: "#65758B"; font.pixelSize: 10 }
                    }
                }

                MouseArea {
                    id: jobMouse
                    anchors.fill: parent
                    hoverEnabled: true
                    enabled: !appController.busy
                    cursorShape: Qt.PointingHandCursor
                    onClicked: appController.toggleJobSelected(index)
                }
                ToolTip.visible: jobMouse.containsMouse && jobRow.outputPath.length > 0
                ToolTip.text: jobRow.outputPath
            }

            Label {
                anchors.centerIn: parent
                visible: jobView.count === 0
                text: "파일을 선택한 뒤 변환 시작을 누르면 작업이 표시됩니다."
                color: "#8290A4"
                font.pixelSize: 12
            }
        }
    }
}
