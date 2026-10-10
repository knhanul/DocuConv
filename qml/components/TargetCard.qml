import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import "../theme"

Rectangle {
    id: root
    property string title: ""
    property string subtitle: ""
    property string iconText: ""
    property color accentColor: Theme.red
    property bool selected: false
    property string notice: ""
    property var chips: []
    signal clicked()

    implicitWidth: 150
    radius: Theme.radius
    color: selected ? Theme.accentSoft : Theme.surface
    border.color: selected ? accentColor : Theme.line
    border.width: selected ? 1.5 : 1

    Behavior on color {
        ColorAnimation { duration: 140 }
    }

    MouseArea {
        anchors.fill: parent
        cursorShape: Qt.PointingHandCursor
        onClicked: root.clicked()
    }

    Rectangle {
        visible: root.selected
        anchors.left: parent.left
        anchors.right: parent.right
        anchors.top: parent.top
        anchors.leftMargin: 1
        anchors.rightMargin: 1
        height: 3
        radius: 1
        color: root.accentColor
    }

    ColumnLayout {
        anchors.fill: parent
        anchors.margins: 12
        anchors.topMargin: 16
        spacing: 8

        RowLayout {
            Layout.fillWidth: true
            spacing: 10
            Rectangle {
                Layout.preferredWidth: 42
                Layout.preferredHeight: 42
                radius: Theme.radiusSm
                color: root.selected
                       ? Qt.rgba(root.accentColor.r, root.accentColor.g, root.accentColor.b, 0.14)
                       : Theme.surfaceMuted
                Text {
                    anchors.centerIn: parent
                    text: root.iconText
                    color: root.selected ? root.accentColor : Theme.inkSecondary
                    font.pixelSize: root.iconText.length > 2 ? 11 : 15
                    font.bold: true
                    font.family: Theme.fontFamily
                }
            }
            ColumnLayout {
                Layout.fillWidth: true
                spacing: 2
                Label {
                    text: root.title
                    color: Theme.ink
                    font.pixelSize: 15
                    font.bold: true
                    font.family: Theme.fontFamily
                    elide: Text.ElideRight
                    Layout.fillWidth: true
                }
                Label {
                    text: root.subtitle
                    color: Theme.inkSecondary
                    font.pixelSize: 11
                    font.family: Theme.fontFamily
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }
            }
        }

        Item {
            visible: root.chips.length > 0
            Layout.fillWidth: true
            implicitWidth: 10
            implicitHeight: chipFlow.implicitHeight
            Flow {
                id: chipFlow
                width: parent.width
                spacing: 5
                Repeater {
                    model: root.chips
                    delegate: Rectangle {
                        required property var modelData
                        width: chipText.implicitWidth + 12
                        height: 22
                        radius: 4
                        color: root.selected ? Theme.surface : Theme.surfaceMuted
                        border.color: Theme.line
                        border.width: 1
                        Text {
                            id: chipText
                            anchors.centerIn: parent
                            text: modelData
                            color: Theme.inkSecondary
                            font.pixelSize: 10
                            font.bold: true
                            font.family: Theme.fontFamily
                        }
                    }
                }
            }
        }

        Rectangle {
            visible: root.notice.length > 0
            implicitWidth: 0
            Layout.fillWidth: true
            Layout.preferredHeight: noticeText.implicitHeight + 14
            radius: Theme.radiusSm
            color: Theme.warningSoft
            border.color: Theme.warningLine
            border.width: 1
            RowLayout {
                anchors.fill: parent
                anchors.margins: 8
                spacing: 7
                Rectangle {
                    Layout.preferredWidth: 6
                    Layout.preferredHeight: 6
                    radius: 3
                    color: Theme.orange
                }
                Text {
                    id: noticeText
                    Layout.fillWidth: true
                    text: root.notice
                    color: Theme.warningInk
                    font.pixelSize: 11
                    font.family: Theme.fontFamily
                    wrapMode: Text.WordWrap
                }
            }
        }

        Item { Layout.fillHeight: true }
    }
}
