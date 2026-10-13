#!/usr/bin/env bash
# Undo the full setup made by install.sh, using the backups it and update-controls.py saved.
# Removed files are moved into the backup folders, never deleted.
set -euo pipefail
[[ $# == 0 ]] || { echo 'Usage: uninstall.sh' >&2; exit 1; }
state="$HOME/.local/state/omarchy"
shopt -s nullglob

initial_backups=("$state"/warm-glass-backup-*)
(( ${#initial_backups[@]} )) || {
  echo 'No full-setup backup found. For the simple install, run:' >&2
  echo '  omarchy theme set "Tokyo Night" && omarchy theme remove warm-glass' >&2
  exit 1
}
initial=${initial_backups[-1]}
stamp=${initial##*warm-glass-backup-}
for file in theme.name shell.json; do
  [[ -f "$initial/$file" ]] || { echo "Backup is incomplete, missing: $initial/$file" >&2; exit 1; }
done

# Control/icon updates made after this install, newest first.
updates=()
for backup in "$state"/warm-glass-controls-*; do
  if [[ ${backup##*warm-glass-controls-} > $stamp ]]; then updates=("$backup" "${updates[@]}"); fi
done

echo "Restoring from $initial and ${#updates[@]} later update backup(s)."
echo 'Files you edited after installing Warm Glass will return to their saved versions.'
read -rp 'Continue? [y/N] ' answer
[[ $answer == [yY] ]] || exit 1

for backup in "${updates[@]}"; do
  for tree in .config .local/state; do
    if [[ -d "$backup/$tree" ]]; then cp -a -- "$backup/$tree/." "$HOME/$tree/"; fi
  done
done
cp -- "$initial/shell.json" "$HOME/.config/omarchy/shell.json"
OMARCHY_THEME_SKIP_BACKGROUND=1 omarchy theme set "$(cat "$initial/theme.name")"
omarchy theme bg set "$initial"/wallpaper.*

for backup in "${updates[@]}" "$initial"; do
  mkdir -p "$backup/removed-plugins"
  # Older versions did not record created plugins: install.sh only made the personal bar clone.
  if [[ -f "$backup/created-plugins" ]]; then plugins=$(cat "$backup/created-plugins")
  elif [[ $backup == "$initial" ]]; then plugins=${USER:-$(id -un)}.bar
  else plugins=''; fi
  while IFS= read -r plugin; do
    if [[ -n "$plugin" && -d "$HOME/.config/omarchy/plugins/$plugin" ]]; then
      mv -n -- "$HOME/.config/omarchy/plugins/$plugin" "$backup/removed-plugins/"
      test ! -d "$HOME/.config/omarchy/plugins/$plugin"
    fi
  done <<< "$plugins"
done

mkdir -p "$initial/removed-fonts"
for file in "$HOME/.local/share/fonts/warm-glass-icons.ttf" "$HOME/.config/fontconfig/conf.d/99-warm-glass-icons.conf"; do
  if [[ -f "$file" ]]; then
    mv -n -- "$file" "$initial/removed-fonts/"
    test ! -f "$file"
  fi
done
for pair in "themes/warm-glass:removed-theme" "backgrounds/warm-glass:removed-backgrounds"; do
  dir="$HOME/.config/omarchy/${pair%%:*}"
  if [[ -d "$dir" ]]; then
    mv -n -- "$dir" "$initial/${pair##*:}"
    test ! -d "$dir"
  fi
done

fc-cache -f "$HOME/.local/share/fonts"
omarchy restart shell
hyprctl reload
hyprctl configerrors
echo "Warm Glass removed. Everything moved out is kept in: $initial"
echo 'Your previous wallpaper is stored there too, so keep that folder while it is selected.'
