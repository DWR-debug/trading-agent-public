#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
RUNNER_USER="${ANDROID_RUNNER_USER:-androidrunner}"
termux-wake-lock 2>/dev/null || true
echo "Android Samsung runner starting as $RUNNER_USER."

proot-distro login ubuntu -- bash -lc "
set -euo pipefail
if ! id -u '$RUNNER_USER' >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash '$RUNNER_USER'
fi
chown -R '$RUNNER_USER:$RUNNER_USER' /opt/android-actions-runner
"
exec proot-distro login ubuntu --user "$RUNNER_USER" -- bash -lc 'cd /opt/android-actions-runner && ./run.sh'
