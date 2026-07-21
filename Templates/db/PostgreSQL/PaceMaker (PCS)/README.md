# Pacemaker PostgreSQL Cluster Monitoring by Zabbix Trapper

This repository provides a Zabbix 7.0 template and sender-based integration to monitor **Pacemaker/Corosync active/passive PostgreSQL clusters**.

The solution is designed for environments where PostgreSQL is managed by Pacemaker as an OCF resource, for example:

~~~text
pgsvc (ocf:heartbeat:pgsql)
~~~

In this architecture, PostgreSQL may be `inactive` on passive nodes at the systemd level. Therefore, the monitoring logic is based on **Pacemaker cluster/resource state**, not PostgreSQL systemd service state.

- Template name: **Pacemaker cluster by Zabbix trapper**
- Zabbix export: **7.0**
- File: `template_cluster_pacemaker_zabbix_7.0.yaml`
- Collection method: `crm_mon -1 --output-as=xml` → `zabbix_sender` → Zabbix trapper item → dependent XMLPath items
- Primary item key: `pacemaker.cluster.raw`

> Note: This is a community template and is not an official Pacemaker, ClusterLabs, PostgreSQL, or Zabbix release.

---

## What’s Included

### Pacemaker Cluster State
- `crm_mon` command result
- Pacemaker stack status
- Current DC (Designated Controller)
- Quorum status
- Configured/online/pending/unclean node counts
- Quorum-only node monitoring
- Cluster maintenance mode
- Stop-all-resources mode
- Location ban count

### Fencing / STONITH
- STONITH enabled state
- Active STONITH resource count
- Failed STONITH resource detection

### PostgreSQL Resource Monitoring
- PostgreSQL resource existence
- PostgreSQL active instance count
- PostgreSQL running node
- PostgreSQL role
- PostgreSQL managed/blocked/failed state
- PostgreSQL monitor operation return code and execution time

### VIP and Resource Group Monitoring
- VIP resource existence
- VIP active instance count
- VIP running node
- VIP failed state
- PostgreSQL and VIP node mismatch detection
- Resource group active/unhealthy counts
- Resource group node mismatch detection

### Sender Logic
- Sender script is installed on every Pacemaker node.
- Under normal conditions, only the current Pacemaker **DC node** sends data.
- If no DC is present, reachable nodes may send data so quorum/DC failures remain visible.
- Zabbix proxy group targets are tried sequentially.
- The script stops after the first successful `zabbix_sender` delivery to prevent duplicate values through multiple proxies.
- Agent2 configuration can be used for `SourceIP` and TLS settings.
- A systemd timer runs the sender periodically, typically every 30 seconds.

---

## Supported Architecture

This integration is intended for:

- Zabbix **7.0**
- Zabbix Agent 2
- `zabbix_sender`
- Pacemaker / Corosync
- `crm_mon --output-as=xml` support
- Active/passive primitive PostgreSQL resource
- PostgreSQL resource running inside a Pacemaker resource group
- PostgreSQL VIP running in the same Pacemaker resource group

> This version is **not designed for promotable clone / multi-state PostgreSQL clusters**.  
> Promotable designs require additional handling for `Promoted` and `Unpromoted` roles instead of only `Started`.

---

## Recommended Repository Structure

~~~text
.
├── README.md
├── template_cluster_pacemaker_zabbix_7.0.yaml
├── zabbix-pacemaker-sender
├── pacemaker_sender.conf.example
├── zabbix-pacemaker-sudoers
├── zabbix-pacemaker-sender.service
├── zabbix-pacemaker-sender.timer
├── SHA256SUMS
└── LICENSE
~~~

---

## Monitoring Architecture

~~~text
Pacemaker node 1 ─┐
Pacemaker node 2 ─┼─ current DC ─ zabbix_sender ─ Zabbix proxy group ─ Zabbix server
Quorum-only node ─┘                         │
                                           └─ Logical host: pacemaker-cluster
                                              Item: pacemaker.cluster.raw
~~~

The sender files must be deployed to all Pacemaker nodes.

