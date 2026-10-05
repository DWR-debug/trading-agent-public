#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

ROOT="$HOME/trading-agent-public"
LLAMA_LOG="$HOME/s10-llama-server.log"
BRIDGE_LOG="$HOME/s10-bridge.log"
MODEL="Qwen/Qwen2.5-1.5B-Instruct-GGUF:Q4_K_M"
LLAMA_URL="http://127.0.0.1:8080"
BRIDGE_URL="http://127.0.0.1:8765"
S10_UBUNTU_USER="${S10_UBUNTU_USER:-s10}"

command -v llama-server >/dev/null 2>&1 || {
  echo "Install first: pkg install -y llama-cpp"
  exit 2
}
command -v python >/dev/null 2>&1 || {
  echo "Install first: pkg install -y python"
  exit 2
}
command -v curl >/dev/null 2>&1 || {
  echo "Install first: pkg install -y curl"
  exit 2
}

termux-wake-lock >/dev/null 2>&1 || true

pkill -f "llama-server.*Qwen2.5-1.5B-Instruct" 2>/dev/null || true
pkill -f "s10_systemone_bridge.py" 2>/dev/null || true
sleep 1

nohup llama-server -hf "$MODEL" --host 127.0.0.1 --port 8080 --alias S10-Qwen2.5-1.5B -c 4096 -t 8 >"$LLAMA_LOG" 2>&1 &
echo $! > "$HOME/s10-llama-server.pid"

echo "Waiting for llama.cpp..."
for _ in $(seq 1 90); do
  if curl -fsS "$LLAMA_URL/health" >/dev/null 2>&1; then
    break
  fi
  sleep 2
done
curl -fsS "$LLAMA_URL/health" >/dev/null
echo "llama.cpp: OK"

cd "$ROOT"
nohup python automation/s10_systemone_bridge.py >"$BRIDGE_LOG" 2>&1 &
echo $! > "$HOME/s10-bridge.pid"

for _ in $(seq 1 30); do
  if curl -fsS "$BRIDGE_URL/health" >/dev/null 2>&1; then
    break
  fi
  sleep 1
done
curl -fsS "$BRIDGE_URL/health"
echo

mkdir -p "$HOME/.cache/s10-model"
proot-distro login ubuntu --user "$S10_UBUNTU_USER" -- bash -lc '
  mkdir -p ~/.trading-agent
  cat > ~/.trading-agent/s10_interface.json <<EOF
{"schema_version":1,"enabled":true,"mode":"systemone_http","base_url":"http://127.0.0.1:8765","model":"S10-Qwen2.5-1.5B","protocol_path":"/v1/systemone","timeout_seconds":120}
EOF
'

SMOKE='{"state":{"claim":"The local model health endpoint is operational.","evidence":"llama.cpp returned HTTP 200 with status ok.","domain":"bounded smoke test"},"questions":{"verdict":{"criteria":{"SUPPORTED":"The supplied evidence directly supports the claim.","REFUTED":"The supplied evidence contradicts the claim.","INSUFFICIENT":"The supplied evidence does not determine the claim."}}}}'

echo "S10 bridge smoke:"
curl -fsS -X POST "$BRIDGE_URL/v1/systemone"   -H 'Content-Type: application/json'   -d "$SMOKE"
echo
echo "S10 local AI: READY"
