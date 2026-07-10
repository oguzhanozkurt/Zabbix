#!/usr/bin/env bash
set -euo pipefail
TARGET_DIR=${1:-/etc/zabbix/zabbix_agent2.d/custom_scripts}
mkdir -p "$TARGET_DIR"
cp "$(dirname "$0")"/custom_queries/*.sql "$TARGET_DIR"/
chown -R zabbix:zabbix "$TARGET_DIR"
chmod 750 "$TARGET_DIR"
chmod 640 "$TARGET_DIR"/*.sql
systemctl restart zabbix-agent2
echo "Installed PostgreSQL custom queries to $TARGET_DIR and restarted zabbix-agent2."