During normal operation:
- Only the current DC sends data.
- If the DC changes, the new DC automatically takes over at the next timer execution.
- Non-DC nodes exit successfully without sending duplicate data.

---

## Zabbix Host Model

### 1) Physical Pacemaker Nodes

Physical nodes should continue to use standard OS-level templates such as:

~~~text
Linux by Zabbix agent
Systemd by Zabbix agent 2
~~~

Do **not** link this Pacemaker trapper template directly to the physical node hosts.

### 2) Logical Pacemaker Cluster Host

Create one logical host in Zabbix:

~~~text
Host name: pacemaker-cluster
Visible name: Pacemaker PostgreSQL Cluster
Monitored by: Relevant Zabbix proxy group
Interface: Not required
Template: Pacemaker cluster by Zabbix trapper
~~~

`pacemaker-cluster` is an example. You may use another host name, but the same value must be configured as `ZABBIX_HOST` in `/etc/zabbix/pacemaker_sender.conf` on every Pacemaker node.

### 3) PostgreSQL Application Monitoring Host

SQL-level PostgreSQL monitoring should be configured separately, preferably through the PostgreSQL VIP:

~~~text
Host name: pacemaker-postgresql
Interface: PostgreSQL VIP
Template: PostgreSQL by Zabbix agent 2
~~~

This template does **not** replace PostgreSQL SQL, transaction, lock, WAL, replication, or database availability monitoring.

---

## Requirements

On every Pacemaker node, the following commands/users must be available:

~~~bash
command -v crm_mon
command -v crm_node
command -v zabbix_sender
id zabbix
~~~

On RHEL-based systems, install `zabbix_sender` if it is missing:

~~~bash
dnf install -y zabbix-sender
~~~

Record the real command paths:

~~~bash
command -v crm_mon
command -v crm_node
command -v zabbix_sender
~~~

Default paths used in this README:

~~~text
/usr/sbin/crm_mon
/usr/sbin/crm_node
/usr/bin/zabbix_sender
~~~

If your paths are different, update both:
- `/etc/zabbix/pacemaker_sender.conf`
- `/etc/sudoers.d/zabbix-pacemaker`

---

## Installation

### 1) Import the Zabbix Template

Zabbix UI:

~~~text
Data collection → Templates → Import
~~~

Import:

~~~text
template_cluster_pacemaker_zabbix_7.0.yaml
~~~

After import, the template name should be:

~~~text
Pacemaker cluster by Zabbix trapper
~~~

---

### 2) Create the Logical Cluster Host

Zabbix UI:

~~~text
Data collection → Hosts → Create host
~~~

Example configuration:

~~~text
Host name: pacemaker-cluster
Visible name: Pacemaker PostgreSQL Cluster
Host groups: Linux clusters
Monitored by: Proxy group
Proxy group: <PROXY_GROUP_NAME>
Status: Enabled
~~~

No Agent, SNMP, JMX, or IPMI interface is required for this logical host.

Link the template:

~~~text
Pacemaker cluster by Zabbix trapper
~~~

---

### 3) Configure Template Macros

The default macro values are based on a three-node sample architecture. Review and override all values before production use.

| Macro | Default | Description |
|---|---:|---|
| `{$PACEMAKER.NODE.EXPECTED}` | `3` | Expected number of online Pacemaker nodes. |
| `{$PACEMAKER.QUORUM_ONLY.EXPECTED}` | `1` | Expected number of online quorum-only nodes. |
| `{$PACEMAKER.RESOURCE.EXPECTED}` | `13` | Expected total Pacemaker resource instances. |
| `{$PACEMAKER.STONITH.EXPECTED}` | `3` | Expected number of configured and active STONITH resources. |
| `{$PACEMAKER.GROUP.ID}` | `pg_group` | PostgreSQL Pacemaker resource group ID. |
| `{$PACEMAKER.GROUP.RESOURCE.EXPECTED}` | `10` | Expected number of resources inside the PostgreSQL resource group. |
| `{$PACEMAKER.PGSQL.ID}` | `pgsvc` | PostgreSQL OCF resource ID. |
| `{$PACEMAKER.VIP.ID}` | `pgvip` | PostgreSQL VIP resource ID. |
| `{$PACEMAKER.BAN.EXPECTED}` | `1` | Expected location ban count. |
| `{$PACEMAKER.NODATA}` | `2m` | Maximum accepted time without receiving cluster XML data. |
| `{$PACEMAKER.FAILOVER.GRACE}` | `2m` | Grace period before PostgreSQL/VIP availability alarms fire during failover. |

