pragma Singleton
import QtQuick

QtObject {
    // PoSID CI. 심벌 그라데이션 원색은 공식 SVG 기준.
    readonly property color gold: "#FAA619"
    readonly property color orange: "#F5821F"
    readonly property color red: "#E22A26"
    readonly property color redHover: "#C9221F"
    readonly property color redPressed: "#A31D1B"

    readonly property color ink: "#1C1C1C"
    readonly property color inkSecondary: "#5C5F64"
    readonly property color muted: "#8B8E93"
    readonly property color wordmark: "#6D6F71"

    readonly property color canvas: "#F3F1EF"
    readonly property color surface: "#FFFFFF"
    readonly property color surfaceMuted: "#F7F5F3"
    readonly property color line: "#E7E2DC"
    readonly property color lineStrong: "#D5D0CA"

    readonly property color accentSoft: "#FFF4EE"
    readonly property color accentLine: "#F3C7B8"

    readonly property color sidebar: "#292A2C"
    readonly property color sidebarHover: "#35373A"
    readonly property color sidebarSelected: "#3E4043"
    readonly property color sidebarText: "#F7F7F7"
    readonly property color sidebarMuted: "#B7B9BC"

    readonly property color success: "#1B7A46"
    readonly property color successSoft: "#E8F6EE"
    readonly property color danger: "#9F1D1A"
    readonly property color dangerSoft: "#FDECEC"
    readonly property color warningSoft: "#FFF6E8"
    readonly property color warningLine: "#F0D7A8"
    readonly property color warningInk: "#6A4E16"

    readonly property int radius: 8
    readonly property int radiusSm: 6
    readonly property string fontFamily: "Malgun Gothic"
}
