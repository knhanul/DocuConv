import QtQuick
import QtQuick.Controls.Basic
import "../theme"

Button {
    id: root
    property string variant: "secondary"

    font.family: Theme.fontFamily
    font.pixelSize: 13
    font.bold: variant === "primary" || variant === "dangerSolid"
    hoverEnabled: true
    implicitHeight: 34
    leftPadding: 14
    rightPadding: 14
    spacing: 0

    readonly property color fg: {
        if (!enabled)
            return Theme.muted
        if (variant === "primary" || variant === "dangerSolid")
            return "#FFFFFF"
        if (variant === "danger")
            return Theme.danger
        return Theme.ink
    }

    background: Rectangle {
        radius: Theme.radiusSm
        border.width: (root.variant === "primary" || root.variant === "dangerSolid") ? 0 : 1
        border.color: {
            if (!root.enabled)
                return Theme.line
            if (root.visualFocus)
                return Theme.red
            if (root.variant === "danger")
                return root.hovered ? "#E7B4B0" : Theme.lineStrong
            if (root.variant === "ghost")
                return "transparent"
            return root.hovered ? Theme.accentLine : Theme.lineStrong
        }
        color: {
            if (!root.enabled)
                return Theme.surfaceMuted
            if (root.variant === "primary")
                return root.down ? Theme.redPressed : root.hovered ? Theme.redHover : Theme.red
            if (root.variant === "dangerSolid")
                return root.down ? "#7E1614" : root.hovered ? "#B42318" : Theme.danger
            if (root.variant === "danger")
                return root.hovered ? Theme.dangerSoft : Theme.surface
            if (root.variant === "ghost")
                return root.hovered ? Theme.accentSoft : "transparent"
            return root.hovered ? Theme.accentSoft : Theme.surface
        }
    }

    contentItem: Text {
        text: root.text
        font: root.font
        color: root.fg
        horizontalAlignment: Text.AlignHCenter
        verticalAlignment: Text.AlignVCenter
        elide: Text.ElideRight
    }
}