Useful validation commands:

~~~bash
pcs status --full
pcs resource config
crm_mon -1 --output-as=xml
~~~

---

### 4) Configure Trapper Allowed Hosts

On the logical cluster host, open this item:

~~~text
Pacemaker: Get cluster status
Key: pacemaker.cluster.raw
~~~

Optionally configure **Allowed hosts** with the source IP addresses of the Pacemaker nodes as seen by the Zabbix proxy/server:

~~~text
192.0.2.11,192.0.2.12,192.0.2.13
~~~

For initial testing, this field can be left empty. After validating data flow, applying an IP/CIDR restriction is recommended.

If NAT is used, configure the source IP as seen by the Zabbix proxy/server, not necessarily the local node IP.

---

### 5) Configure Proxy Group Targets

Example Zabbix Agent2 active server/proxy group configuration:

~~~ini
ServerActive=10.20.30.40;10.20.30.41
~~~

A semicolon (`;`) separates members of the same proxy group / HA endpoint list.

This project intentionally avoids using only `zabbix_sender -c`, because `zabbix_sender` may send the same value to all `ServerActive` entries. That can create duplicate data through multiple proxies.

Instead, the sender script:

1. Splits `ZABBIX_TARGETS` by semicolon.
2. Tries each proxy target sequentially.
3. Uses `-z` to select one target at a time.
4. Exits after the first successful delivery.
5. Uses `-c` only to inherit Agent2 `SourceIP` and TLS-related parameters.

Example node configuration:

~~~bash
ZABBIX_TARGETS="10.20.30.40;10.20.30.41"
~~~

Single proxy or direct server example:

~~~bash
ZABBIX_TARGETS="10.20.30.40"
~~~

All targets are expected to use the same trapper port:

~~~bash
ZABBIX_PORT="10051"
~~~

---

### 6) Deploy Files to All Pacemaker Nodes

Run these steps on **every** Pacemaker node:
- Active-capable PostgreSQL node
- Passive PostgreSQL node
- Quorum-only node, if present

From the repository directory:

~~~bash
install -o root -g zabbix -m 0750 \
  zabbix-pacemaker-sender \
  /usr/local/sbin/zabbix-pacemaker-sender

install -o root -g zabbix -m 0640 \
  pacemaker_sender.conf.example \
  /etc/zabbix/pacemaker_sender.conf

install -o root -g root -m 0440 \
  zabbix-pacemaker-sudoers \
  /etc/sudoers.d/zabbix-pacemaker

install -o root -g root -m 0644 \
  zabbix-pacemaker-sender.service \
  /etc/systemd/system/zabbix-pacemaker-sender.service

install -o root -g root -m 0644 \
  zabbix-pacemaker-sender.timer \
  /etc/systemd/system/zabbix-pacemaker-sender.timer
~~~

Validate ownership and permissions:

~~~bash
stat -c '%U:%G %a %n' \
  /usr/local/sbin/zabbix-pacemaker-sender \
  /etc/zabbix/pacemaker_sender.conf \
  /etc/sudoers.d/zabbix-pacemaker \
  /etc/systemd/system/zabbix-pacemaker-sender.service \
  /etc/systemd/system/zabbix-pacemaker-sender.timer
~~~

Expected:

~~~text
root:zabbix 750 /usr/local/sbin/zabbix-pacemaker-sender
root:zabbix 640 /etc/zabbix/pacemaker_sender.conf
root:root 440 /etc/sudoers.d/zabbix-pacemaker
root:root 644 /etc/systemd/system/zabbix-pacemaker-sender.service
root:root 644 /etc/systemd/system/zabbix-pacemaker-sender.timer
~~~

