#!/bin/bash
set -euo pipefail

if ! xcode-select -p >/dev/null 2>&1; then
  xcode-select --install
  echo 'Finish installing Command Line Tools, then run this script again.'
  exit 1
fi
if ! command -v brew >/dev/null; then
  /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
  if [[ -x /opt/homebrew/bin/brew ]]; then
    eval "$(/opt/homebrew/bin/brew shellenv)"
  else
    eval "$(/usr/local/bin/brew shellenv)"
  fi
fi
SOURCE_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
if [[ -f "$SOURCE_DIR/settings/manifest.json" ]]; then
  TRANSFER_DIR="$SOURCE_DIR"
else
  TRANSFER_DIR="$HOME/mac-transfer"
  if [[ -d "$TRANSFER_DIR/.git" ]]; then
    git -C "$TRANSFER_DIR" pull --ff-only
  else
    git clone https://github.com/Zhuofeng-Li/mac-transfer.git "$TRANSFER_DIR"
  fi
fi
brew bundle install --file="$TRANSFER_DIR/Brewfile"
bash "$TRANSFER_DIR/cursor/install-extensions.sh"
echo 'Packages installed. Start Alfred once, then quit it.'
echo 'Install Input Source Pro and your input methods; quit apps before restoring.'
echo "Restore settings: python3 \"$TRANSFER_DIR/settings/restore.py\""
echo 'The restore command backs up existing settings before changing them.'
