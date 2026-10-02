#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/trading-agent-public"
LLAMA_LOG="$HOME/s10-llama-server.log"
BRIDGE_LOG="$HOME/s10-bridge.log"
MODEL="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"

command -v llama-server >/dev/null 2>&1 || {
  echo "Install first: pkg install -y llama-cpp"
  exit 2
}
command -v python >/dev/null 2>&1 || {
  echo "Install first: pkg install -y python"
  exit 2
}

termux-wake-lock >/dev/null 2>&1 || true

pkill -f "llama-server.*Qwen2.5-1.5B-Instruct" 2>/dev/null || true
pkill -f "s10_systemone_bridge.py" 2>/dev/null || true
sleep 1

nohup llama-server -hf "$MODEL" --host 127.0.0.1 --port 8080 --alias S10-Qwen2.5-1.5B -c 4096 -t 8 >"$LLAMA_LOG" 2>&1 &
echo $! > "$HOME/s10-llama-server.pid"

cd "$ROOT"
nohup python automation/s10_systemone_bridge.py >"$BRIDGE_LOG" 2>&1 &
echo $! > "$HOME/s10-bridge.pid"

mkdir -p "$HOME/.cache/s10-model"
proot-distro login ubuntu --user s10runner -- bash -lc '
  mkdir -p ~/.trading-agent
  cat > ~/.trading-agent/s10_interface.json <<EOF
{"schema_version":1,"enabled":true,"mode":"systemone_http","base_url":"http://127.0.0.1:8765","model":"S10-Qwen2.5-1.5B","protocol_path":"/v1/systemone","timeout_seconds":120}
EOF
'

echo "S10 local AI started."
echo "Health: curl -s http://127.0.0.1:8765/health"
