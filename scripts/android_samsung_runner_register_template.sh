#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="DWR-debug/trading-agent-public"
RUNNER_VERSION="$(printenv ANDROID_RUNNER_VERSION 2>/dev/null || printf 2.337.0)"
DEVICE_MODEL="$(printenv ANDROID_PHONE_MODEL 2>/dev/null || printf UNKNOWN)"
SHORT_ID="$(printenv ANDROID_PHONE_ID 2>/dev/null || printf A1)"
RUNNER_NAME="$(printenv ANDROID_RUNNER_NAME 2>/dev/null || printf '')"
[ -n "$RUNNER_NAME" ] || RUNNER_NAME="ANDROID-SAMSUNG-$DEVICE_MODEL-$SHORT_ID"
RUNNER_LABELS="$(printenv ANDROID_RUNNER_LABELS 2>/dev/null || printf '')"
[ -n "$RUNNER_LABELS" ] || RUNNER_LABELS="android-phone,samsung,linux,ARM64"
RUNNER_USER="$(printenv ANDROID_RUNNER_USER 2>/dev/null || printf androidrunner)"
RUNNER_ROOT="$(printenv ANDROID_RUNNER_ROOT 2>/dev/null || printf /opt/android-actions-runner)"
ALLOW_REREGISTER="$(printenv ANDROID_ALLOW_REREGISTER 2>/dev/null || printf false)"

command -v proot-distro >/dev/null 2>&1 || { echo "Install first: pkg install -y proot-distro"; exit 2; }
printf "GitHub runner registration token (input locally; not stored): "
read -rs TOKEN
printf "\n"
[ -n "$TOKEN" ] || { echo "Missing runner registration token"; exit 2; }

proot-distro login ubuntu -- env \
  ANDROID_RUNNER_TOKEN="$TOKEN" \
  ANDROID_RUNNER_NAME="$RUNNER_NAME" \
  ANDROID_RUNNER_LABELS="$RUNNER_LABELS" \
  ANDROID_RUNNER_VERSION="$RUNNER_VERSION" \
  ANDROID_RUNNER_REPO="$REPO" \
  ANDROID_RUNNER_USER="$RUNNER_USER" \
  ANDROID_RUNNER_ROOT="$RUNNER_ROOT" \
  ANDROID_ALLOW_REREGISTER="$ALLOW_REREGISTER" bash -lc '
set -euo pipefail
apt-get update -qq
apt-get install -y -qq ca-certificates curl tar git python3 util-linux

if ! id -u "$ANDROID_RUNNER_USER" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$ANDROID_RUNNER_USER"
fi

mkdir -p "$ANDROID_RUNNER_ROOT"
cd "$ANDROID_RUNNER_ROOT"

if [ -f .runner ] && [ "$ANDROID_ALLOW_REREGISTER" != "true" ]; then
  echo "Android runner already registered; refusing silent re-registration."
  echo "Use the start template after reboot, or set ANDROID_ALLOW_REREGISTER=true explicitly."
  exit 0
fi

if [ ! -x ./run.sh ]; then
  curl -L --fail --silent --show-error --retry 5 --retry-all-errors --retry-delay 2 \
    -o actions-runner.tar.gz \
    "https://github.com/actions/runner/releases/download/v$ANDROID_RUNNER_VERSION/actions-runner-linux-arm64-$ANDROID_RUNNER_VERSION.tar.gz"
  tar -xzf actions-runner.tar.gz
fi

if [ -x ./bin/installdependencies.sh ]; then
  ./bin/installdependencies.sh
fi

chown -R "$ANDROID_RUNNER_USER:$ANDROID_RUNNER_USER" "$ANDROID_RUNNER_ROOT"

if [ "$ANDROID_ALLOW_REREGISTER" = "true" ] || [ ! -f .runner ]; then
  runuser -u "$ANDROID_RUNNER_USER" -- env \
    ANDROID_RUNNER_TOKEN="$ANDROID_RUNNER_TOKEN" \
    ANDROID_RUNNER_NAME="$ANDROID_RUNNER_NAME" \
    ANDROID_RUNNER_LABELS="$ANDROID_RUNNER_LABELS" \
    ANDROID_RUNNER_REPO="$ANDROID_RUNNER_REPO" \
    ANDROID_RUNNER_ROOT="$ANDROID_RUNNER_ROOT" \
    bash -lc '\''
      set -euo pipefail
      cd "$ANDROID_RUNNER_ROOT"
      ./config.sh --url "https://github.com/$ANDROID_RUNNER_REPO" \
        --token "$ANDROID_RUNNER_TOKEN" \
        --name "$ANDROID_RUNNER_NAME" \
        --labels "$ANDROID_RUNNER_LABELS" \
        --work "_work" \
        --unattended
    '\''
  chown -R "$ANDROID_RUNNER_USER:$ANDROID_RUNNER_USER" "$ANDROID_RUNNER_ROOT"
fi
'
echo "Android phone runner registered: $RUNNER_NAME"
echo "Start: proot-distro login ubuntu --user $RUNNER_USER -- bash -lc \"cd $RUNNER_ROOT && ./run.sh\""
