#!/usr/bin/env python3
"""Stage/verify the shared controls; --apply installs through user-owned clones."""
from collections import Counter
import hashlib
import json
import os
from pathlib import Path
import re
import shutil
import shlex
import subprocess
import sys
import tempfile
import tomllib
from xml.sax.saxutils import escape
from datetime import datetime

ROOT = Path(__file__).resolve().parent
OMARCHY = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
USER_ROOT = Path.home()
CONFIG = USER_ROOT / ".config/omarchy"
PLUGINS = CONFIG / "plugins"
TYPES = ("KeyboardPanel", "PanelSlider", "ToggleSwitch", "Button")
BAR_TYPES = ("WidgetButton", "BarIconButton", "BarIndicator")
USERNAME = os.environ.get('USER') or subprocess.check_output(["id", "-un"], text=True).strip()
BAR_ID = f"{USERNAME}.bar"
SKIN = PLUGINS / BAR_ID / "warm-ui"


def run(*args, **kwargs):
    return subprocess.run(args, check=True, **kwargs)


def diagnostics(path, imports):
    result = run("/usr/lib/qt6/bin/qmllint", "-I", str(imports), "--json", "-",
                 "--max-warnings", "100000", str(path), capture_output=True, text=True)
    return Counter((w["id"], w["type"], w["message"])
                   for f in json.loads(result.stdout)["files"] for w in f["warnings"]
                   if w["type"] == "error" or w["id"] in ("syntax", "duplicate-property-binding")
                   or (w["id"] == "missing-property" and any(
                       name in w["message"] for name in ("iconText", "iconFontFamily", "FontLoader", "IconMap"))))


def plans(types=TYPES):
    pattern = re.compile(r"(?m)^(\s*)(" + "|".join(types) + r")(\s*\{)")
    config = json.loads((CONFIG / "shell.json").read_text())
    ids = {entry["id"] if isinstance(entry, dict) else entry
           for section in config["bar"]["layout"].values() for entry in section}
    ids.update(entry["id"] for entry in config.get("plugins", []))
    if types == BAR_TYPES:
        ids.add(BAR_ID)
    sources = {}
    for manifest in (OMARCHY / "shell/plugins").rglob("manifest.json"):
        sources[json.loads(manifest.read_text())["id"]] = manifest.parent
    result = []
    for plugin_id in sorted(ids):
        local = PLUGINS / plugin_id
        source = local if local.is_dir() else sources.get(plugin_id)
        if source is None:
            continue
        files = {}
        for path in source.rglob("*.qml"):
            before = path.read_text()
            after = pattern.sub(r"\1WarmGlass.\2\3", before)
            if types == BAR_TYPES and plugin_id == f"{USERNAME}.menu":
                after = after.replace('    fontFamily: "FiraCode Nerd Font"\n', '')
            if types == BAR_TYPES and plugin_id in ("omarchy.power", f"{USERNAME}.power") and path.name == "Panel.qml":
                after = after.replace(' + "% "', ' + "% " + root.batteryIcon()')
                after = after.replace('      : ""', '      : root.batteryIcon()')
            if types == BAR_TYPES and plugin_id == BAR_ID and path.name == "Bar.qml":
                loader = '  FontLoader { source: "warm-ui/shell-icons.ttf" }\n'
                if loader not in after:
                    assert "  id: root\n" in after
                    after = after.replace("  id: root\n", "  id: root\n" + loader, 1)
            if before != after:
                skin_import = f'import "{SKIN.as_uri()}" as WarmGlass\n'
                if skin_import not in after:
                    after = skin_import + after
                files[path.relative_to(source)] = after
        if files:
            destination = local if local.is_dir() else PLUGINS / f"{USERNAME}.{plugin_id.removeprefix('omarchy.')}"
            if destination != local and destination.exists():
                raise RuntimeError(f"Existing inactive clone needs review: {destination}")
            result.append((plugin_id, source, destination, files))
    return result