---

### 7) Configure the Sender

Edit the configuration file on every node:

~~~bash
vi /etc/zabbix/pacemaker_sender.conf
~~~

Example:

~~~bash
ZABBIX_HOST="pacemaker-cluster"

ZABBIX_TARGETS="10.20.30.40;10.20.30.41"
ZABBIX_PORT="10051"
ZABBIX_TIMEOUT="10"

ZABBIX_AGENT_CONFIG="/etc/zabbix/zabbix_agent2.conf"

CRM_MON="/usr/sbin/crm_mon"
CRM_NODE="/usr/sbin/crm_node"
ZABBIX_SENDER="/usr/bin/zabbix_sender"
~~~

Important points:

- `ZABBIX_HOST` must match the technical **Host name** in Zabbix exactly.
- Visible name is not used.
- `ZABBIX_TARGETS` should contain proxy/server targets separated by semicolons.
- DNS names can be used if the Agent2 runtime can resolve them.
- `ZABBIX_TIMEOUT` is the sender timeout per proxy target.
- With two proxies and a 10-second timeout, the second proxy is attempted after the first one times out.

Secure the configuration file:

~~~bash
chown root:zabbix /etc/zabbix/pacemaker_sender.conf
chmod 640 /etc/zabbix/pacemaker_sender.conf
~~~

The file is sourced by the shell, so it must not be writable by the `zabbix` user.

---

### 8) Configure sudoers

Validate command paths first:

~~~bash
command -v crm_mon
command -v crm_node
~~~

Default sudoers content:

~~~sudoers
zabbix ALL=(root) NOPASSWD: /usr/sbin/crm_mon -1 --output-as=xml
zabbix ALL=(root) NOPASSWD: /usr/sbin/crm_node -n
~~~

Validate the sudoers file:

~~~bash
visudo -cf /etc/sudoers.d/zabbix-pacemaker
~~~

Expected output:

~~~text
/etc/sudoers.d/zabbix-pacemaker: parsed OK
~~~

Test permissions:

~~~bash
sudo -u zabbix sudo -n /usr/sbin/crm_node -n

sudo -u zabbix sudo -n \
  /usr/sbin/crm_mon -1 --output-as=xml | head
~~~

Expected:
- The first command returns the local Pacemaker node name.
- The second command returns XML beginning with `<pacemaker-result`.

---

### 9) TLS Usage

The sender runs `zabbix_sender` with the following model:

~~~text
-c /etc/zabbix/zabbix_agent2.conf
-z <selected_proxy>
~~~

Through `-c`, the sender may inherit Agent2 parameters such as:

- `SourceIP`
- `TLSConnect`
- `TLSCAFile`
- `TLSCRLFile`
- `TLSServerCertIssuer`
- `TLSServerCertSubject`
- `TLSCertFile`
- `TLSKeyFile`
- `TLSPSKIdentity`
- `TLSPSKFile`

The `-z` and `-p` options override the `ServerActive` target for the actual sender delivery.

#### PSK Consideration

If the sender reuses the physical node’s Agent2 PSK configuration, the logical `pacemaker-cluster` host must accept that TLS/PSK identity.

If multiple physical nodes use different PSK identities, choose one of the following approaches:

- Use a shared sender-specific PSK identity/key for all sender nodes.
- Use certificate-based TLS for the logical host.
- Create a separate shared Agent-style TLS configuration file for the sender.

This additional step is not required for unencrypted sender connections.

---

### 10) Enable the systemd Timer

Run on every node:

~~~bash
systemctl daemon-reload
systemctl enable --now zabbix-pacemaker-sender.timer
~~~

Run the service manually once:

~~~bash
systemctl start zabbix-pacemaker-sender.service
~~~

Check the timer:

~~~bash
systemctl status zabbix-pacemaker-sender.timer
systemctl list-timers --all | grep zabbix-pacemaker
~~~

The service is `Type=oneshot`, so it is normal for it to show as:

~~~text
inactive (dead)
~~~

The unit that must stay active is:

~~~text
zabbix-pacemaker-sender.timer
~~~

