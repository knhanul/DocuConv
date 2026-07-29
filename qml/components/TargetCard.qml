import QtQuick
import QtQuick.Controls
import QtQuick.Layouts

Rectangle {
    id: root
    property string title: ""
    property string subtitle: ""
    property string iconText: ""
    property color accentColor: "#2F74E8"
    property bool selected: false
    property string notice: ""
    property var chips: []
    signal clicked()

    radius: 6
    color: selected ? "#F7FAFF" : "#FFFFFF"
    border.color: selected ? accentColor : "#D8E0EC"
    border.width: selected ? 2 : 1

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 13
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Rectangle {
                width: 46
                height: 46
                radius: 6
                color: Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.12)
                Text {
                    anchors.centerIn: parent
                    text: root.iconText
                    color: root.accentColor
                    font.pixelSize: 22
                    font.bold: true
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 3
                Label {
                    text: root.title
                    color: "#152239"
                    font.pixelSize: 16
                    font.bold: true
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Label {
                    text: root.subtitle
                    color: "#687992"
                    font.pixelSize: 12
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        Flow {
            visible: root.chips.length > 0
            Layout.fillWidth: true
            spacing: 5
            Repeater {
                model: root.chips
                delegate: Rectangle {
                    required property var modelData
                    width: chipText.implicitWidth + 14
                    height: 24
                    radius: 4
                    color: "#F0F4FA"
                    Text {
                        id: chipText
                        anchors.centerIn: parent
                        text: modelData
                        color: "#576A84"
                        font.pixelSize: 11
                    }
                }
            }
        }

        Rectangle {
            visible: root.notice.length > 0
            Layout.fillWidth: true
            Layout.preferredHeight: noticeText.implicitHeight + 16
            radius: 5
            color: "#FFF8E8"
            border.color: "#F1D28B"
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 7
                Text { text: "ⓘ"; color: "#E49A00"; font.pixelSize: 15 }
                Text {
                    id: noticeText
                    Layout.fillWidth: true
                    text: root.notice
                    color: "#5D513A"
                    font.pixelSize: 11
                    font.bold: true
                    wrapMode: Text.WordWrap
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
