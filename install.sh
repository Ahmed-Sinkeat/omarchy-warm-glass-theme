#!/usr/bin/env bash
set -euo pipefail
[[ $# == 0 ]] || { echo 'Usage: install.sh' >&2; exit 1; }
cd -- "$(dirname -- "${BASH_SOURCE[0]}")"
python3 check.py
python3 build-shell-icons.py

theme_dir="$HOME/.config/omarchy/themes/warm-glass"
bar_dir="$HOME/.config/omarchy/plugins/${USER:-$(id -un)}.bar"
state_dir="$HOME/.local/state/omarchy/current"
backup_dir="$HOME/.local/state/omarchy/warm-glass-backup-$(date +%Y%m%d-%H%M%S)"
background_dir="$HOME/.config/omarchy/backgrounds/warm-glass"
icon_font="$HOME/.local/share/fonts/warm-glass-icons.ttf"
icon_config="$HOME/.config/fontconfig/conf.d/99-warm-glass-icons.conf"

if [[ -e "$theme_dir" || -L "$theme_dir" || -e "$bar_dir" || -L "$bar_dir" || -e "$background_dir" || -e "$icon_font" || -e "$icon_config" ]]; then
  echo "Refusing to overwrite an existing warm-glass theme, background folder, or personal bar clone." >&2
  exit 1
fi
omarchy-shell shell ping >/dev/null
previous_background=$(readlink -f "$state_dir/background")
[[ -f "$previous_background" ]] || { echo "Current wallpaper is missing; stopping before any changes." >&2; exit 1; }

mkdir -p "$backup_dir"
cp "$HOME/.config/omarchy/shell.json" "$backup_dir/shell.json"
cp "$state_dir/theme.name" "$backup_dir/theme.name"
printf '%s\n' "${bar_dir##*/}" > "$backup_dir/created-plugins"
cp "$previous_background" "$backup_dir/wallpaper.${previous_background##*.}"
printf '%s\n' "$previous_background" > "$backup_dir/background.path"
echo "Backup: $backup_dir"

rollback() {
  local status=$?
  trap - ERR
  set +e
  rm -f "$icon_font" "$icon_config"
  fc-cache -f "$HOME/.local/share/fonts"
  cp "$backup_dir/shell.json" "$HOME/.config/omarchy/shell.json"
  OMARCHY_THEME_SKIP_BACKGROUND=1 omarchy theme set "$(cat "$backup_dir/theme.name")"
  omarchy-shell shell reloadConfig
  hyprctl reload
  echo "Installation failed; rollback attempted. Backup: $backup_dir" >&2
  exit "$status"
}
trap rollback ERR

# The current wallpaper may live inside the theme directory that theme-set replaces.
mkdir -p "$background_dir"
cp "$previous_background" "$background_dir/current-wallpaper.${previous_background##*.}"
ln -nsf "$background_dir/current-wallpaper.${previous_background##*.}" "$state_dir/background"
mkdir -p "$theme_dir"
cp colors.toml shell.toml icons.theme extras/hyprland.lua "$theme_dir/"
omarchy plugin clone omarchy.bar
patch --batch --fuzz=0 --directory="$bar_dir" < bar.patch
mkdir -p "$bar_dir/warm-ui"
cp assets/icons/lucide/shell-icons.ttf "$bar_dir/warm-ui/"
cp assets/icons/lucide/LICENSE "$bar_dir/warm-ui/LUCIDE-LICENSE"
mkdir -p "$HOME/.local/share/fonts" "$HOME/.config/fontconfig/conf.d"
cp assets/icons/lucide/shell-icons.ttf "$HOME/.local/share/fonts/warm-glass-icons.ttf"
cp assets/icons/lucide/fontconfig.conf "$HOME/.config/fontconfig/conf.d/99-warm-glass-icons.conf"
fc-cache -f "$HOME/.local/share/fonts"
OMARCHY_THEME_SKIP_BACKGROUND=1 omarchy theme set warm-glass
hyprctl reload
errors=$(hyprctl configerrors)
[[ -z "$errors" ]] || { printf '%s\n' "$errors" >&2; false; }
omarchy-shell shell ping
cmp "$backup_dir/wallpaper.${previous_background##*.}" "$(readlink -f "$state_dir/background")"
trap - ERR
echo "Warm Glass applied. Wallpaper bytes unchanged. Backup: $backup_dir"