View logs:

~~~bash
journalctl -u zabbix-pacemaker-sender.service -n 100 --no-pager
journalctl -u zabbix-pacemaker-sender.service -f
~~~

---

## Manual Validation

### Find the Current DC Node

~~~bash
pcs status --full | grep 'Current DC'
~~~

or:

~~~bash
crm_mon -1 | grep 'Current DC'
~~~

### Test on the DC Node

~~~bash
sudo -u zabbix /usr/local/sbin/zabbix-pacemaker-sender
echo "Return code: $?"
~~~

Successful delivery example:

~~~text
processed: 1; failed: 0; total: 1
Return code: 0
~~~

### Test on a Non-DC Node

~~~bash
sudo -u zabbix /usr/local/sbin/zabbix-pacemaker-sender
echo "Return code: $?"
~~~

Normal result:

~~~text
Return code: 0
~~~

A non-DC node may exit without output. This means it intentionally skipped sending data to avoid duplicate values.

### Direct Trapper Test

Use this to validate sender connectivity and trapper item acceptance:

~~~bash
sudo -u zabbix zabbix_sender \
  -c /etc/zabbix/zabbix_agent2.conf \
  -z 10.20.30.40 \
  -p 10051 \
  -t 10 \
  -s "pacemaker-cluster" \
  -k pacemaker.cluster.raw \
  -o '<pacemaker-result><status code="0" message="OK"/></pacemaker-result>' \
  -vv
~~~

This minimal XML validates transport only. Full dependent item validation requires real `crm_mon` XML.

---

## Latest Data Validation

Zabbix UI:

~~~text
Monitoring → Latest data → pacemaker-cluster
~~~

First validate the master item:

~~~text
Pacemaker: Get cluster status
Key: pacemaker.cluster.raw
~~~

Then verify dependent items.

For a healthy three-node example, typical values may look like:

| Item | Expected |
|---|---:|
| Pacemaker: crm_mon result is OK | `1` |
| Pacemaker: Stack is running | `1` |
| Pacemaker: DC is present | `1` |
| Pacemaker: Cluster has quorum | `1` |
| Pacemaker: Online node count | `3` |
| Pacemaker: Online quorum-only node count | `1` |
| Pacemaker: Active STONITH resource count | `3` |
| Pacemaker pg_group: Resource count | `10` |
| Pacemaker pg_group: Active resource count | `10` |
| Pacemaker pg_group: Unhealthy resource count | `0` |
| Pacemaker PostgreSQL: Active instance count | `1` |
| Pacemaker PostgreSQL: Role | `Started` |
| Pacemaker VIP: Active instance count | `1` |
| PostgreSQL and VIP node mismatch | `0` |

These values are examples. Your expected values must match your own cluster design and macro configuration.

---

## Systemd Template Adjustment

If PostgreSQL is managed by Pacemaker, exclude the PostgreSQL unit from the physical node’s Systemd service discovery.

Find the actual unit name:

~~~bash
systemctl list-unit-files --type=service |
  grep -Ei 'postgres|pgsql'
~~~

Adjust this macro on the physical host or parent systemd template:

~~~text
{$SYSTEMD.NAME.SERVICE.NOT_MATCHES}
~~~

Example regex:

~~~regex
^(postgresql.*|pgsql.*)\.service$
~~~

If exclusions already exist, merge them into a single regex:

~~~regex
^(dnf-makecache|kdump|postgresql.*|pgsql.*)\.service$
~~~

These cluster services should continue to be monitored by the Systemd template:

~~~text
corosync.service
pacemaker.service
pcsd.service
sbd.service
~~~

`sbd.service` applies only if SBD is used.

> Do not manage Pacemaker-controlled PostgreSQL resources with Zabbix remote commands such as `systemctl start`, `systemctl stop`, or `systemctl restart`.

---

## Monitored Items Summary

The template monitors:

