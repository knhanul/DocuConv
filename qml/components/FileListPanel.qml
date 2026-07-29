import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    color: "#FFFFFF"
    border.color: "#D8E0EC"
    border.width: 1
    radius: 4

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            color: "#FFFFFF"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                spacing: 8
                Label {
                    Layout.fillWidth: true
                    text: appController.currentFolder
                    color: "#34455D"
                    font.pixelSize: 12
                    elide: Text.ElideMiddle
                }
                ToolButton {
                    text: "모두 선택"
                    font.pixelSize: 11
                    onClicked: appController.selectAllVisibleFiles(true)
                }
                ToolButton {
                    text: "선택 해제"
                    font.pixelSize: 11
                    onClicked: appController.selectAllVisibleFiles(false)
                }
            }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#E1E7F0" }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: "#F8FAFD"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 10
                anchors.rightMargin: 10
                spacing: 8
                Item { Layout.preferredWidth: 28 }
                Label { text: "이름"; color: "#53657E"; font.bold: true; Layout.fillWidth: true }
                Label { text: "형식"; color: "#53657E"; font.bold: true; Layout.preferredWidth: 86 }
                Label { text: "크기"; color: "#53657E"; font.bold: true; Layout.preferredWidth: 76 }
                Label { text: "수정한 날짜"; color: "#53657E"; font.bold: true; Layout.preferredWidth: 130 }
            }
        }

        ListView {
            id: fileView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: appController.fileListModel
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                id: fileRow
                required property int index
                required property bool checked
                required property string fileName
                required property string typeLabel
                required property string sizeText
                required property string modifiedText
                required property string extension
                width: fileView.width
                height: 43
                color: fileMouse.containsMouse ? "#F2F7FE" : "#FFFFFF"
                border.color: "#EDF1F6"
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 8
                    CheckBox {
                        Layout.preferredWidth: 28
                        checked: fileRow.checked
                        onClicked: appController.toggleFileSelected(index)
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        spacing: 8
                        Rectangle {
                            width: 26
                            height: 28
                            radius: 3
                            color: fileRow.typeLabel === "한글" ? "#EAF2FF" :
                                   fileRow.typeLabel === "Word" ? "#E9F1FF" :
                                   fileRow.typeLabel === "Excel" ? "#E9F8EF" :
                                   fileRow.typeLabel === "PowerPoint" ? "#FFF0E9" : "#FCEBEC"
                            Text {
                                anchors.centerIn: parent
                                text: fileRow.extension.length > 2 ? fileRow.extension.substring(0, 2) : fileRow.extension
                                color: "#32547B"
                                font.pixelSize: 9
                                font.bold: true
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            text: fileRow.fileName
                            color: "#1E2F46"
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                    }
                    Label { text: fileRow.typeLabel; color: "#687A93"; Layout.preferredWidth: 86; font.pixelSize: 11 }
                    Label { text: fileRow.sizeText; color: "#687A93"; Layout.preferredWidth: 76; font.pixelSize: 11 }
                    Label { text: fileRow.modifiedText; color: "#687A93"; Layout.preferredWidth: 130; font.pixelSize: 11 }
                }
                MouseArea {
                    id: fileMouse
                    anchors.fill: parent
                    anchors.leftMargin: 44
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: appController.toggleFileSelected(index)
                }
            }

            Label {
                anchors.centerIn: parent
                visible: fileView.count === 0
                text: "이 폴더에 지원되는 문서 파일이 없습니다."
                color: "#8290A4"
                font.pixelSize: 13
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: "#F8FAFD"
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                Label { text: appController.currentFolderSummary; color: "#5E6F87"; font.pixelSize: 11 }
                Item { Layout.fillWidth: true }
                Label { text: appController.selectionSummary; color: "#2F74E8"; font.pixelSize: 11; font.bold: true }
            }
        }
    }
}
