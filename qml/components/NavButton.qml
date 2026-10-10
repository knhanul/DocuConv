import QtQuick
import QtQuick.Controls.Basic
import "../theme"

Button {
    id: root
    property string iconKind: "files"
    property bool selected: false

    width: 100
    height: 92
    hoverEnabled: true
    padding: 0
    font.family: Theme.fontFamily

    readonly property color iconColor: selected ? Theme.orange : (hovered ? Theme.sidebarText : Theme.sidebarMuted)

    background: Rectangle {
        color: root.selected ? Theme.sidebarSelected : (root.hovered ? Theme.sidebarHover : "transparent")
        Rectangle {
            visible: root.selected
            width: 3
            height: parent.height
            anchors.left: parent.left
            color: Theme.red
        }
    }

    contentItem: Column {
        spacing: 8
        width: root.width
        anchors.verticalCenter: parent.verticalCenter

        Item {
            width: parent.width
            height: 22
            Item {
                anchors.centerIn: parent
                width: 26
                height: 22

                Item {
                    anchors.fill: parent
                    visible: root.iconKind === "files"
                    Rectangle {
                        x: 1
                        y: 1
                        width: 11
                        height: 5
                        radius: 1.5
                        color: "transparent"
                        border.color: root.iconColor
                        border.width: 1.6
                    }
                    Rectangle {
                        x: 1
                        y: 5
                        width: 22
                        height: 15
                        radius: 2
                        color: "transparent"
                        border.color: root.iconColor
                        border.width: 1.6
                    }
                }

                Item {
                    anchors.fill: parent
                    visible: root.iconKind === "history"
                    Rectangle {
                        x: 2
                        y: 1
                        width: 20
                        height: 20
                        radius: 10
                        color: "transparent"
                        border.color: root.iconColor
                        border.width: 1.6
                    }
                    Rectangle {
                        x: 11
                        y: 5
                        width: 1.7
                        height: 7
                        radius: 1
                        color: root.iconColor
                    }
                    Rectangle {
                        x: 11
                        y: 11
                        width: 6
                        height: 1.7
                        radius: 1
                        color: root.iconColor
                    }
                }
            }
        }

        Text {
            width: parent.width
            text: root.text
            color: root.selected ? Theme.sidebarText : Theme.sidebarMuted
            font.family: Theme.fontFamily
            font.pixelSize: 12
            font.bold: root.selected
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideNone
        }
    }
}
