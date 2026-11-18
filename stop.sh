#!/usr/bin/env bash
# Stop the servers started by ./start.sh
cd "$(dirname "$0")" || exit 1

if [ ! -f .run/pids ]; then
  echo "No running SearNXG instance found."
  exit 0
fi

read -r API_PID UI_PID < .run/pids
for pid in "$API_PID" "$UI_PID"; do
  if [ -n "$pid" ] && kill -0 "$pid" 2>/dev/null; then
    kill -- "-$pid" 2>/dev/null || kill "$pid" 2>/dev/null || true
    echo "Stopped $pid"
  fi
done
rm -f .run/pids
echo "SearNXG stopped."
