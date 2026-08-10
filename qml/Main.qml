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

    Dialog {
        id: aboutDialog
        modal: true
        anchors.centerIn: parent
        width: 520
        title: "버전 정보"
        standardButtons: Dialog.Ok

        background: Rectangle {
            color: "#FFFFFF"
            border.color: "#E2E7EE"
            border.width: 1
            radius: 8
        }

        contentItem: ColumnLayout {
            spacing: 16
            Layout.fillWidth: true

            Image {
                source: appController.aiResearchImagePath
                Layout.fillWidth: true
                Layout.preferredHeight: 280
                fillMode: Image.PreserveAspectFit
                smooth: true
                Layout.alignment: Qt.AlignHCenter
            }

            Label {
                text: "우체국금융개발원 우정정보관리원 AI킥오프모임"
                color: "#13223A"
                font.pixelSize: 16
                font.bold: true
                Layout.alignment: Qt.AlignHCenter
            }

            Rectangle {
                Layout.fillWidth: true
                Layout.preferredHeight: 1
                color: "#E2E7EE"
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "버전"
                    color: "#71819A"
                    font.pixelSize: 13
                    Layout.preferredWidth: 80
                }
                Label {
                    text: appController.appVersion
                    color: "#25364E"
                    font.pixelSize: 13
                    font.bold: true
                }
            }

            RowLayout {
                Layout.fillWidth: true
                spacing: 8

                Label {
                    text: "빌드 날짜"
                    color: "#71819A"
                    font.pixelSize: 13
                    Layout.preferredWidth: 80
                }
                Label {
                    text: appController.buildDate
                    color: "#25364E"
                    font.pixelSize: 13
                    font.bold: true
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

                Item { Layout.fillWidth: true }

                AbstractButton {
                    Layout.preferredWidth: 36
                    Layout.preferredHeight: 36
                    Layout.alignment: Qt.AlignVCenter

                    contentItem: Label {
                        text: "ⓘ"
                        color: parent.hovered ? "#13223A" : "#71819A"
                        font.pixelSize: 22
                        horizontalAlignment: Text.AlignHCenter
                        verticalAlignment: Text.AlignVCenter
                    }

                    background: Rectangle {
                        color: parent.hovered ? "#F4F7FB" : "transparent"
                        radius: 18
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
                        text: "v" + appController.appVersion
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
