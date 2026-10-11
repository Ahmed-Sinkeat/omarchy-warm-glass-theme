#!/usr/bin/env bash
set -euo pipefail
[[ $# == 0 ]] || { echo 'Usage: install-simple.sh' >&2; exit 1; }
theme_dir="$HOME/.config/omarchy/themes/warm-glass"
[[ ! -e "$theme_dir" && ! -L "$theme_dir" ]] || {
  echo 'Warm Glass is already installed; stopping to preserve your setup.' >&2
  exit 1
}
omarchy theme install https://github.com/Ahmed-Sinkeat/omarchy-warm-glass-theme.git
