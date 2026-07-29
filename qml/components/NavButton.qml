import QtQuick
import QtQuick.Controls

Button {
    id: root
    property string iconText: ""
    property bool selected: false

    width: 94
    height: 104
    hoverEnabled: true

    background: Rectangle {
        color: root.selected ? "#253A55" : (root.hovered ? "#26384F" : "transparent")
        Rectangle {
            visible: root.selected
            width: 4
            height: parent.height
            color: "#FF6B24"
            anchors.left: parent.left
        }
    }

    contentItem: Column {
        spacing: 9
        anchors.centerIn: parent
        Text {
            text: root.iconText
            color: "#FFFFFF"
            font.pixelSize: 28
            anchors.horizontalCenter: parent.horizontalCenter
        }
        Text {
            text: root.text
            color: root.selected ? "#FFFFFF" : "#D5DDE8"
            font.pixelSize: 13
            font.bold: root.selected
            anchors.horizontalCenter: parent.horizontalCenter
        }
    }
}
