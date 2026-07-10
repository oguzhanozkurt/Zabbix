# PostgreSQL HA Monitoring Templates for Zabbix 7.0

Zabbix 7.0 templates and PostgreSQL Agent 2 custom queries for monitoring PostgreSQL high-availability environments, including primary/standby replication, cascading replicas, standby receivers, replication slots, WAL growth, and data filesystem utilization.

The project is intentionally generic. It does not include environment-specific hostnames, IP addresses, customer names, passwords, or organization-specific configuration.

## Contents

```text
.
├── zabbix_pg_ha_monitoring_templates_7.0.yaml
├── custom_queries/
│   ├── zbx_pg_replication_clients.sql
│   ├── zbx_pg_replication_slots.sql
│   ├── zbx_pg_standby_receiver.sql
│   └── zbx_pg_wal_settings.sql
├── examples/
│   └── postgresql_custom.conf
├── install_custom_queries.sh
├── LICENSE
└── README.md
```

## Templates

### Template PostgreSQL Replication Source

Use this template on PostgreSQL nodes that send WAL to downstream replicas.

Typical targets:

- Primary nodes
- Standby leaders
- Cascading standby nodes that also stream to another replica

Main coverage:

- `pg_stat_replication`
- `pg_replication_slots`
- Replication client state
- Replication lag breakdown
- Slot activity
- Slot retained WAL
- Slot `wal_status`
- Temporary or long-running basebackup slot visibility

### Template PostgreSQL Standby Receiver

Use this template on PostgreSQL nodes that receive WAL from an upstream server.

Typical targets:

- Synchronous standbys
- Asynchronous standbys
- Standby leaders
- Cascading replicas
- Leaf replicas

Main coverage:

- `pg_is_in_recovery()`
- `pg_stat_wal_receiver`
- WAL receiver status
- Upstream sender host and port
- Replication slot name used by the receiver
- Receive/replay gap
- Replay delay
- Seconds since the last WAL receiver message

Do not assign this template to a writable primary node unless you intentionally want to monitor that it should stay in recovery mode. A primary does not have a WAL receiver process.

### Template PostgreSQL WAL and Disk

Use this template on all PostgreSQL database nodes.

Main coverage:

- `pg_wal` directory size
- PostgreSQL data filesystem used percent
- PostgreSQL data filesystem free/total bytes
- `wal_keep_size`
- `min_wal_size`
- `max_wal_size`
- `max_slot_wal_keep_size`
- Configuration drift detection for expected `wal_keep_size`

## Recommended template assignment

| Node role | Assign templates |
|---|---|
| Writable primary | `Template PostgreSQL Replication Source` + `Template PostgreSQL WAL and Disk` |
| Standby that does not stream to another node | `Template PostgreSQL Standby Receiver` + `Template PostgreSQL WAL and Disk` |
| Standby leader / cascading standby | `Template PostgreSQL Replication Source` + `Template PostgreSQL Standby Receiver` + `Template PostgreSQL WAL and Disk` |
| Leaf replica | `Template PostgreSQL Standby Receiver` + `Template PostgreSQL WAL and Disk` |

## Requirements

- Zabbix Server or Zabbix Proxy 7.0.
- Zabbix Agent 2 installed on PostgreSQL hosts.
- Zabbix Agent 2 PostgreSQL plugin available.
- PostgreSQL monitoring user with access to PostgreSQL statistics views.
- Custom query SQL files deployed on each monitored PostgreSQL host.
- Local or network PostgreSQL access from the Agent 2 process.

The SQL queries are designed for modern PostgreSQL releases that expose `pg_stat_replication`, `pg_stat_wal_receiver`, and `pg_replication_slots` WAL status fields. The package was prepared for PostgreSQL HA monitoring use cases and should be tested in a non-production Zabbix environment before rollout.

## PostgreSQL monitoring user

Create the monitoring user on the writable primary. In a physical replication setup, the role will normally replicate to standby nodes.

```sql
CREATE USER zabbix WITH PASSWORD 'CHANGE_ME';
GRANT pg_monitor TO zabbix;
GRANT pg_read_all_stats TO zabbix;
```

