import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    color: Theme.surface
    border.color: Theme.line
    border.width: 1
    radius: Theme.radius

    function statusColor(status) {
        if (status === "실패")
            return Theme.danger
        if (status === "완료")
            return Theme.success
        if (status === "취소됨" || status === "취소 요청")
            return Theme.inkSecondary
        if (status === "변환 중")
            return Theme.red
        return Theme.inkSecondary
    }

    function statusFill(status) {
        if (status === "실패")
            return Theme.dangerSoft
        if (status === "완료")
            return Theme.successSoft
        if (status === "변환 중")
            return Theme.accentSoft
        return Theme.surfaceMuted
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 48
            Layout.leftMargin: 14
            Layout.rightMargin: 10
            spacing: 8
            Rectangle {
                Layout.preferredWidth: 3
                Layout.preferredHeight: 14
                radius: 1
                color: Theme.red
            }
            Label {
                text: "변환 작업 목록"
                color: Theme.ink
                font.pixelSize: 15
                font.bold: true
                font.family: Theme.fontFamily
            }
            Item { Layout.fillWidth: true }
            AppButton {
                text: "모두 제거"
                enabled: !appController.busy
                onClicked: appController.clearJobs()
            }
            AppButton {
                text: "선택 제거"
                enabled: !appController.busy
                onClicked: appController.removeSelectedJobs()
            }
        }

        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.line }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 34
            color: Theme.surfaceMuted
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                spacing: 8
                Label { text: "순서"; Layout.preferredWidth: 46; horizontalAlignment: Text.AlignHCenter; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                Label { text: "파일 이름"; Layout.fillWidth: true; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                Label { text: "변환 대상"; Layout.preferredWidth: 88; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                Label { text: "상태"; Layout.preferredWidth: 86; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                Label { text: "진행률"; Layout.preferredWidth: 96; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
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
                color: jobRow.selected ? Theme.accentSoft : (jobMouse.containsMouse ? Theme.surfaceMuted : Theme.surface)

                Rectangle {
                    anchors.left: parent.left
                    anchors.right: parent.right
                    anchors.bottom: parent.bottom
                    height: 1
                    color: Theme.line
                }

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 12
                    anchors.rightMargin: 12
                    spacing: 8
                    Label {
                        text: jobRow.sequence
                        Layout.preferredWidth: 46
                        horizontalAlignment: Text.AlignHCenter
                        color: Theme.inkSecondary
                        font.family: Theme.fontFamily
                    }
                    ColumnLayout {
                        Layout.fillWidth: true
                        spacing: 1
                        Label {
                            text: jobRow.fileName
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: Theme.ink
                            font.pixelSize: 12
                            font.family: Theme.fontFamily
                        }
                        Label {
                            text: jobRow.message
                            Layout.fillWidth: true
                            elide: Text.ElideRight
                            color: Theme.muted
                            font.pixelSize: 10
                            font.family: Theme.fontFamily
                        }
                    }
                    Label {
                        text: jobRow.targetLabel
                        Layout.preferredWidth: 88
                        color: Theme.inkSecondary
                        font.bold: true
                        font.family: Theme.fontFamily
                    }
                    Rectangle {
                        Layout.preferredWidth: 86
                        Layout.preferredHeight: 24
                        radius: 12
                        color: root.statusFill(jobRow.status)
                        Label {
                            anchors.centerIn: parent
                            text: jobRow.status
                            color: root.statusColor(jobRow.status)
                            font.pixelSize: 11
                            font.bold: true
                            font.family: Theme.fontFamily
                        }
                    }
                    ColumnLayout {
                        Layout.preferredWidth: 96
                        spacing: 3
                        AppProgress {
                            from: 0
                            to: 100
                            value: jobRow.progress
                            Layout.fillWidth: true
                        }
                        Label {
                            text: jobRow.progress + "%"
                            Layout.fillWidth: true
                            horizontalAlignment: Text.AlignRight
                            color: Theme.muted
                            font.pixelSize: 10
                            font.family: Theme.fontFamily
                        }
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
                color: Theme.muted
                font.pixelSize: 12
                font.family: Theme.fontFamily
            }
        }
    }
}
