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

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            Layout.leftMargin: 10
            Layout.rightMargin: 8
            spacing: 4
            ToolButton {
                text: "↻"
                font.pixelSize: 18
                ToolTip.visible: hovered
                ToolTip.text: "현재 폴더 새로고침"
                onClicked: appController.refreshCurrentFolder()
            }
            ToolButton {
                text: "+ 폴더"
                font.pixelSize: 12
                ToolTip.visible: hovered
                ToolTip.text: "다른 폴더 열기"
                onClicked: appController.chooseSourceFolder()
            }
            Item { Layout.fillWidth: true }
        }

        Rectangle { Layout.fillWidth: true; height: 1; color: "#E1E7F0" }

        ListView {
            id: treeView
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: appController.folderTreeModel
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                id: rowItem
                required property int index
                required property int depth
                required property bool hasChildren
                required property bool expanded
                required property bool checked
                required property string folderName
                required property bool isVirtual
                width: treeView.width
                height: 36
                color: rowMouse.containsMouse ? "#F1F6FD" : "transparent"

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 7 + rowItem.depth * 18
                    anchors.rightMargin: 6
                    spacing: 4

                    Item {
                        Layout.preferredWidth: 22
                        Layout.preferredHeight: 28
                        ToolButton {
                            anchors.fill: parent
                            visible: rowItem.hasChildren
                            enabled: rowItem.hasChildren
                            text: rowItem.expanded ? "⌄" : "›"
                            font.pixelSize: 17
                            onClicked: appController.toggleFolderExpanded(index)
                        }
                    }
                    CheckBox {
                        id: folderCheck
                        visible: !rowItem.isVirtual
                        checked: rowItem.checked
                        onClicked: appController.toggleFolderSelected(index)
                    }
                    Text { text: "▰"; color: "#E9B949"; font.pixelSize: 16; visible: !rowItem.isVirtual }
                    Label {
                        Layout.fillWidth: true
                        text: rowItem.folderName
                        color: "#26364D"
                        font.pixelSize: 13
                        font.bold: rowItem.isVirtual
                        elide: Text.ElideRight
                    }
                }

                MouseArea {
                    id: rowMouse
                    anchors.fill: parent
                    anchors.leftMargin: 70 + rowItem.depth * 18
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onDoubleClicked: appController.toggleFolderExpanded(index)
                    onClicked: {
                        if (rowItem.isVirtual)
                            appController.toggleFolderExpanded(index)
                        else
                            appController.activateFolder(index)
                    }
                }
            }
        }
    }
}
