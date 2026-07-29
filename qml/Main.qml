import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtQuick.Window
import "components"
import "pages"

ApplicationWindow {
    id: window
    width: 1600
    height: 920
    minimumWidth: 1280
    minimumHeight: 760
    visible: true
    title: "포시드 문서 변환기"
    color: "#F4F7FB"
    font.family: "Malgun Gothic"

    property int currentPage: 0

    Dialog {
        id: messageDialog
        property string level: "info"
        modal: true
        anchors.centerIn: parent
        width: 430
        title: "안내"
        standardButtons: Dialog.Ok
        contentItem: Label {
            text: messageDialogText.text
            color: "#25364E"
            font.pixelSize: 13
            wrapMode: Text.WordWrap
            padding: 16
        }
        Text { id: messageDialogText; visible: false }
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
            Layout.preferredHeight: 84
            color: "#FFFFFF"
            border.color: "#E2E7EE"
            border.width: 1

            RowLayout {
                anchors.fill: parent
                anchors.leftMargin: 20
                anchors.rightMargin: 20
                spacing: 15

                Image {
                    source: appController.logoPath
                    Layout.preferredWidth: 50
                    Layout.preferredHeight: 50
                    fillMode: Image.PreserveAspectFit
                    smooth: true
                }
                ColumnLayout {
                    Layout.fillWidth: true
                    spacing: 3
                    Label {
                        text: "포시드 문서 변환기"
                        color: "#13223A"
                        font.pixelSize: 25
                        font.bold: true
                    }
                    Label {
                        text: "HWP/HWPX 및 Office 문서를 HWPX, PDF, 이미지로 변환합니다."
                        color: "#71819A"
                        font.pixelSize: 13
                    }
                }
            }
        }

        RowLayout {
            Layout.fillWidth: true
            Layout.fillHeight: true
            spacing: 0

            Rectangle {
                Layout.preferredWidth: 94
                Layout.fillHeight: true
                color: "#203147"

                Column {
                    anchors.fill: parent
                    spacing: 0

                    NavButton {
                        iconText: "▰"
                        text: "파일 탐색"
                        selected: window.currentPage === 0
                        onClicked: window.currentPage = 0
                    }
                    NavButton {
                        iconText: "▤"
                        text: "작업 이력"
                        selected: window.currentPage === 1
                        onClicked: window.currentPage = 1
                    }

                    Item { width: 1; height: Math.max(0, window.height - 84 - 208 - 44) }
                    Label {
                        width: 94
                        height: 44
                        text: "v1.0.0"
                        color: "#CED7E3"
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                        font.pixelSize: 11
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