If the user already exists:

```sql
GRANT pg_monitor TO zabbix;
GRANT pg_read_all_stats TO zabbix;
```

For local TCP connections, ensure `pg_hba.conf` or your HA manager's PostgreSQL access configuration allows the user to connect, for example:

```text
host    all     zabbix      127.0.0.1/32      scram-sha-256
host    all     zabbix      ::1/128           scram-sha-256
```

Reload PostgreSQL after changing access rules.

```bash
psql -d postgres -c "SELECT pg_reload_conf();"
```

## Install custom query files

Copy all SQL files to the Zabbix Agent 2 PostgreSQL custom query directory on every monitored database host.

Default target path used by this package:

```text
/etc/zabbix/zabbix_agent2.d/custom_scripts
```

Manual installation:

```bash
mkdir -p /etc/zabbix/zabbix_agent2.d/custom_scripts
cp custom_queries/*.sql /etc/zabbix/zabbix_agent2.d/custom_scripts/
chown -R zabbix:zabbix /etc/zabbix/zabbix_agent2.d/custom_scripts
chmod 750 /etc/zabbix/zabbix_agent2.d/custom_scripts
chmod 640 /etc/zabbix/zabbix_agent2.d/custom_scripts/*.sql
```

Or use the helper script:

```bash
chmod +x install_custom_queries.sh
./install_custom_queries.sh /etc/zabbix/zabbix_agent2.d/custom_scripts
```

The helper script copies the SQL files, fixes ownership and permissions, and restarts `zabbix-agent2`.

## Agent 2 PostgreSQL custom query configuration

Create or update this file:

```text
/etc/zabbix/zabbix_agent2.d/postgresql_custom.conf
```

Recommended content:

```ini
Plugins.PostgreSQL.CustomQueriesEnabled=true
Plugins.PostgreSQL.CustomQueriesPath=/etc/zabbix/zabbix_agent2.d/custom_scripts
Plugins.PostgreSQL.Default.Database=postgres
```

Restart Agent 2:

```bash
systemctl restart zabbix-agent2
systemctl status zabbix-agent2 --no-pager
```

Check Agent 2 logs if needed:

```bash
journalctl -u zabbix-agent2 -n 100 --no-pager
```

## Import the Zabbix template

In the Zabbix frontend:

```text
Data collection → Templates → Import
```

Import this file:

```text
zabbix_pg_ha_monitoring_templates_7.0.yaml
```

When updating an existing import, enable update options for existing templates, items, discovery rules, triggers, and macros.

## Required host macros

Set these macros on each monitored PostgreSQL host.

| Macro | Example value | Description |
|---|---:|---|
| `{$PG.CONN.URI}` | `tcp://127.0.0.1:5432` | PostgreSQL connection URI used by Agent 2. |
| `{$PG.CONN.USER}` | `zabbix` | PostgreSQL monitoring user. |
| `{$PG.CONN.PASSWORD}` | `CHANGE_ME` | PostgreSQL monitoring user password. Store as a secret macro where possible. |
| `{$PG.CONN.DB}` | `postgres` | Database used for monitoring queries. |
| `{$PG.DATA_DIR}` | `/var/lib/pgsql/17/data` | PostgreSQL data directory path. |
| `{$PG.FS.MOUNT}` | `/var/lib/pgsql` | Filesystem mount path for capacity checks. |
| `{$PG.WAL_KEEP_SIZE.EXPECTED}` | `34359738368` | Expected `wal_keep_size` in bytes. Default example is 32 GiB. |

For systems that use a different data path, adjust `{$PG.DATA_DIR}` and `{$PG.FS.MOUNT}` accordingly.

## Default threshold macros

### Replication lag

| Macro | Default | Meaning |
|---|---:|---|
| `{$PG.REPL.LAG.WARN}` | `5368709120` | Replication byte lag warning threshold, 5 GiB. |
| `{$PG.REPL.LAG.HIGH}` | `21474836480` | Replication byte lag high threshold, 20 GiB. |
| `{$PG.REPL.LAG.DISASTER}` | `53687091200` | Replication byte lag disaster threshold, 50 GiB. |
| `{$PG.REPL.TIME.WARN}` | `900` | Replication time lag warning threshold, seconds. |
| `{$PG.REPL.TIME.HIGH}` | `1800` | Replication time lag high threshold, seconds. |

