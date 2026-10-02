#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="DWR-debug/trading-agent-public"
RUNNER_VERSION="2.337.0"
RUNNER_DIR="/opt/s10-actions-runner"

command -v proot-distro >/dev/null 2>&1 || {
  echo "Install first: pkg install -y proot-distro"
  exit 2
}

proot-distro login ubuntu -- bash -lc '
set -euo pipefail
apt-get update -qq
apt-get install -y -qq ca-certificates curl git tar python3
mkdir -p "'"$RUNNER_DIR"'"
cd "'"$RUNNER_DIR"'"
if [ ! -x ./run.sh ]; then
  curl -L --fail --silent --show-error --retry 5 --retry-all-errors --retry-delay 2     -o actions-runner.tar.gz     "https://github.com/actions/runner/releases/download/v'"$RUNNER_VERSION"'/actions-runner-linux-arm64-'"$RUNNER_VERSION"'.tar.gz"
  tar -xzf actions-runner.tar.gz
fi
./bin/Runner.Listener --version
echo "S10 runner runtime prepared."
'

echo
echo "Next: register this runner for $REPO with label s10-phone."
echo "Keep the registration token off chat/repo history."
