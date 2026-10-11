# Lucide icons

Official npm package: `lucide-static@1.55.0`

Source: https://registry.npmjs.org/lucide-static/-/lucide-static-1.55.0.tgz

The package SHA-512 matched npm's published integrity value:
`sha512-h18lunTFsIJWnY0FMRPjXeO9KcAtNi7fDqtqgWHOFbssfgUWsctn/pA7bpiyrd4g1DuBOJ24CsRnPfkYblwm/A==`

`codepoints.json` and `LICENSE` are extracted unchanged. `lucide.ttf` is subset
with installed FontTools to retain only private-use icon glyphs (U+E000 and
above). The package's empty ASCII glyphs would otherwise hide numbers and
lowercase text in mixed icon/text buttons; removing them enables normal Qt
font fallback for RPM, percentages and other text.
`IconMap.js` records the legacy-to-Lucide mapping used to build and check the
font. Widget text and input handlers retain their original codepoints.

`shell-icons.ttf` is built by `build-shell-icons.py` from the same Lucide
outlines. Its character map uses Omarchy's existing icon codepoints, with the
family renamed to `Warm Glass Icons`. Native Fontconfig rules make it the
icon fallback for Adwaita Sans, covering popup headings, buttons, menus,
notifications and OSD icons while normal text uses Adwaita Sans. QML uses the
single family name `Adwaita Sans`; comma-separated family strings do not work
there. Ordinary Unicode arrows and crosses can use Adwaita Sans. Application logos
remain application logos. Battery levels use Lucide's warning/low/medium/full
variants; charging uses its charging variant.

Licensing: ISC, with MIT notices for icons derived from Feather. See
[LICENSE](LICENSE) and https://lucide.dev/license.
