import QtQuick
import QtQuick.Controls.Basic
import "../theme"

ProgressBar {
    id: root

    background: Rectangle {
        implicitWidth: 120
        implicitHeight: 6
        radius: 3
        color: Theme.line
    }

    contentItem: Item {
        implicitHeight: 6
        Rectangle {
            width: Math.max(root.visualPosition > 0 ? 6 : 0, root.visualPosition * parent.width)
            height: parent.height
            radius: 3
            color: Theme.red
            visible: root.visualPosition > 0
        }
    }
}
