# Warm Glass

A warm dark Omarchy theme: charcoal surfaces, ivory text, muted gold accents and soft transparency.

![Warm Glass desktop](screenshots/desktop.png)

Made for **Omarchy 4.0.0.alpha with the Quickshell shell**. Includes 18 wallpapers.

## Install

**Theme only** (colors, top bar styling and wallpapers):

```sh
omarchy theme install https://github.com/Ahmed-Sinkeat/omarchy-warm-glass-theme
```

**Full setup** (everything above, plus Lucide icons, matching menus and popups, rounded windows,
warm borders, blur and shadows):

```sh
git clone https://github.com/Ahmed-Sinkeat/omarchy-warm-glass-theme.git
cd omarchy-warm-glass-theme
bash install.sh
```

The full setup backs up your current settings first and keeps your current wallpaper. Pick an
included one with **Style → Background**, or run `omarchy theme bg next`.

## Remove

**Theme only:** switch to another theme, then remove this one:

```sh
omarchy theme set "Tokyo Night"
omarchy theme remove warm-glass
```

**Full setup:** from the cloned folder:

```sh
bash uninstall.sh
```

It restores your previous theme, wallpaper, bar and fonts from the backups made during install.
Nothing is deleted: removed files are moved into `~/.local/state/omarchy/warm-glass-backup-*`.

<details>
<summary>More screenshots</summary>

![Warm Glass menu](screenshots/menu.png)

![Warm Glass calendar](screenshots/calendar.png)

Screenshots show the full setup. See the [color palette](preview.svg).

</details>

<details>
<summary>Full setup details</summary>

Requires Python 3.11+, Python FontTools, Node.js, `patch`, Lua's `luac`, Fontconfig tools,
`g++`, `pkg-config`, Qt 6 Gui/Qml development files, `qml6`,
`/usr/lib/qt6/bin/qmllint` and Adwaita Sans. The script does not install packages.

It refuses to run if Warm Glass is already installed, so install the full setup directly rather
than after the theme-only install. It makes personal copies of the shell plugins it changes,
installs an icon font fallback, removes the persistent no-gaps override, reloads Hyprland and
restarts the shell. Input handlers and hardware commands are left alone.

Bar opacity is 90%; menus/panels 95%; tooltips/notifications 97%. Text and icons stay opaque.
Terminal fonts and prompts keep their current settings. Switching to another theme changes the
colors but leaves the plugin copies and font fallback in place; run `bash uninstall.sh` to
remove those too.

To update an existing full setup, pull the latest version and run:

```sh
python3 update-controls.py --apply
python3 update-controls.py --bar --apply
```

Checks (`python3 check.py`) cover theme generation, palette contrast, TOML/JSON, Lua/Bash
syntax, QML patches, icon fonts and battery states.

</details>

## Credits and license

Theme/helper code: [MIT](LICENSE). Fonts: [Lucide ISC and Feather MIT](assets/icons/lucide/LICENSE),
with [source/build notes](assets/icons/lucide/SOURCE.md). Apple fonts and SF Symbols are not included.
Yaru icons and Adwaita Sans come from the user's system.

The included wallpapers are third-party artwork, separate from the theme's MIT license.
See [wallpaper sources and attribution status](backgrounds/README.md).
