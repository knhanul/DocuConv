import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"
import "pages"
import "theme"

ApplicationWindow {
    id: window
    width: 1600
    height: 920
    minimumWidth: 1280
    minimumHeight: 760
    visible: true
    title: "포시드 문서 변환기"
    color: Theme.canvas
    font.family: Theme.fontFamily
    font.pixelSize: 13

    palette.highlight: Theme.red
    palette.highlightedText: "white"
    palette.accent: Theme.red
    palette.window: Theme.canvas
    palette.windowText: Theme.ink
    palette.base: Theme.surface
    palette.text: Theme.ink
    palette.button: Theme.surface
    palette.buttonText: Theme.ink
    palette.mid: Theme.line

    property int currentPage: 0

    Dialog {
        id: messageDialog
        property string level: "info"
        modal: true
        anchors.centerIn: parent
        width: 440
        padding: 0
        title: "안내"
        standardButtons: Dialog.Ok

        background: Rectangle {
            color: Theme.surface
            border.color: Theme.line
            border.width: 1
            radius: Theme.radius
        }

        contentItem: ColumnLayout {
            spacing: 0
            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 4
                gradient: Gradient {
                    orientation: Gradient.Horizontal
                    GradientStop { position: 0.0; color: Theme.gold }
                    GradientStop { position: 0.48; color: Theme.orange }
                    GradientStop { position: 1.0; color: Theme.red }
                }
            }
            Label {
                Layout.fillWidth: true
                Layout.margins: 18
                text: messageDialogText.text
                color: Theme.ink
                font.pixelSize: 13
                font.family: Theme.fontFamily
                wrapMode: Text.WordWrap
            }
        }
        Text { id: messageDialogText; visible: false }
    }

    Dialog {
        id: aboutDialog
        modal: true
        anchors.centerIn: parent
        width: 520
        padding: 0
        title: "버전 정보"
        standardButtons: Dialog.Ok

        background: Rectangle {
            color: Theme.surface
            border.color: Theme.line
            border.width: 1
            radius: Theme.radius
        }

        contentItem: ColumnLayout {
            spacing: 0

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 92
                color: Theme.sidebar
                Image {
                    anchors.centerIn: parent
                    width: 168
                    height: 80
                    source: appController.signatureWhitePath
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                }
            }

            ColumnLayout {
                Layout.fillWidth: true
                Layout.margins: 18
                spacing: 14

                Image {
                    source: appController.aiResearchImagePath
                    Layout.fillWidth: true
                    Layout.preferredHeight: 240
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    Layout.alignment: Qt.AlignHCenter
                }

                Label {
                    text: "우체국금융개발원 우정정보관리원 AI킥오프모임"
                    color: Theme.ink
                    font.pixelSize: 15
                    font.bold: true
                    font.family: Theme.fontFamily
                    Layout.alignment: Qt.AlignHCenter
                    horizontalAlignment: Text.AlignHCenter
                    wrapMode: Text.WordWrap
                    Layout.fillWidth: true
                }

                Rectangle {
                    Layout.fillWidth: true
                    Layout.preferredHeight: 1
                    color: Theme.line
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Label {
                        text: "버전"
                        color: Theme.muted
                        font.pixelSize: 13
                        font.family: Theme.fontFamily
                        Layout.preferredWidth: 80
                    }
                    Label {
                        text: appController.appVersion
                        color: Theme.ink
                        font.pixelSize: 13
                        font.bold: true
                        font.family: Theme.fontFamily
                    }
                }

                RowLayout {
                    Layout.fillWidth: true
                    spacing: 8
                    Label {
                        text: "빌드 날짜"
                        color: Theme.muted
                        font.pixelSize: 13
                        font.family: Theme.fontFamily
                        Layout.preferredWidth: 80
                    }
                    Label {
                        text: appController.buildDate
                        color: Theme.ink
                        font.pixelSize: 13
                        font.bold: true
                        font.family: Theme.fontFamily
                    }
                }
            }
        }
    }

    Connections {
        target: appController
        function onNotify(title, message, level) {
            messageDialog.title = title
            messageDialogText.text = message
            messageDialog.level = level
            messageDialog.open()
        }
    }

    ColumnLayout {
        anchors.fill: parent
        spacing: 0

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 4
            gradient: Gradient {
                orientation: Gradient.Horizontal
                GradientStop { position: 0.0; color: Theme.gold }
                GradientStop { position: 0.48; color: Theme.orange }
                GradientStop { position: 1.0; color: Theme.red }
            }
        }

        Rectangle {
            Layout.fillWidth: true
            Layout.preferredHeight: 84
            color: Theme.surface
            border.color: Theme.line
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 18
                anchors.rightMargin: 16
                spacing: 14

                Image {
                    source: appController.signaturePath
                    Layout.preferredWidth: 148
                    Layout.preferredHeight: 70
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                    mipmap: true
                    Layout.alignment: Qt.AlignVCenter
                }

                Rectangle {
                    Layout.preferredWidth: 1
                    Layout.preferredHeight: 40
                    color: Theme.line
                }

                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 2
                    Label {
                        text: "문서 변환기"
                        color: Theme.ink
                        font.pixelSize: 22
                        font.bold: true
                        font.family: Theme.fontFamily
                    }
                    Label {
                        text: "HWP/HWPX와 Office 문서를 HWPX, PDF, 이미지로 변환합니다."
                        color: Theme.inkSecondary
                        font.pixelSize: 12
                        font.family: Theme.fontFamily
                    }
                }

                Item { Layout.fillWidth: true }

                AbstractButton {
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: Qt.AlignVCenter
                    Accessible.name: "버전 정보"

                    contentItem: Text {
                        text: "i"
                        color: parent.hovered ? Theme.red : Theme.inkSecondary
                        font.pixelSize: 16
                        font.bold: true
                        font.family: "Times New Roman"
                        font.italic: true
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        color: parent.hovered ? Theme.accentSoft : "transparent"
                        radius: 18
                        border.color: parent.hovered ? Theme.accentLine : Theme.line
                        border.width: 1
                    }

                    onClicked: aboutDialog.open()
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 100
                Layout.fillHeight: true
                color: Theme.sidebar

                Column {
                    anchors.fill: parent
                    spacing: 0

                    NavButton {
                        iconKind: "files"
                        text: "파일 탐색"
                        selected: window.currentPage === 0
                        onClicked: window.currentPage = 0
                    }
                    NavButton {
                        iconKind: "history"
                        text: "작업 이력"
                        selected: window.currentPage === 1
                        onClicked: window.currentPage = 1
                    }

                    Item { width: 1; height: Math.max(0, window.height - 88 - 184 - 52) }
                    Rectangle {
                        width: 100
                        height: 1
                        color: "#3A3C3F"
                    }
                    Label {
                        width: 100
                        height: 40
                        text: "v" + appController.appVersion
                        color: Theme.sidebarMuted
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 11
                        font.family: Theme.fontFamily
                    }
                }
            }

            StackLayout {
                Layout.fillWidth: true
                Layout.fillHeight: true
                currentIndex: window.currentPage
                ConverterPage {}
                HistoryPage {}
            }
        }
    }
}
