#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REPO="DWR-debug/trading-agent-public"
RUNNER_VERSION="2.337.0"
RUNNER_NAME="${S10_RUNNER_NAME:-S10-TERMUX}"
RUNNER_LABELS="s10-phone,linux,ARM64"

command -v proot-distro >/dev/null 2>&1 || { echo "Install first: pkg install -y proot-distro"; exit 2; }
printf "GitHub runner registration token (input locally; not stored): "
read -rs TOKEN
printf "\n"
[ -n "$TOKEN" ] || { echo "Missing runner registration token"; exit 2; }

proot-distro login ubuntu -- env S10_RUNNER_TOKEN="$TOKEN" S10_RUNNER_NAME="$RUNNER_NAME" S10_RUNNER_LABELS="$RUNNER_LABELS" S10_RUNNER_VERSION="$RUNNER_VERSION" S10_REPO="$REPO" bash -lc '
set -euo pipefail
apt-get update -qq
apt-get install -y -qq ca-certificates curl tar git python3
mkdir -p /opt/s10-actions-runner
cd /opt/s10-actions-runner
if [ ! -x ./run.sh ]; then
  curl -L --fail --silent --show-error --retry 5 --retry-all-errors --retry-delay 2 -o actions-runner.tar.gz "https://github.com/actions/runner/releases/download/v${S10_RUNNER_VERSION}/actions-runner-linux-arm64-${S10_RUNNER_VERSION}.tar.gz"
  tar -xzf actions-runner.tar.gz
fi
if [ -x ./bin/installdependencies.sh ]; then
  ./bin/installdependencies.sh
fi
./config.sh --url "https://github.com/${S10_REPO}" --token "$S10_RUNNER_TOKEN" --name "$S10_RUNNER_NAME" --labels "$S10_RUNNER_LABELS" --work "_work" --unattended --replace
'
echo "S10 phone runner registered: $RUNNER_NAME"
echo "Start: proot-distro login ubuntu -- bash -lc \"cd /opt/s10-actions-runner && ./run.sh\""
