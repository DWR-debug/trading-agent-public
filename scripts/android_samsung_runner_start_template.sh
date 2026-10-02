#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
termux-wake-lock 2>/dev/null || true
proot-distro login ubuntu -- bash -lc 'cd /opt/android-actions-runner && ./run.sh'