def main():
    args = sys.argv[1:]
    bar_only = "--bar" in args
    apply = "--apply" in args
    if len(args) != len(set(args)) or set(args) - {"--bar", "--apply"}:
        raise SystemExit("Usage: update-controls.py [--bar] [--apply]")
    types = BAR_TYPES if bar_only else TYPES
    assert (CONFIG / "themes/warm-glass").is_dir(), "Install Warm Glass first"
    assert (PLUGINS / BAR_ID / "Bar.qml").is_file(), "Warm Glass bar clone is missing"
    changes = plans(types)
    with tempfile.TemporaryDirectory(prefix="warm-glass-controls-") as tmp:
        stage = Path(tmp)
        (stage / "qs").symlink_to(OMARCHY / "shell", target_is_directory=True)
        baseline = {}
        for name in types:
            target = stage / f"{name}.qml"
            shutil.copy2(OMARCHY / "shell/Ui" / target.name, target)
            baseline[name] = diagnostics(target, stage)
        patch = "icons.patch" if bar_only else "controls.patch"
        run("patch", "--batch", "--fuzz=0", "-p1", f"--directory={stage}",
            "--input", str(ROOT / patch))
        if bar_only:
            run("python3", str(ROOT / "build-shell-icons.py"))
            charset = run("fc-query", "--format=%{charset}", str(ROOT / "assets/icons/lucide/lucide.ttf"),
                          capture_output=True, text=True).stdout
            run("node", str(ROOT / "check-icons.cjs"), charset)
            run("qml6", "-a", "core", "-f", str(ROOT / "check-icons.qml"),
                env={**os.environ, "QT_QPA_PLATFORMTHEME": "generic"})
            print("PASS: Qt icon lookup, supplementary Unicode and mixed text")
            for name in ("IconMap.js", "lucide.ttf", "shell-icons.ttf", "LICENSE"):
                shutil.copy2(ROOT / "assets/icons/lucide" / name, stage / name)
            font_dir = stage / "fonts"
            font_dir.mkdir()
            shutil.copy2(stage / "shell-icons.ttf", font_dir)
            font_config = stage / "fonts.conf"
            font_config.write_text('<fontconfig><include>/etc/fonts/fonts.conf</include><dir>'
                + escape(str(font_dir)) + '</dir><cachedir>' + escape(str(stage / "cache"))
                + '</cachedir><include>' + escape(str(ROOT / "assets/icons/lucide/fontconfig.conf"))
                + '</include></fontconfig>')
            names = json.loads((ROOT / "assets/icons/lucide/IconMap.js").read_text()
                               .split("var names = ", 1)[1].split("\nvar glyphs", 1)[0])
            (stage / "names.json").write_text(json.dumps(names))
            flags = run("pkg-config", "--cflags", "--libs", "Qt6Gui", "Qt6Qml",
                        capture_output=True, text=True).stdout
            run("g++", "-fPIC", str(ROOT / "check-font.cpp"), "-o", str(stage / "check-font"),
                *shlex.split(flags))
            family = tomllib.loads((ROOT / "shell.toml").read_text())["font"]["family"]
            run(str(stage / "check-font"), str(stage / "lucide.ttf"), str(stage / "shell-icons.ttf"),
                str(stage / "names.json"), family, env={**os.environ,
                    "QT_QPA_PLATFORM": "offscreen", "QT_QPA_PLATFORMTHEME": "generic",
                    "FONTCONFIG_FILE": str(font_config)})
        for name in types:
            new = diagnostics(stage / f"{name}.qml", stage) - baseline[name]
            assert not new, f"New QML errors in {name}: {new}"
        interaction = "WidgetButton" if bar_only else "PanelSlider"
        original = (OMARCHY / f"shell/Ui/{interaction}.qml").read_text()
        updated = (stage / f"{interaction}.qml").read_text()
        assert original[original.index("  MouseArea {"):] == updated[updated.index("  MouseArea {"):]
        print("PASS: patch, Qt 6 syntax, unchanged input handlers")
        print("Panels:", ", ".join(item[0] for item in changes) or "already use shared controls")
        if not apply:
            return

        backup = USER_ROOT / ".local/state/omarchy" / ("warm-glass-controls-" + datetime.now().strftime("%Y%m%d-%H%M%S-%f"))
        backup.mkdir(parents=True)
        (backup / "created-plugins").write_text("".join(
            destination.name + "\n" for _, source, destination, _ in changes if destination != source))
        saved = []
        created = []

        def preserve(path):
            if path.exists():
                copy = backup / path.relative_to(USER_ROOT)
                copy.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(path, copy)
                saved.append((copy, path))

        shell_theme = CONFIG / "themes/warm-glass/shell.toml"
        current_shell = USER_ROOT / ".local/state/omarchy/current/theme/shell.toml"
        no_gaps = USER_ROOT / ".local/state/omarchy/toggles/hypr/window-no-gaps.lua"
        wallpaper = USER_ROOT / ".local/state/omarchy/current/background"
        wallpaper_hash = hashlib.sha256(wallpaper.read_bytes()).digest()
        preserve(CONFIG / "shell.json")
        preserve(shell_theme)
        if bar_only:
            preserve(current_shell)
        preserve(no_gaps)
        try:
            SKIN.mkdir(exist_ok=True)
            assets = [f"{name}.qml" for name in types]
            if bar_only:
                assets += ["IconMap.js", "lucide.ttf", "shell-icons.ttf", "LICENSE"]
            for name in assets:
                target = SKIN / name
                preserve(target)
                pending = target.with_name(target.name + ".tmp")
                shutil.copy2(stage / target.name, pending)
                pending.replace(target)
            for plugin_id, source, destination, files in changes:
                if destination != source:
                    run("omarchy", "plugin", "clone", plugin_id)
                for relative, content in files.items():
                    target = destination / relative
                    preserve(target)
                    pending = target.with_suffix(".qml.tmp")
                    pending.write_text(content)
                    pending.replace(target)
            shutil.copy2(ROOT / "shell.toml", shell_theme)
            if bar_only:
                for source, target in (
                    (stage / "shell-icons.ttf", USER_ROOT / ".local/share/fonts/warm-glass-icons.ttf"),
                    (ROOT / "assets/icons/lucide/fontconfig.conf", USER_ROOT / ".config/fontconfig/conf.d/99-warm-glass-icons.conf")):
                    if not target.exists():
                        created.append(target)
                    preserve(target)
                    target.parent.mkdir(parents=True, exist_ok=True)
                    pending = target.with_name(target.name + ".tmp")
                    shutil.copy2(source, pending)
                    pending.replace(target)
                run("fc-cache", "-f", str(USER_ROOT / ".local/share/fonts"))
                shutil.copy2(shell_theme, current_shell)
                # Imported QML helpers remain cached across plugin rescans.
                run("omarchy", "restart", "shell")
            else:
                no_gaps.unlink(missing_ok=True)
                run("omarchy", "theme", "set", "warm-glass",
                    env={**os.environ, "OMARCHY_THEME_SKIP_BACKGROUND": "1"})
                run("hyprctl", "reload")
                errors = run("hyprctl", "configerrors", capture_output=True, text=True).stdout.strip()
                assert not errors, errors
                run("omarchy-shell", "shell", "rescanPlugins")
            run("omarchy-shell", "shell", "ping")
            assert hashlib.sha256(wallpaper.read_bytes()).digest() == wallpaper_hash, "Wallpaper changed"
        except BaseException:
            for path in created:
                path.unlink(missing_ok=True)
            for copy, path in reversed(saved):
                shutil.copy2(copy, path)
            if bar_only:
                subprocess.run(["fc-cache", "-f", str(USER_ROOT / ".local/share/fonts")])
                subprocess.run(["omarchy", "restart", "shell"])
            else:
                subprocess.run(["omarchy", "theme", "set", "warm-glass"],
                               env={**os.environ, "OMARCHY_THEME_SKIP_BACKGROUND": "1"})
                subprocess.run(["hyprctl", "reload"])
                subprocess.run(["omarchy-shell", "shell", "rescanPlugins"])
            print(f"Restored saved files after failure. Backup: {backup}", file=sys.stderr)
            raise
        print(f"Updated Warm Glass {'bar icons and color' if bar_only else 'controls'}. Backup: {backup}")


if __name__ == "__main__":
    main()
