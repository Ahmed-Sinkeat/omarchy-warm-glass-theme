#!/usr/bin/env python3
"""Give existing shell icon codepoints Lucide outlines; keep text fonts separate."""
import json
from pathlib import Path
from fontTools.ttLib import TTFont
from fontTools.ttLib.tables._c_m_a_p import CmapSubtable

root = Path(__file__).resolve().parent / "assets/icons/lucide"
source = (root / "IconMap.js").read_text()
names = json.loads(source.split("var names = ", 1)[1].split("\nvar glyphs", 1)[0])
codes = json.loads((root / "codepoints.json").read_text())
font = TTFont(root / "lucide.ttf")
original = font.getBestCmap()
mapping = {ord(legacy): original[codes[name]] for legacy, name in names.items()}
assert not any(code < 128 for code in mapping), "Never replace ordinary text glyphs"
font["cmap"].tables = []
for fmt, encoding in ((4, 1), (12, 10)):
    table = CmapSubtable.newSubtable(fmt)
    table.platformID, table.platEncID, table.language = 3, encoding, 0
    table.cmap = {code: glyph for code, glyph in mapping.items() if fmt == 12 or code <= 0xffff}
    font["cmap"].tables.append(table)
for record in font["name"].names:
    value = {1: "Warm Glass Icons", 2: "Regular", 3: "Warm Glass Icons Regular",
             4: "Warm Glass Icons Regular", 6: "WarmGlassIcons-Regular",
             16: "Warm Glass Icons", 17: "Regular"}.get(record.nameID)
    if value:
        record.string = value.encode(record.getEncoding())
font["OS/2"].recalcUnicodeRanges(font)
font["OS/2"].usFirstCharIndex = min(mapping)
font["OS/2"].usLastCharIndex = min(0xffff, max(mapping))
target = root / "shell-icons.ttf"
font.save(target)
saved = TTFont(target)
assert {code: saved.getGlyphID(glyph) for code, glyph in saved.getBestCmap().items()} == {
    code: font.getGlyphID(glyph) for code, glyph in mapping.items()}
print(f"PASS: {len(mapping)} shell symbols mapped to Lucide; no ASCII replaced")
