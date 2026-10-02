#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
command -v proot-distro >/dev/null 2>&1 || { echo "Install first: pkg install -y proot-distro"; exit 2; }
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock || true
fi
echo "S10 phone runner starting. Keep this Termux session alive and the phone powered."
exec proot-distro login ubuntu -- bash -lc "cd /opt/s10-actions-runner && ./run.sh"