### Replication slots

| Macro | Default | Meaning |
|---|---:|---|
| `{$PG.SLOT.RETAINED.WARN}` | `10737418240` | Slot retained WAL warning threshold, 10 GiB. |
| `{$PG.SLOT.RETAINED.HIGH}` | `32212254720` | Slot retained WAL high threshold, 30 GiB. |
| `{$PG.SLOT.RETAINED.DISASTER}` | `85899345920` | Slot retained WAL disaster threshold, 80 GiB. |
| `{$PG.SLOT.INACTIVE.TIME}` | `5m` | Duration before an inactive slot triggers. |

### WAL and filesystem

| Macro | Default | Meaning |
|---|---:|---|
| `{$PG.WAL.SIZE.WARN}` | `68719476736` | `pg_wal` size warning threshold, 64 GiB. |
| `{$PG.WAL.SIZE.HIGH}` | `137438953472` | `pg_wal` size high threshold, 128 GiB. |
| `{$PG.WAL.SIZE.DISASTER}` | `214748364800` | `pg_wal` size disaster threshold, 200 GiB. |
| `{$PG.FS.PUSED.WARN}` | `80` | Data filesystem used percent warning threshold. |
| `{$PG.FS.PUSED.HIGH}` | `90` | Data filesystem used percent high threshold. |
| `{$PG.FS.PUSED.DISASTER}` | `95` | Data filesystem used percent disaster threshold. |

### Standby receiver

| Macro | Default | Meaning |
|---|---:|---|
| `{$PG.WAL.RECEIVER.MSG.MAX}` | `300` | Maximum seconds since last WAL receiver message. |
| `{$PG.STANDBY.GAP.HIGH}` | `5368709120` | Standby receive/replay gap high threshold, 5 GiB. |
| `{$PG.STANDBY.REPLAY_DELAY.HIGH}` | `1800` | Standby replay delay high threshold, seconds. |

## Manual Agent 2 tests

Run these commands on a monitored PostgreSQL host after copying SQL files and restarting Agent 2.

Replace `CHANGE_ME` with the monitoring user's password.

### WAL settings

```bash
zabbix_agent2 -t 'pgsql.custom.query[tcp://127.0.0.1:5432,zabbix,CHANGE_ME,postgres,zbx_pg_wal_settings]'
```

### Replication slots

Use on nodes with `Template PostgreSQL Replication Source`.

```bash
zabbix_agent2 -t 'pgsql.custom.query[tcp://127.0.0.1:5432,zabbix,CHANGE_ME,postgres,zbx_pg_replication_slots]'
```

### Replication clients

Use on nodes with `Template PostgreSQL Replication Source`.

```bash
zabbix_agent2 -t 'pgsql.custom.query[tcp://127.0.0.1:5432,zabbix,CHANGE_ME,postgres,zbx_pg_replication_clients]'
```

### Standby receiver

Use on nodes with `Template PostgreSQL Standby Receiver`.

```bash
zabbix_agent2 -t 'pgsql.custom.query[tcp://127.0.0.1:5432,zabbix,CHANGE_ME,postgres,zbx_pg_standby_receiver]'
```

Expected result: each command should return a JSON array or JSON object-like value without plugin errors.

## Main items and discoveries

### Replication Source

Master items:

- `PostgreSQL replication slots raw`
- `PostgreSQL replication clients raw`

Discovery rules:

- `PostgreSQL replication slots discovery`
- `PostgreSQL replication clients discovery`

Important discovered metrics:

- Slot active status
- Slot retained WAL bytes
- Slot WAL status
- Slot safe WAL size
- Replication client state
- Replication client sync state
- Current-to-sent lag
- Sent-to-write lag
- Write-to-flush lag
- Flush-to-replay lag
- Total replay lag
- Time-based replay lag

