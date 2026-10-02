#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
REPO="DWR-debug/trading-agent-public"
RUNNER_VERSION="2.337.0"
DEVICE_MODEL="$(printenv ANDROID_PHONE_MODEL 2>/dev/null || printf UNKNOWN)"
SHORT_ID="$(printenv ANDROID_PHONE_ID 2>/dev/null || printf A1)"
RUNNER_NAME="$(printenv ANDROID_RUNNER_NAME 2>/dev/null || true)"
if [ -z "$RUNNER_NAME" ]; then RUNNER_NAME="ANDROID-SAMSUNG-$DEVICE_MODEL-$SHORT_ID"; fi
RUNNER_LABELS="$(printenv ANDROID_RUNNER_LABELS 2>/dev/null || true)"
if [ -z "$RUNNER_LABELS" ]; then RUNNER_LABELS="android-phone,samsung,linux,ARM64"; fi
command -v proot-distro >/dev/null 2>&1 || { echo "Install first: pkg install -y proot-distro"; exit 2; }
printf "GitHub runner registration token (input locally; not stored): "
read -rs TOKEN
printf "\n"
[ -n "$TOKEN" ] || { echo "Missing runner registration token"; exit 2; }
proot-distro login ubuntu -- env ANDROID_RUNNER_TOKEN="$TOKEN" ANDROID_RUNNER_NAME="$RUNNER_NAME" ANDROID_RUNNER_LABELS="$RUNNER_LABELS" ANDROID_RUNNER_VERSION="$RUNNER_VERSION" ANDROID_RUNNER_REPO="$REPO" bash -lc '
set -euo pipefail
apt-get update -qq
apt-get install -y -qq ca-certificates curl tar git python3
mkdir -p /opt/android-actions-runner
cd /opt/android-actions-runner
if [ ! -x ./run.sh ]; then
  curl -L --fail --silent --show-error --retry 5 --retry-all-errors --retry-delay 2 -o actions-runner.tar.gz "https://github.com/actions/runner/releases/download/v${ANDROID_RUNNER_VERSION}/actions-runner-linux-arm64-${ANDROID_RUNNER_VERSION}.tar.gz"
  tar -xzf actions-runner.tar.gz
fi
if [ -x ./bin/installdependencies.sh ]; then ./bin/installdependencies.sh; fi
./config.sh --url "https://github.com/${ANDROID_RUNNER_REPO}" --token "$ANDROID_RUNNER_TOKEN" --name "$ANDROID_RUNNER_NAME" --labels "$ANDROID_RUNNER_LABELS" --work "_work" --unattended --replace
'
echo "Android phone runner registered: $RUNNER_NAME"
