import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    default property alias content: container.data
    property string title: ""
    property bool showTitle: title.length > 0
    property int padding: 14

    color: Theme.surface
    radius: Theme.radius
    border.color: Theme.line
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.padding
        spacing: 10

        RowLayout {
            visible: root.showTitle
            Layout.fillWidth: true
            spacing: 8
            Rectangle {
                Layout.preferredWidth: 3
                Layout.preferredHeight: 14
                radius: 1
                color: Theme.red
            }
            Label {
                text: root.title
                color: Theme.ink
                font.pixelSize: 15
                font.bold: true
                font.family: Theme.fontFamily
                Layout.fillWidth: true
            }
        }

        Item {
            id: container
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
