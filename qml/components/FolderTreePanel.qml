pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts

Rectangle {
    id: root
    property var controller: appController
    color: "#FFFFFF"
    border.color: "#D8E0EC"
    border.width: 1
    radius: 4

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 1
        spacing: 0

        RowLayout {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            Layout.leftMargin: 12
            Layout.rightMargin: 8
            spacing: 4
            Label {
                Layout.fillWidth: true
                text: "파일 탐색"
                color: "#26364D"
                font.pixelSize: 13
                font.bold: true
            }
            ToolButton {
                objectName: "refreshFoldersButton"
                Layout.preferredWidth: 28
                text: "↻"
                font.pixelSize: 18
                Accessible.name: "현재 폴더 새로고침"
                ToolTip.visible: hovered
                ToolTip.text: "현재 폴더 새로고침"
                onClicked: root.controller.refreshCurrentFolder()
            }
            ToolButton {
                objectName: "addFolderButton"
                text: "+ 폴더"
                font.pixelSize: 12
                ToolTip.visible: hovered
                ToolTip.text: "빠른 액세스에 폴더 고정"
                onClicked: root.controller.chooseSourceFolder()
            }
        }

        ListView {
            id: treeView
            objectName: "folderTreeView"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.controller.folderTreeModel
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                id: rowItem
                required property int index
                required property int depth
                required property string kind
                required property bool hasChildren
                required property bool expanded
                required property string folderPath
                required property string folderName
                required property bool activeFolder
                required property string icon
                required property bool isQuick
                required property bool canUnpin
                objectName: kind === "section" ? "folderSectionRow" : "folderTreeRow"
                x: 6
                width: treeView.width - 12
                height: kind === "section" ? 30 : 32
                radius: 5
                color: kind === "section" ? "transparent"
                       : activeFolder ? "#E9E9E9"
                       : rowHover.hovered ? "#F3F3F3" : "transparent"
                HoverHandler { id: rowHover }
                MouseArea {
                    objectName: "folderNavigationArea"
                    anchors.fill: parent
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (rowItem.kind === "section")
                            root.controller.toggleFolderExpanded(rowItem.index)
                        else
                            root.controller.activateFolder(rowItem.index)
                    }
                }
                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 8 + rowItem.depth * 16
                    anchors.rightMargin: 6
                    spacing: 6
                    Item {
                        Layout.preferredWidth: 20
                        Layout.preferredHeight: rowItem.height
                        Basic.ToolButton {
                            objectName: "folderChevron"
                            anchors.fill: parent
                            visible: rowItem.hasChildren
                            enabled: rowItem.hasChildren
                            padding: 0
                            Accessible.name: rowItem.expanded ? "접기" : "펼치기"
                            background: Item {}
                            contentItem: Text {
                                text: "›"
                                rotation: rowItem.expanded ? 90 : 0
                                color: "#73777F"
                                font.pixelSize: 20
                                horizontalAlignment: Text.AlignHCenter
                                verticalAlignment: Text.AlignVCenter
                            }
                            onClicked: root.controller.toggleFolderExpanded(rowItem.index)
                        }
                    }
                    Image {
                        objectName: "folderSystemIcon"
                        Layout.preferredWidth: 20
                        Layout.preferredHeight: 20
                        visible: rowItem.kind !== "section"
                        source: visible ? "image://filesystem/" + rowItem.icon : ""
                        sourceSize: Qt.size(32, 32)
                        fillMode: Image.PreserveAspectFit
                    }
                    Label {
                        Layout.fillWidth: true
                        text: rowItem.folderName
                        color: rowItem.kind === "section" ? "#60656D" : "#30343B"
                        font.pixelSize: 12
                        font.bold: rowItem.kind === "section"
                        elide: Text.ElideRight
                    }
                    Item {
                        Layout.preferredWidth: 24
                        Layout.preferredHeight: 28
                        visible: rowItem.kind !== "section"
                        Basic.ToolButton {
                            anchors.fill: parent
                            visible: rowItem.canUnpin && rowHover.hovered
                            text: "×"
                            Accessible.name: "빠른 액세스에서 고정 해제"
                            ToolTip.visible: hovered
                            ToolTip.text: "빠른 액세스에서 고정 해제"
                            onClicked: root.controller.unpinFolder(rowItem.folderPath)
                            background: Item {}
                        }
                        Basic.ToolButton {
                            anchors.fill: parent
                            visible: !rowItem.isQuick && !rowItem.canUnpin && rowHover.hovered
                            text: "+"
                            Accessible.name: "빠른 액세스에 폴더 고정"
                            ToolTip.visible: hovered
                            ToolTip.text: "빠른 액세스에 폴더 고정"
                            onClicked: root.controller.pinFolder(rowItem.folderPath)
                            background: Item {}
                        }
                    }
                }
            }
        }
    }
}