- `crm_mon` command status
- Pacemaker stack state
- Current DC
- Quorum
- Configured, online, pending, and unclean node counts
- Quorum-only node state
- Cluster maintenance mode
- Stop-all-resources mode
- STONITH enabled/active/failed state
- Total resource and blocked resource counts
- Location ban count
- PostgreSQL resource group state
- PostgreSQL resource availability, role, running node, failed/blocked/managed state
- PostgreSQL monitor operation return code and execution time
- VIP resource availability and running node
- PostgreSQL/VIP node mismatch
- Resource group node mismatch

---

## Triggers Included

### Cluster / Data Collection
- Cluster status data unavailable
- `crm_mon` returned non-OK status
- Cluster stack is not running
- DC is not present
- Quorum lost
- One or more nodes offline
- One or more nodes unclean
- Pending nodes remain pending
- Cluster maintenance mode enabled
- Stop-all-resources enabled

### Fencing / STONITH
- STONITH disabled
- STONITH active resource count mismatch
- STONITH resource failed

### Resource Counts / Bans
- Configured resource count mismatch
- Blocked resources detected
- Location ban count mismatch

### PostgreSQL Resource
- PostgreSQL resource missing
- PostgreSQL active instance count is not one
- PostgreSQL resource is failed
- PostgreSQL resource is blocked
- PostgreSQL resource is unmanaged
- PostgreSQL monitor operation failed or has unexpected return code

### VIP / Placement
- VIP resource missing
- VIP active instance count is not one
- VIP resource failed
- PostgreSQL and VIP are running on different nodes
- Resource group members are running on different nodes

---

## Security Notes

- Sudo access is limited to two read-only Pacemaker commands:
  - `crm_mon -1 --output-as=xml`
  - `crm_node -n`
- Do not grant wildcard sudo permissions.
- Do not make `/etc/zabbix/pacemaker_sender.conf` writable by the `zabbix` user.
- Use `Allowed hosts` on the trapper item after validating data flow.
- Use TLS for `zabbix_sender` where possible.
- The sender runs as the `zabbix` user, not as root.
- The systemd service should restrict home access and system directory writes.
- Do not add `NoNewPrivileges=true`; it may prevent `sudo` setuid execution.

---

## Troubleshooting

### `ZABBIX_HOST is required`

~~~bash
grep '^ZABBIX_HOST=' /etc/zabbix/pacemaker_sender.conf
~~~

The value must be defined and must not be empty.

### `ZABBIX_TARGETS is required`

~~~bash
grep '^ZABBIX_TARGETS=' /etc/zabbix/pacemaker_sender.conf
~~~

Proxy group example:

~~~bash
ZABBIX_TARGETS="10.20.30.40;10.20.30.41"
~~~

### `Configuration file is not readable`

~~~bash
ls -l /etc/zabbix/pacemaker_sender.conf
sudo -u zabbix test -r /etc/zabbix/pacemaker_sender.conf && echo OK
~~~

### `Zabbix agent configuration is not readable`

~~~bash
ls -l /etc/zabbix/zabbix_agent2.conf
sudo -u zabbix test -r /etc/zabbix/zabbix_agent2.conf && echo OK
~~~

### `sudo: a password is required`

~~~bash
visudo -cf /etc/sudoers.d/zabbix-pacemaker

sudo -u zabbix sudo -n /usr/sbin/crm_node -n
sudo -u zabbix sudo -n /usr/sbin/crm_mon -1 --output-as=xml
~~~

The command paths in sudoers must exactly match the paths configured in `pacemaker_sender.conf`.

### `processed: 0; failed: 1`

Check:

- `ZABBIX_HOST` matches the Zabbix technical host name.
- The logical host is enabled.
- The template is linked to the logical host.
- `pacemaker.cluster.raw` is a Zabbix trapper item.
- The item is enabled.
- `Allowed hosts` accepts the sender source IP.
- The host is monitored by the expected proxy group.
- Zabbix configuration cache has been refreshed.

### Sender fails for all proxies

~~~bash
nc -vz 10.20.30.40 10051
nc -vz 10.20.30.41 10051
~~~

Check firewall, routing, proxy trapper processes, and TLS settings.

### Service failed, timer active

~~~bash
systemctl status zabbix-pacemaker-sender.service
journalctl -u zabbix-pacemaker-sender.service -n 100 --no-pager
~~~

