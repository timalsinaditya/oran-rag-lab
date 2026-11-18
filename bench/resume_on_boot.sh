#!/usr/bin/env bash
# Called by `crontab @reboot`: restart the benchmark queue after a server reboot.
# Every step resumes from its checkpoint and finished steps are skipped, so a reboot costs ~2 minutes.
# Remove the crontab line when the work is done:  crontab -l | grep -v resume_on_boot.sh | crontab -
cd "$(dirname "$0")/.." || exit 1
LOG=logs/queue_official.log
mkdir -p logs
echo "[$(date +%H:%M)] boot detected, resume_on_boot.sh started" >> "$LOG"

[ -f logs/queue_official.done ] && { echo "[$(date +%H:%M)] queue already finished, nothing to do" >> "$LOG"; exit 0; }
pgrep -f "bash bench/queue_official.sh" >/dev/null && { echo "[$(date +%H:%M)] queue already running" >> "$LOG"; exit 0; }

for i in $(seq 1 60); do nvidia-smi >/dev/null 2>&1 && break; sleep 10; done    # wait up to 10 min for the GPU driver
nvidia-smi >/dev/null 2>&1 || { echo "[$(date +%H:%M)] GPU not available after 10 min, giving up" >> "$LOG"; exit 1; }

echo "[$(date +%H:%M)] restarting queue after reboot" >> "$LOG"
nohup setsid bash bench/queue_official.sh >> "$LOG" 2>&1 < /dev/null &
