pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls
import QtQuick.Controls.Basic as Basic
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    property var controller: appController
    property var columnOrder: root.controller.fileListColumnOrder
    property var columnWidths: root.controller.fileListColumnWidths
    readonly property int columnWidthsSum: columnWidths["name"] + columnWidths["type"] + columnWidths["size"] + columnWidths["modified"]
    readonly property int minListWidth: 80 + columnWidthsSum
    readonly property var columnInfo: ({
        "type":     { "title": "유형" },
        "size":     { "title": "크기" },
        "modified": { "title": "수정한 날짜" }
    })
    color: Theme.surface
    border.color: Theme.line
    border.width: 1
    radius: Theme.radius

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 46
            color: Theme.surface
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 10
                spacing: 8
                Item { Layout.fillWidth: true }
                ToolButton {
                    objectName: "selectAllFilesButton"
                    text: "모두 선택"
                    font.pixelSize: 11
                    onClicked: root.controller.selectAllVisibleFiles(true)
                }
                ToolButton {
                    text: "선택 해제"
                    font.pixelSize: 11
                    onClicked: root.controller.selectAllVisibleFiles(false)
                }
            }
        }

        Rectangle { Layout.fillWidth: true; Layout.preferredHeight: 1; color: Theme.line }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: Theme.surfaceMuted
            clip: true
            RowLayout {
                x: 10 - fileView.contentX
                width: Math.max(parent.width - 20, root.minListWidth - 20)
                height: parent.height
                spacing: 8
                Item { Layout.preferredWidth: 28 }
                component ColumnHeader: Item {
                    id: columnHeader
                    property string title
                    property string column
                    property Item dragContainer: null
                    property int colIndex: -1
                    property bool resizable: false
                    implicitHeight: 30
                    Rectangle {
                        id: headerBox
                        width: columnHeader.width
                        height: columnHeader.height
                        radius: 3
                        color: (headerMouse.containsMouse || headerBox.Drag.active) ? "#14000000" : "transparent"
                        z: headerBox.Drag.active ? 10 : 0
                        Drag.active: headerMouse.drag.active
                        Drag.dragType: Drag.None
                        Row {
                            id: headerRow
                            objectName: "columnTitleRow"
                            anchors.horizontalCenter: parent.horizontalCenter
                            anchors.verticalCenter: parent.verticalCenter
                            spacing: 3
                            Label { text: columnHeader.title; color: Theme.muted; font.bold: true; font.pixelSize: 12; font.family: Theme.fontFamily }
                            Label {
                                text: root.controller.fileListModel.sortAscending ? "▲" : "▼"
                                color: Theme.muted
                                font.pixelSize: 9
                                visible: root.controller.fileListModel.sortColumn === columnHeader.column
                            }
                        }
                        MouseArea {
                            id: headerMouse
                            anchors.fill: parent
                            anchors.rightMargin: columnHeader.resizable ? 10 : 0
                            hoverEnabled: true
                            cursorShape: Qt.PointingHandCursor
                            drag.target: columnHeader.dragContainer !== null ? headerBox : null
                            drag.axis: Drag.XAxis
                            onClicked: root.controller.fileListModel.setSort(columnHeader.column)
                            onReleased: {
                                if (columnHeader.dragContainer !== null && columnHeader.colIndex >= 0) {
                                    var center = headerBox.mapToItem(columnHeader.dragContainer, headerBox.width / 2, 0).x
                                    var order = root.columnOrder
                                    var acc = 0
                                    var target = 0
                                    for (var i = 0; i < order.length; i++) {
                                        var slot = root.columnWidths[order[i]] + columnHeader.dragContainer.spacing
                                        if (center > acc + slot / 2) target = i + 1
                                        acc += slot
                                    }
                                    if (target !== columnHeader.colIndex && target !== columnHeader.colIndex + 1) {
                                        var next = order.slice()
                                        next.splice(columnHeader.colIndex, 1)
                                        next.splice(target > columnHeader.colIndex ? target - 1 : target, 0, columnHeader.column)
                                        root.controller.setFileListColumnOrder(next)
                                    }
                                }
                                headerBox.x = 0
                            }
                        }
                    }
                    Rectangle {
                        anchors.right: parent.right
                        anchors.verticalCenter: parent.verticalCenter
                        width: 2
                        height: 16
                        visible: columnHeader.resizable
                        color: selfResizeMouse.containsMouse || selfResizeMouse.pressed ? Theme.wordmark : Theme.line
                    }
                    MouseArea {
                        id: selfResizeMouse
                        objectName: "columnResizeHandle"
                        anchors.right: parent.right
                        anchors.rightMargin: -6
                        anchors.top: parent.top
                        anchors.bottom: parent.bottom
                        width: 12
                        enabled: columnHeader.resizable
                        visible: columnHeader.resizable
                        hoverEnabled: true
                        cursorShape: Qt.SizeHorCursor
                        property real startX: 0
                        property real startWidth: 0
                        onPressed: function(mouse) {
                            startX = mapToItem(null, mouse.x, mouse.y).x
                            startWidth = columnHeader.width
                        }
                        onPositionChanged: function(mouse) {
                            if (!pressed)
                                return
                            var current = mapToItem(null, mouse.x, mouse.y).x
                            root.controller.setFileListColumnWidth(columnHeader.column, Math.round(startWidth + current - startX))
                        }
                    }
                }
                ColumnHeader { objectName: "nameColumnHeader"; title: "이름"; column: "name"; resizable: true; Layout.fillWidth: true; Layout.minimumWidth: root.columnWidths["name"]; Layout.preferredHeight: 30 }
                Row {
                    id: sortableColumns
                    spacing: 8
                    Layout.preferredHeight: 30
                    Layout.alignment: Qt.AlignVCenter
                    Repeater {
                        model: root.columnOrder
                        delegate: Item {
                            id: columnSlot
                            required property int index
                            required property string modelData
                            objectName: "sortableColumnHeader"
                            width: root.columnWidths[modelData]
                            height: 30
                            ColumnHeader {
                                anchors.fill: parent
                                anchors.rightMargin: 6
                                title: root.columnInfo[parent.modelData].title
                                column: parent.modelData
                                colIndex: parent.index
                                dragContainer: sortableColumns
                            }
                            Rectangle {
                                anchors.right: parent.right
                                anchors.verticalCenter: parent.verticalCenter
                                width: 2
                                height: 16
                                color: resizeMouse.containsMouse || resizeMouse.pressed ? Theme.wordmark : Theme.line
                            }
                            MouseArea {
                                id: resizeMouse
                                objectName: "columnResizeHandle"
                                anchors.right: parent.right
                                anchors.rightMargin: -5
                                anchors.top: parent.top
                                anchors.bottom: parent.bottom
                                width: 12
                                hoverEnabled: true
                                cursorShape: Qt.SizeHorCursor
                                property real startX: 0
                                property real startWidth: 0
                                onPressed: function(mouse) {
                                    startX = mapToItem(null, mouse.x, mouse.y).x
                                    startWidth = columnSlot.width
                                }
                                onPositionChanged: function(mouse) {
                                    if (!pressed)
                                        return
                                    var current = mapToItem(null, mouse.x, mouse.y).x
                                    root.controller.setFileListColumnWidth(columnSlot.modelData, Math.round(startWidth + current - startX))
                                }
                            }
                        }
                    }
                }
            }
        }

        ListView {
            id: fileView
            objectName: "fileListView"
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            model: root.controller.fileListModel
            contentWidth: Math.max(width, root.minListWidth)
            flickableDirection: Flickable.HorizontalAndVerticalFlick
            ScrollBar.vertical: ScrollBar { policy: ScrollBar.AsNeeded }
            ScrollBar.horizontal: ScrollBar { policy: ScrollBar.AsNeeded }

            delegate: Rectangle {
                id: fileRow
                required property int index
                required property bool checked
                required property bool isFolder
                required property string fileName
                required property string typeLabel
                required property string sizeText
                required property string modifiedText
                required property string extension
                objectName: "fileListRow"
                width: fileView.contentWidth
                height: 43
                color: fileMouse.containsMouse ? (isFolder ? Theme.surfaceMuted : Theme.accentSoft) : Theme.surface
                border.color: Theme.line
                border.width: 1

                RowLayout {
                    anchors.fill: parent
                    anchors.leftMargin: 10
                    anchors.rightMargin: 10
                    spacing: 8
                    Item {
                        Layout.preferredWidth: 28
                        Layout.fillHeight: true
                        Loader {
                            anchors.fill: parent
                            active: !fileRow.isFolder
                            sourceComponent: CheckBox {
                                objectName: "fileCheckbox"
                                checked: fileRow.checked
                                onClicked: root.controller.toggleFileSelected(fileRow.index)
                            }
                        }
                    }
                    RowLayout {
                        Layout.fillWidth: true
                        Layout.minimumWidth: root.columnWidths["name"]
                        spacing: 8
                        Item {
                            Layout.preferredWidth: 26
                            Layout.preferredHeight: 28
                            Image {
                                anchors.centerIn: parent
                                width: 24
                                height: 24
                                visible: fileRow.isFolder
                                source: visible ? "image://filesystem/folder" : ""
                                sourceSize: Qt.size(32, 32)
                                fillMode: Image.PreserveAspectFit
                            }
                            Rectangle {
                                anchors.fill: parent
                                visible: !fileRow.isFolder
                                radius: 3
                                color: fileRow.typeLabel === "한글" ? Theme.accentSoft :
                                       fileRow.typeLabel === "Word" ? "#F3F1EF" :
                                       fileRow.typeLabel === "Excel" ? Theme.successSoft :
                                       fileRow.typeLabel === "PowerPoint" ? "#FFF6E8" : Theme.dangerSoft
                                Text {
                                    anchors.centerIn: parent
                                    text: fileRow.extension.length > 2 ? fileRow.extension.substring(0, 2) : fileRow.extension
                                    color: fileRow.typeLabel === "Excel" ? Theme.success :
                                           fileRow.typeLabel === "PowerPoint" ? "#9A5B10" :
                                           Theme.red
                                    font.pixelSize: 9
                                    font.bold: true
                                }
                            }
                        }
                        Label {
                            Layout.fillWidth: true
                            text: fileRow.fileName
                            color: Theme.ink
                            font.pixelSize: 12
                            elide: Text.ElideRight
                        }
                    }
                    Repeater {
                        model: root.columnOrder
                        delegate: Label {
                            required property string modelData
                            objectName: "dataCell"
                            Layout.preferredWidth: root.columnWidths[modelData]
                            text: modelData === "type" ? fileRow.typeLabel
                                 : modelData === "size" ? fileRow.sizeText
                                 : fileRow.modifiedText
                            color: Theme.inkSecondary
                            font.pixelSize: 11
                        }
                    }
                }
                MouseArea {
                    id: fileMouse
                    anchors.fill: parent
                    anchors.leftMargin: fileRow.isFolder ? 0 : 44
                    hoverEnabled: true
                    cursorShape: Qt.PointingHandCursor
                    onClicked: {
                        if (!fileRow.isFolder)
                            root.controller.toggleFileSelected(fileRow.index)
                    }
                    onDoubleClicked: {
                        if (fileRow.isFolder)
                            root.controller.openListedFolder(fileRow.index)
                    }
                }
            }

            Label {
                anchors.centerIn: parent
                visible: fileView.count === 0
                text: "이 폴더에 하위 폴더나 지원되는 문서 파일이 없습니다."
                color: Theme.muted
                font.pixelSize: 13
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 36
            color: Theme.surfaceMuted
            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 12
                anchors.rightMargin: 12
                Label { text: root.controller.currentFolderSummary; color: Theme.inkSecondary; font.pixelSize: 11; font.family: Theme.fontFamily }
                Item { Layout.fillWidth: true }
                Label { text: root.controller.selectionSummary; color: Theme.red; font.pixelSize: 11; font.bold: true; font.family: Theme.fontFamily }
            }
        }
    }
}
