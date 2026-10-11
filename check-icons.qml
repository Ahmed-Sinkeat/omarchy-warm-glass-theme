import QtQml
import "assets/icons/lucide/IconMap.js" as Icons

QtObject {
  Component.onCompleted: {
    for (var legacy in Icons.glyphs) {
      if (Icons.render(legacy) !== Icons.glyphs[legacy]) {
        console.error("FAIL: Qt icon lookup:", Icons.names[legacy])
        Qt.exit(1)
        return
      }
    }
    if (Icons.render("󰈐 1900 RPM 🐧 العربية") !== Icons.glyphs["󰈐"] + " 1900 RPM 🐧 العربية") {
      console.error("FAIL: Qt mixed icon and Unicode text")
      Qt.exit(1)
      return
    }
    Qt.exit(0)
  }
}
