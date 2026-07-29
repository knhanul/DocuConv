import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    default property alias content: container.data
    property string title: ""
    property bool showTitle: title.length > 0
    property int padding: 14

    color: "#FFFFFF"
    radius: 6
    border.color: "#D8E0EC"
    border.width: 1

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: root.padding
        spacing: 10

        Label {
            visible: root.showTitle
            text: root.title
            color: "#17243A"
            font.pixelSize: 16
            font.bold: true
            Layout.fillWidth: true
        }

        Item {
            id: container
            Layout.fillWidth: true
            Layout.fillHeight: true
        }
    }
}
