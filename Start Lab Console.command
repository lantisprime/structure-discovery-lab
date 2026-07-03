#!/bin/bash
# Structure Discovery Lab — console launcher (double-click me on macOS).
# Starts the local web console and opens it in your browser.
#   ./Start\ Lab\ Console.command          -> http://localhost:8787
#   ./Start\ Lab\ Console.command --lan    -> also reachable from your phone
#                                             on the same Wi-Fi
cd "$(dirname "$0")"

PORT=8787
PY=$(command -v python3 || command -v python)
if [ -z "$PY" ]; then
  echo "python3 not found — install Python 3 first."; read -r; exit 1
fi

# Always run the CURRENT code: if any server (possibly an outdated one) is
# holding the port, stop it first. This makes double-clicking this file a
# true restart.
OLD_PIDS=$(lsof -ti tcp:$PORT 2>/dev/null)
if [ -n "$OLD_PIDS" ]; then
  echo "Stopping the previous console (pid $OLD_PIDS)…"
  kill $OLD_PIDS 2>/dev/null
  sleep 1
  kill -9 $(lsof -ti tcp:$PORT 2>/dev/null) 2>/dev/null
  sleep 0.5
fi

echo "Starting Structure Discovery Lab console…"
"$PY" webapp/server.py $PORT "$@" &
SERVER_PID=$!
trap 'kill $SERVER_PID 2>/dev/null' EXIT INT TERM

# wait for it to answer, then open the browser
for _ in $(seq 1 20); do
  if curl -s -o /dev/null --max-time 1 "http://localhost:$PORT/api/state"; then
    (command -v open >/dev/null && open "http://localhost:$PORT") || \
    (command -v xdg-open >/dev/null && xdg-open "http://localhost:$PORT") || \
    echo "Open http://localhost:$PORT in your browser."
    break
  fi
  sleep 0.5
done

echo
echo "Console running (pid $SERVER_PID). Press Ctrl-C or close this window to stop."
wait $SERVER_PID