The timer will retry periodically. The actual error should be visible in the service journal.

### Dependent item preprocessing errors

Copy the XML from the master item history and test it in the preprocessing test screen:

~~~text
Data collection → Hosts → Items → Preprocessing → Test
~~~

Verify that Pacemaker resource names match the template macros.

---

## Failover Test Procedure

Before a planned failover test, confirm your operational procedure and fencing state.

Recommended monitoring validation:

1. Record the current DC and PostgreSQL running node.
2. Perform the resource move/failover according to your internal procedure.
3. Confirm that **Pacemaker PostgreSQL: Running node** changes.
4. Confirm that **Pacemaker VIP: Running node** moves to the same node.
5. Confirm that **PostgreSQL and VIP node mismatch** remains `0`.
6. If the failover completes within `{$PACEMAKER.FAILOVER.GRACE}`, PostgreSQL/VIP availability alarms should not fire.
7. If the DC changes, confirm that the new DC node takes over sender execution.

Check sender logs:

~~~bash
journalctl -u zabbix-pacemaker-sender.service --since '-10 minutes'
~~~

---

## Update

### Update the Template

Zabbix UI:

~~~text
Data collection → Templates → Import
~~~

Import the updated YAML file and update existing objects.

### Update Node Files

~~~bash
install -o root -g zabbix -m 0750 \
  zabbix-pacemaker-sender \
  /usr/local/sbin/zabbix-pacemaker-sender

install -o root -g root -m 0644 \
  zabbix-pacemaker-sender.service \
  /etc/systemd/system/zabbix-pacemaker-sender.service

install -o root -g root -m 0644 \
  zabbix-pacemaker-sender.timer \
  /etc/systemd/system/zabbix-pacemaker-sender.timer

systemctl daemon-reload
systemctl restart zabbix-pacemaker-sender.timer
~~~

Do not automatically overwrite the existing `/etc/zabbix/pacemaker_sender.conf`. Compare it with the new example file first.

---

## Uninstall

Run on every node:

~~~bash
systemctl disable --now zabbix-pacemaker-sender.timer

rm -f /etc/systemd/system/zabbix-pacemaker-sender.timer
rm -f /etc/systemd/system/zabbix-pacemaker-sender.service
rm -f /usr/local/sbin/zabbix-pacemaker-sender
rm -f /etc/zabbix/pacemaker_sender.conf
rm -f /etc/sudoers.d/zabbix-pacemaker

systemctl daemon-reload
systemctl reset-failed
~~~

Then remove or unlink the template from the logical Zabbix cluster host.

---

## Validation Performed

The release package was validated with:

- YAML parse validation
- UUIDv4 uniqueness validation
- Template object review
- XMLPath expression validation against sample Pacemaker XML
- Simulation where PostgreSQL monitor history is missing
- `bash -n` sender script syntax validation
- `visudo -cf` sudoers validation
- `systemd-analyze verify` service/timer validation
- DC node sender test
- Non-DC node skip test
- Fallback sender test when no DC is present
- Proxy failover test from first proxy to second proxy
- Duplicate-send prevention check after the first successful sender delivery

---

## Official Documentation

- [Zabbix 7.0 zabbix_sender man page](https://www.zabbix.com/documentation/7.0/en/manpages/zabbix_sender)
- [Zabbix 7.0 Agent 2 configuration](https://www.zabbix.com/documentation/7.0/en/manual/appendix/config/zabbix_agent2)
- [Zabbix 7.0 trapper items](https://www.zabbix.com/documentation/7.0/en/manual/config/items/itemtypes/trapper)
- [Zabbix 7.0 template import/export](https://www.zabbix.com/documentation/7.0/en/manual/xml_export_import/templates)
- [Zabbix Systemd integration](https://www.zabbix.com/integrations/systemd)
- [Pacemaker command-line XML output](https://projects.clusterlabs.org/w/projects/pacemaker/pacemaker_command-line_output/)

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by ClusterLabs, Pacemaker, Corosync, PostgreSQL, or Zabbix.
