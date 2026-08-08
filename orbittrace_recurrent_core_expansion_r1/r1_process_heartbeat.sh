#!/usr/bin/env bash
set -euo pipefail
pid="${1:?usage: r1_process_heartbeat.sh PID [SECONDS]}"
interval="${2:-60}"
start="$(date +%s)"
while kill -0 "$pid" 2>/dev/null; do
  now="$(date +%s)"
  elapsed=$((now-start))
  if [[ -r "/proc/$pid/stat" && -r "/proc/$pid/status" ]]; then
    read -r utime stime < <(awk '{print $14, $15}' "/proc/$pid/stat")
    rss_kb="$(awk '/^VmRSS:/ {print $2}' "/proc/$pid/status")"
    threads="$(awk '/^Threads:/ {print $2}' "/proc/$pid/status")"
    echo "R1_HEARTBEAT elapsed_s=$elapsed pid=$pid cpu_ticks=$((utime+stime)) rss_kb=${rss_kb:-NA} threads=${threads:-NA} at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  else
    echo "R1_HEARTBEAT elapsed_s=$elapsed pid=$pid proc_status_unavailable at=$(date -u +%Y-%m-%dT%H:%M:%SZ)"
  fi
  sleep "$interval"
done
wait "$pid" 2>/dev/null || true
