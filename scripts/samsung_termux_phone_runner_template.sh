#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

# Reusable Samsung/Android Termux runner template.
# Never store a GitHub registration token in the repository.
REPO="${TRADING_AGENT_REPO:-DWR-debug/trading-agent-public}"
PHONE_RESOURCE_ID="${PHONE_RESOURCE_ID:-ANDROID-PHONE}"
PHONE_RUNNER_NAME="${PHONE_RUNNER_NAME:-${PHONE_RESOURCE_ID}-TERMUX}"
PHONE_RUNNER_LABEL="${PHONE_RUNNER_LABEL:-android-phone}"
PHONE_RUNNER_USER="${PHONE_RUNNER_USER:-s10}"
RUNNER_VERSION="${ACTIONS_RUNNER_VERSION:-2.337.0}"
RUNNER_DIR="${PHONE_RUNNER_DIR:-/opt/trading-agent-actions-runner}"
DOTNET_GC_HEAP_HARD_LIMIT="${DOTNET_GC_HEAP_HARD_LIMIT:-268435456}"
REPO_DIR="${PHONE_REPO_DIR:-$HOME/trading-agent-public}"

case "$(uname -m)" in
  aarch64|arm64) ;;
  *) echo "Unsupported phone architecture: $(uname -m)" >&2; exit 3 ;;
esac

command -v proot-distro >/dev/null 2>&1 || {
  echo "Missing proot-distro. Install with: pkg install -y proot-distro" >&2
  exit 2
}

usage() {
  echo "Usage: $0 prepare|runtime|register|start"
}

ensure_ubuntu() {
  if ! proot-distro list 2>/dev/null | grep -Eq '(^|[[:space:]])ubuntu([[:space:]]|$)'; then
    echo "Ubuntu userland not present; installing it now."
    proot-distro install ubuntu
  fi
}

prepare() {
  ensure_ubuntu
  proot-distro login ubuntu -- env \
    PHONE_RESOURCE_ID="$PHONE_RESOURCE_ID" \
    RUNNER_VERSION="$RUNNER_VERSION" \
    RUNNER_DIR="$RUNNER_DIR" \
    bash -lc '
      set -euo pipefail
      apt-get update -qq
      DEBIAN_FRONTEND=noninteractive apt-get install -y -qq ca-certificates curl git tar python3
      mkdir -p "$RUNNER_DIR"
      cd "$RUNNER_DIR"
      if [ ! -x ./run.sh ]; then
        curl -L --fail --silent --show-error --retry 5 --retry-all-errors --retry-delay 2 \
          -o actions-runner.tar.gz \
          "https://github.com/actions/runner/releases/download/v${RUNNER_VERSION}/actions-runner-linux-arm64-${RUNNER_VERSION}.tar.gz"
        tar -xzf actions-runner.tar.gz
      fi
      ./bin/Runner.Listener --version
      echo "PHONE_RESOURCE_ID=$PHONE_RESOURCE_ID"
      echo "Samsung/Android Termux runner prepared."
    '
}

runtime() {
  ensure_ubuntu
  proot-distro login ubuntu -- env \
    REPO="$REPO" \
    REPO_DIR="$REPO_DIR" \
    PHONE_RESOURCE_ID="$PHONE_RESOURCE_ID" \
    bash -lc '
      set -euo pipefail
      export DEBIAN_FRONTEND=noninteractive
      apt-get update -qq
      apt-get install -y -qq ca-certificates curl git python3
      mkdir -p "$(dirname "$REPO_DIR")" "$HOME/.trading-agent" "$HOME/.cache/trading-agent/android-phone/$PHONE_RESOURCE_ID/runs"
      if [ ! -d "$REPO_DIR/.git" ]; then
        git clone --depth=1 "https://github.com/${REPO}.git" "$REPO_DIR"
      else
        git -C "$REPO_DIR" fetch --depth=1 origin master
        git -C "$REPO_DIR" checkout -q master
        git -C "$REPO_DIR" reset --hard origin/master
      fi
      cd "$REPO_DIR"
      python3 -m automation.s10_local_stack \
        --repo-root "$REPO_DIR" \
        --descriptor "$HOME/.trading-agent/phone_interface.json" \
        --work-root "$HOME/.cache/trading-agent/android-phone/$PHONE_RESOURCE_ID/runs"
      echo "Bounded local runtime prepared for $PHONE_RESOURCE_ID."
    '
}

register() {
  ensure_ubuntu
  printf "GitHub runner registration token (input locally; not stored): "
  read -rs TOKEN
  printf "\n"
  [ -n "$TOKEN" ] || { echo "Missing runner registration token" >&2; exit 2; }

  proot-distro login ubuntu -- env \
    PHONE_RUNNER_TOKEN="$TOKEN" \
    PHONE_RUNNER_NAME="$PHONE_RUNNER_NAME" \
    PHONE_RUNNER_LABEL="$PHONE_RUNNER_LABEL" \
    RUNNER_VERSION="$RUNNER_VERSION" \
    RUNNER_DIR="$RUNNER_DIR" \
    TRADING_AGENT_REPO="$REPO" \
    bash -lc '
      set -euo pipefail
      cd "$RUNNER_DIR"
      if [ -x ./bin/installdependencies.sh ]; then
        ./bin/installdependencies.sh
      fi
      ./config.sh \
        --url "https://github.com/${TRADING_AGENT_REPO}" \
        --token "$PHONE_RUNNER_TOKEN" \
        --name "$PHONE_RUNNER_NAME" \
        --labels "${PHONE_RUNNER_LABEL},android-phone,linux,ARM64" \
        --work "_work" \
        --unattended \
        --replace
    '
  unset TOKEN
  echo "Registered $PHONE_RUNNER_NAME ($PHONE_RUNNER_LABEL)."
}

start() {
  ensure_ubuntu
  if command -v termux-wake-lock >/dev/null 2>&1; then
    termux-wake-lock || true
  fi
  echo "Starting $PHONE_RUNNER_NAME; keep Termux and the phone powered."
  exec proot-distro login ubuntu --user "$PHONE_RUNNER_USER" -- env \
    DOTNET_GCHeapHardLimit="$DOTNET_GC_HEAP_HARD_LIMIT" \
    COMPlus_GCHeapHardLimit="$DOTNET_GC_HEAP_HARD_LIMIT" \
    DOTNET_gcServer=0 \
    COMPlus_gcServer=0 \
    bash -lc "unset DOTNET_GCHeapHardLimitPercent COMPlus_GCHeapHardLimitPercent; cd '$RUNNER_DIR' && exec ./run.sh"
}

case "${1:-}" in
  prepare) prepare ;;
  runtime) runtime ;;
  register) register ;;
  start) start ;;
  *) usage; exit 2 ;;
esac
