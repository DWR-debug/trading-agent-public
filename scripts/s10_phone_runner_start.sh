#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
command -v proot-distro >/dev/null 2>&1 || { echo "Install first: pkg install -y proot-distro"; exit 2; }
if command -v termux-wake-lock >/dev/null 2>&1; then
  termux-wake-lock || true
fi
echo "S10 phone runner starting. Keep this Termux session alive and the phone powered."

# GitHub's runner refuses interactive execution as root. The historical registration
# lives at /opt/s10-actions-runner, so repair ownership once and run the existing
# registered identity as an unprivileged Ubuntu user. This does not re-register it.
#
# CoreCLR on ARM64 Ubuntu under Termux/proot can fail during GC heap initialization
# because it attempts an excessively large virtual-memory reservation. A bounded
# 1-GiB GC heap limit is applied only to the runner process; S10's Python/llama.cpp
# workload is not configured through this variable.
proot-distro login ubuntu -- bash -lc '
set -euo pipefail
if ! id -u s10runner >/dev/null 2>&1; then
  useradd --create-home --shell /bin/bash s10runner
fi
chown -R s10runner:s10runner /opt/s10-actions-runner
'
exec proot-distro login ubuntu --user s10runner -- bash -lc 'cd /opt/s10-actions-runner && DOTNET_GCHeapHardLimit=40000000 ./run.sh'