### Standby Receiver

Important metrics:

- In recovery
- WAL receiver status
- Sender host
- Slot name
- Seconds since last message
- Receive/replay gap
- Replay delay

### WAL and Disk

Important metrics:

- `pg_wal` directory size
- Data filesystem used percent
- Data filesystem free/total bytes
- `wal_keep_size`
- `min_wal_size`
- `max_wal_size`
- `max_slot_wal_keep_size`

## Triggers

### Replication Source triggers

- Slot retained WAL is high or critical.
- Slot is inactive for longer than the configured threshold.
- Slot `wal_status` is `extended`.
- Slot `wal_status` is `lost`.
- Replication client state is not healthy.
- Replication client total replay lag is high or critical.
- Primary or upstream source cannot send WAL fast enough.
- Time-based replay lag is high.

### Standby Receiver triggers

- Standby node is not in recovery mode.
- WAL receiver is not streaming.
- No recent WAL receiver message.
- Receive/replay gap is high.
- Replay delay is high.

### WAL and Disk triggers

- `pg_wal` directory size is high or critical.
- Data filesystem usage is high or critical.
- `wal_keep_size` differs from the expected macro value.
- `max_slot_wal_keep_size` is unlimited.

## Notes about `max_slot_wal_keep_size`

The template reports `max_slot_wal_keep_size = -1` as an unlimited setting. Unlimited slot retention is operationally risky in HA environments because a broken or delayed replication slot can retain WAL until the filesystem fills.

If your operational policy intentionally keeps this value unlimited, adjust or disable the related trigger.

## Troubleshooting

### `Fifth parameter "QueryName" is required: Too few parameters`

The Agent 2 PostgreSQL plugin expects the database parameter before the query name.

Correct format:

```text
pgsql.custom.query[ConnString,User,Password,Database,QueryName]
```

Template keys use:

```text
pgsql.custom.query[{$PG.CONN.URI},{$PG.CONN.USER},{$PG.CONN.PASSWORD},{$PG.CONN.DB},zbx_pg_wal_settings]
```

### `query zbx_pg_... not found`

Check that SQL files exist in the configured custom query path.

```bash
ls -lh /etc/zabbix/zabbix_agent2.d/custom_scripts
grep -R "CustomQueriesPath" /etc/zabbix/zabbix_agent2.d/
journalctl -u zabbix-agent2 -n 100 --no-pager
```

### `password authentication failed`

Verify the host macros and test with `psql`.

```bash
psql -h 127.0.0.1 -p 5432 -U zabbix -d postgres -c "SELECT 1;"
```

### `no pg_hba.conf entry`

Allow the monitoring user to connect from the Agent 2 host, then reload PostgreSQL.

### Replication fields show empty, unknown, or incomplete values

Re-apply statistics privileges:

```sql
GRANT pg_monitor TO zabbix;
GRANT pg_read_all_stats TO zabbix;
```

Then test:

```bash
psql -h 127.0.0.1 -p 5432 -U zabbix -d postgres -c "SELECT application_name, client_addr, state, sync_state FROM pg_stat_replication;"
```

### `safe WAL size` returns `-1`

The value means the database reports the value as unavailable or unlimited. The template stores this as a numeric float to avoid unsigned integer errors.

### `wal_keep_size` differs from expected value

Check the active source of the setting:

```sql
SELECT name, setting, unit, source, sourcefile, sourceline, pending_restart
FROM pg_settings
WHERE name = 'wal_keep_size';
```

If the setting is overridden by `postgresql.auto.conf`, remove the stale override carefully according to your PostgreSQL/HA management process.

## Security notes

- Store `{$PG.CONN.PASSWORD}` as a secret macro where possible.
- Do not commit real passwords, hostnames, IP addresses, or customer-specific values to a public repository.
- Use a dedicated read-only monitoring user.
- Restrict PostgreSQL access for the monitoring user to the minimum required source addresses.
- Test alert thresholds in a non-production environment before enabling notifications.

## License

Licensed under the MIT License. See the `LICENSE` file for details.
