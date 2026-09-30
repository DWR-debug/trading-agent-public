#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail

REPO="DWR-debug/trading-agent-public"
EDGE_BRANCH="edge-control"
BASE="https://raw.githubusercontent.com/$REPO/master"
ROOT="$HOME/.trading-agent-edge"

printf '\nTrading Agent Mobile Edge — Einrichtung\n\n'
printf 'Knoten-ID [edge01/edge02]: '
read -r NODE_ID
case "$NODE_ID" in
  edge01|edge02) ;;
  *) echo "Bitte edge01 oder edge02 verwenden."; exit 2 ;;
esac

printf 'Dediziertes GitHub Fine-grained Token (wird nicht angezeigt): '
read -r -s TOKEN
printf '\n'

pkg update -y
pkg install -y python git curl

mkdir -p "$ROOT" "$HOME/.termux/boot"
chmod 700 "$ROOT" "$HOME/.termux" "$HOME/.termux/boot"

curl -fsSL "$BASE/scripts/mobile_edge/edge_worker.py" -o "$ROOT/edge_worker.py"
chmod 700 "$ROOT/edge_worker.py"

cat > "$ROOT/config.env" <<EOF
export EDGE_NODE_ID="$NODE_ID"
export TRADING_AGENT_REPO="$REPO"
export TRADING_AGENT_EDGE_BRANCH="$EDGE_BRANCH"
export TRADING_AGENT_GITHUB_TOKEN="$TOKEN"
export EDGE_ROOT="$ROOT"
export EDGE_POLL_SECONDS="900"
export EDGE_HEARTBEAT_SECONDS="21600"
EOF
unset TOKEN
chmod 600 "$ROOT/config.env"

cat > "$HOME/.termux/boot/trading-agent-edge" <<'EOF'
#!/data/data/com.termux/files/usr/bin/bash
set -euo pipefail
ROOT="$HOME/.trading-agent-edge"
[ -f "$ROOT/config.env" ] || exit 1
. "$ROOT/config.env"
command -v termux-wake-lock >/dev/null 2>&1 && termux-wake-lock || true
exec python "$ROOT/edge_worker.py" >> "$ROOT/edge.log" 2>&1
EOF
chmod 700 "$HOME/.termux/boot/trading-agent-edge"

. "$ROOT/config.env"
EDGE_ONCE=1 python "$ROOT/edge_worker.py"

echo
echo "Fertig: $NODE_ID"
echo "Boot-Skript: $HOME/.termux/boot/trading-agent-edge"
echo "Log:         $ROOT/edge.log"
echo "Nächster Schritt: Termux:Boot einmal öffnen und danach das Telefon am Strom/WLAN lassen."
echo "Wichtig: Für dauerhaften Betrieb Termux (und Termux:Boot/Termux:API, falls installiert) von Akkuoptimierung ausnehmen."
