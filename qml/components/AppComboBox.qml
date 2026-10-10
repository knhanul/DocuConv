pragma ComponentBehavior: Bound

import QtQuick
import QtQuick.Controls.Basic

ComboBox {
    id: control
    font.pixelSize: 12

    delegate: ItemDelegate {
        id: itemDelegate
        required property var modelData
        required property int index
        width: ListView.view ? ListView.view.width : control.width
        highlighted: control.highlightedIndex === index
        contentItem: Text {
            text: itemDelegate.modelData
            color: "#26364D"
            font: control.font
            elide: Text.ElideRight
            verticalAlignment: Text.AlignVCenter
        }
        background: Rectangle {
            color: itemDelegate.highlighted || itemDelegate.hovered ? "#EAF2FF" : "#FFFFFF"
        }
    }

    popup: Popup {
        y: control.height
        width: control.width
        implicitHeight: Math.min(contentItem.implicitHeight + 2, 220)
        padding: 1

        contentItem: ListView {
            clip: true
            implicitHeight: contentHeight
            model: control.popup.visible ? control.delegateModel : null
            currentIndex: control.highlightedIndex
            ScrollBar.vertical: ScrollBar { }
        }

        background: Rectangle {
            color: "#FFFFFF"
            border.color: "#D8E0EC"
            radius: 4
        }
    }
}
