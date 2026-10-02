#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

RUNNER_USER="$(printenv ANDROID_RUNNER_USER 2>/dev/null || printf androidrunner)"
RUNNER_ROOT="$(printenv ANDROID_RUNNER_ROOT 2>/dev/null || printf /opt/android-actions-runner)"
GC_LIMIT="$(printenv ANDROID_DOTNET_GC_HEAP_HARD_LIMIT 2>/dev/null || printf 40000000)"
MIN_MEM_MB="$(printenv ANDROID_MIN_MEM_AVAILABLE_MB 2>/dev/null || printf 1536)"
MIN_STORAGE_MB="$(printenv ANDROID_MIN_FREE_STORAGE_MB 2>/dev/null || printf 4096)"

command -v proot-distro >/dev/null 2>&1 || { echo "Install first: pkg install -y proot-distro"; exit 2; }
termux-wake-lock 2>/dev/null || true

proot-distro login ubuntu -- env \
  ANDROID_RUNNER_USER="$RUNNER_USER" \
  ANDROID_RUNNER_ROOT="$RUNNER_ROOT" \
  ANDROID_MIN_MEM_MB="$MIN_MEM_MB" \
  ANDROID_MIN_STORAGE_MB="$MIN_STORAGE_MB" bash -lc '
set -euo pipefail
if ! id -u "$ANDROID_RUNNER_USER" >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash "$ANDROID_RUNNER_USER"
fi
if [ ! -x "$ANDROID_RUNNER_ROOT/run.sh" ] || [ ! -f "$ANDROID_RUNNER_ROOT/.runner" ]; then
  echo "Existing Android runner registration not found at $ANDROID_RUNNER_ROOT"
  exit 3
fi
chown -R "$ANDROID_RUNNER_USER:$ANDROID_RUNNER_USER" "$ANDROID_RUNNER_ROOT"

arch="$(uname -m)"
case "$arch" in
  aarch64|arm64) ;;
  *) echo "Unsupported architecture: $arch"; exit 4 ;;
esac

[ "$(id -u "$ANDROID_RUNNER_USER")" != "0" ] || { echo "Runner user must be non-root"; exit 5; }

mem_kb="$(awk "/MemAvailable:/ {print \$2; exit}" /proc/meminfo)"
mem_mb=$((mem_kb / 1024))
[ "$mem_mb" -ge "$ANDROID_MIN_MEM_MB" ] || {
  echo "Insufficient available memory: $mem_mb MiB < $ANDROID_MIN_MEM_MB MiB"
  exit 6
}

free_mb="$(df -Pm "$ANDROID_RUNNER_ROOT" | awk "NR==2 {print \$4; exit}")"
[ "$free_mb" -ge "$ANDROID_MIN_STORAGE_MB" ] || {
  echo "Insufficient free storage: $free_mb MiB < $ANDROID_MIN_STORAGE_MB MiB"
  exit 7
}

echo "ANDROID_PREFLIGHT=PASS arch=$arch mem_available_mib=$mem_mb free_storage_mib=$free_mb runner_user=$ANDROID_RUNNER_USER"
'

echo "Android Samsung runner starting as $RUNNER_USER."
exec proot-distro login ubuntu --user "$RUNNER_USER" -- env \
  DOTNET_GCHeapHardLimit="$GC_LIMIT" \
  bash -lc "cd '$RUNNER_ROOT' && ./run.sh"
