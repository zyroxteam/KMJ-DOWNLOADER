#!/data/data/com.termux/files/usr/bin/bash
# ============================================================
#  KMJ DOWNLOADER — One Click Setup for Termux
#  Made By KMJ TIPS CHANNEL
#  Usage: bash setup.sh
# ============================================================
set -e

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'
CYAN='\033[0;36m'; MAGENTA='\033[0;35m'; BOLD='\033[1m'; NC='\033[0m'

banner() {
  clear
  echo -e "${CYAN}${BOLD}"
  echo '██╗  ██╗███╗   ███╗     ██╗'
  echo '██║ ██╔╝████╗ ████║     ██║'
  echo '█████╔╝ ██╔████╔██║     ██║'
  echo '██╔═██╗ ██║╚██╔╝██║██   ██║'
  echo '██║  ██╗██║ ╚═╝ ██║╚█████╔╝'
  echo '╚═╝  ╚═╝╚═╝     ╚═╝ ╚════╝ '
  echo -e "${YELLOW}${BOLD}       D O W N L O A D E R${NC}"
  echo -e "${BOLD}    Made By KMJ TIPS CHANNEL${NC}"
  echo ""
}

step() { echo -e "${MAGENTA}${BOLD}[*]${NC} $1"; }
ok()   { echo -e "${GREEN}${BOLD}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}${BOLD}[!]${NC} $1"; }

banner
echo -e "${CYAN}${BOLD}=== KMJ DOWNLOADER One-Click Setup ===${NC}"
echo ""

# 1. Termux storage permission (for KMJ TIPS folder in Downloads)
step "Storage permission check..."
if [ ! -d "$HOME/storage/downloads" ]; then
  warn "Running termux-setup-storage (allow the popup)..."
  termux-setup-storage || true
  sleep 2
fi
ok "Storage ready"

# 2. Packages
step "Updating packages..."
pkg update -y >/dev/null 2>&1 || true
ok "Package list updated"

step "Installing python, ffmpeg, curl..."
pkg install -y python ffmpeg curl >/dev/null 2>&1
ok "python + ffmpeg + curl installed"

# 3. Python deps
step "Installing yt-dlp + rich (this may take a minute)..."
pip install -U yt-dlp rich >/dev/null 2>&1
ok "yt-dlp + rich installed"

# 4. KMJ TIPS download folder
step "Creating KMJ TIPS folder..."
FOLDER="$HOME/storage/downloads/KMJ TIPS"
if mkdir -p "$FOLDER" 2>/dev/null; then
  ok "Folder: $FOLDER"
else
  FOLDER="$HOME/KMJ TIPS"
  mkdir -p "$FOLDER"
  ok "Folder: $FOLDER"
fi

# 5. Install kmj command
step "Installing 'kmj' command..."
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
if [ -f "$SCRIPT_DIR/kmj.py" ]; then
  cp "$SCRIPT_DIR/kmj.py" "$PREFIX/bin/kmj"
  chmod +x "$PREFIX/bin/kmj"
  ok "'kmj' command installed"
else
  warn "kmj.py not found next to setup.sh — copy it manually to \$PREFIX/bin/kmj"
fi

# 6. Verify
step "Verifying..."
if command -v yt-dlp >/dev/null 2>&1; then
  ok "yt-dlp $(yt-dlp --version)"
else
  warn "yt-dlp not on PATH, but python module is present"
fi

echo ""
echo -e "${GREEN}${BOLD}============================================${NC}"
echo -e "${GREEN}${BOLD}  ✅ SETUP COMPLETE — KMJ DOWNLOADER READY${NC}"
echo -e "${GREEN}${BOLD}============================================${NC}"
echo ""
echo -e "  Run it with:  ${CYAN}${BOLD}kmj${NC}"
echo -e "  Videos save:  ${YELLOW}${BOLD}$FOLDER${NC}"
echo ""
echo -e "${BOLD}  Made By KMJ TIPS CHANNEL 💛${NC}"
echo ""
