#!/usr/bin/env python3
"""Read-only checks against the installed Omarchy; generated files stay in /tmp."""
import json
import os
from collections import Counter
from pathlib import Path
import re
import shutil
import subprocess
import tempfile
import tomllib
import xml.etree.ElementTree as ET

root = Path(__file__).resolve().parent
omarchy = Path(os.environ.get("OMARCHY_PATH", "/usr/share/omarchy"))
palette = tomllib.loads((root / "colors.toml").read_text())
shell = tomllib.loads((root / "shell.toml").read_text())


def luminance(color):
    channels = [int(color[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    linear = [v / 12.92 if v <= 0.04045 else ((v + 0.055) / 1.055) ** 2.4 for v in channels]
    return sum(a * b for a, b in zip(linear, (0.2126, 0.7152, 0.0722)))


def contrast(a, b):
    light, dark = sorted((luminance(a), luminance(b)), reverse=True)
    return (light + 0.05) / (dark + 0.05)


assert palette["mode"] == "dark"
assert contrast(palette["foreground"], palette["background"]) >= 7
assert contrast(palette["muted"], palette["background"]) >= 4.5
assert contrast(palette["red"], palette["background"]) >= 4.5
assert contrast(shell["bar"]["text"], shell["bar"]["background"]) >= 7
assert contrast(shell["bar"]["active"], shell["bar"]["background"]) >= 3
assert contrast(shell["bar"]["active"], palette["background"]) >= 4.5
for surface in ("popups", "tooltip", "notifications", "menu", "launcher", "polkit", "lock"):
    assert contrast(shell[surface]["text"], shell[surface]["background"]) >= 7, surface
wallpapers = [p for p in (root / "backgrounds").iterdir() if p.suffix in (".png", ".jpg")]
assert len(wallpapers) == 18, "The selected rotation must contain all 18 wallpapers"
for wallpaper in wallpapers:
    signature = wallpaper.read_bytes()[:8]
    assert signature.startswith(b"\x89PNG\r\n\x1a\n" if wallpaper.suffix == ".png" else b"\xff\xd8"), wallpaper
assert (root / "LICENSE").is_file()
assert not list(root.rglob("*.dmg")), "Reference downloads must stay outside the release"
ET.parse(root / "preview.svg")
for block in re.findall(r"```(?:bash|sh)\n(.*?)```", (root / "README.md").read_text(), re.S):
    subprocess.run(["bash", "-n"], input=block, text=True, check=True)

with tempfile.TemporaryDirectory(prefix="warm-glass-check-") as tmp:
    staging = Path(tmp)
    commands = staging / "commands"
    commands.mkdir()
    mock = commands / "omarchy"
    mock.write_text('#!/bin/sh\nprintf "%s\\n" "$@" > "$HOME/called"\n')
    mock.chmod(0o755)
    home = staging / "home"
    home.mkdir()
    env = {**os.environ, "HOME": str(home), "PATH": str(commands) + os.pathsep + os.environ["PATH"]}
    subprocess.run(["bash", str(root / "install-simple.sh")], env=env, check=True)
    called = home / "called"
    assert called.read_text().splitlines() == ["theme", "install", "https://github.com/Ahmed-Sinkeat/omarchy-warm-glass-theme.git"]
    called.unlink()
    theme = home / ".config/omarchy/themes/warm-glass"
    theme.mkdir(parents=True)
    for dangling in (False, True):
        if dangling:
            theme.rmdir()
            theme.symlink_to(home / "missing")
        result = subprocess.run(["bash", str(root / "install-simple.sh")], env=env, capture_output=True)
        assert result.returncode != 0 and not called.exists(), "Existing setup was passed to the destructive native installer"
    result = subprocess.run(["bash", str(root / "install-simple.sh"), "unexpected"], env=env, capture_output=True)
    assert result.returncode != 0 and not called.exists()

with tempfile.TemporaryDirectory(prefix="warm-glass-templates-") as tmp:
    staging = Path(tmp)
    for name in ("colors.toml", "shell.toml", "icons.theme"):
        shutil.copy2(root / name, staging / name)
    shutil.copy2(root / "extras/hyprland.lua", staging / "hyprland.lua")
    subprocess.run(["luac", "-p", str(staging / "hyprland.lua")], check=True)
    subprocess.run(["bash", "-n", str(root / "install.sh")], check=True)
    subprocess.run(["bash", "-n", str(root / "install-simple.sh")], check=True)
    subprocess.run(["bash", "-n", str(root / "uninstall.sh")], check=True)

    # Run Omarchy's real generator, pointing only its staging directory at /tmp.
    generator = (omarchy / "bin/omarchy-theme-set-templates").read_text()
    assignment = 'NEXT_THEME_DIR="$HOME/.local/state/omarchy/current/next-theme"'
    assert generator.count(assignment) == 1, "Omarchy staging layout changed"
    generator = generator.replace(assignment, 'NEXT_THEME_DIR="$WARM_GLASS_CHECK_DIR"')
    subprocess.run(["bash", "-c", generator], check=True,
                   env={**os.environ, "OMARCHY_PATH": str(omarchy), "WARM_GLASS_CHECK_DIR": tmp})
    generated = list(staging.iterdir())
    assert len(generated) > 15, "Omarchy templates were not generated"
    for file in generated:
        assert "{{" not in file.read_text(), f"Unresolved template token in {file.name}"
        if file.suffix == ".json":
            json.loads(file.read_text())
        if file.suffix == ".toml":
            tomllib.loads(file.read_text())

    original = (omarchy / "shell/plugins/bar/Bar.qml").read_text()
    (staging / "Bar.qml").write_text(original)
    shutil.copy2(omarchy / "shell/plugins/bar/BarModel.js", staging / "BarModel.js")
    (staging / "qs").symlink_to(omarchy / "shell", target_is_directory=True)

    def qml_diagnostics():
        result = subprocess.run(["/usr/lib/qt6/bin/qmllint", "-I", tmp, "--json", "-",
                                 "--max-warnings", "100000", str(staging / "Bar.qml")],
                                check=True, capture_output=True, text=True)
        data = json.loads(result.stdout)
        return Counter((w["id"], w["type"], w["message"])
                       for file in data["files"] for w in file["warnings"])

    baseline = qml_diagnostics()
    subprocess.run(["patch", "--batch", "--fuzz=0", f"--directory={tmp}",
                    "--input", str(root / "bar.patch")], check=True)
    patched = (staging / "Bar.qml").read_text()
    assert "property color foreground: Color.foreground" in patched
    assert "property color background: Color.background" in patched
    assert patched.count('root.transparent ? "transparent" : root.barBackground') == 4
    assert 'root.transparent ? "transparent" : root.background' not in patched
    assert 'Color.shellValues["font.family"] || "monospace"' in patched
    # Keep every existing interaction, service, and hardware control intact.
    assert abs(len(patched) - len(original)) < 400
    new_diagnostics = qml_diagnostics() - baseline
    assert not new_diagnostics, f"New QML diagnostics: {new_diagnostics}"

print("PASS: native theme layout, license/assets, README commands, preview, contrast, templates and syntax")
print("PASS: Qt 6 QML lint adds no diagnostics over the installed stock bar")
