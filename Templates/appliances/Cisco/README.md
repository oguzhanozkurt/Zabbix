# Cisco IronPort ESA by SNMP (Zabbix Template)

This repository provides a Zabbix template to monitor **Cisco IronPort / Cisco Secure Email Gateway (ESA/MGA)** via **SNMP**, using **ASYNCOS-MAIL-MIB**.

- Template name: **Cisco IronPort ESA by SNMP**
- Export format: **Zabbix 7.0**
- File: **Cisco IronPort ESA by SNMP.yaml**
- Base OID: `1.3.6.1.4.1.15497.1.1`

> Note: This is a community template and is not an official Cisco release.

---

## What’s Included

### Availability & Connectivity
- ICMP ping, packet loss, and response time
- SNMP agent availability (Zabbix internal check)

### System Information (SNMP)
- System name, description, contact, location
- Uptime (network and hardware uptime)

### Performance & Capacity (ASYNCOS-MAIL-MIB)
- CPU utilization
- Memory utilization
- Disk I/O utilization
- DNS pending/outstanding requests
- Mail transfer threads
- Open files/sockets

### Mail Queue & Operational Status
- Queue utilization
- Queue availability status
- Oldest message age
- Work queue messages
- Resource conservation reason/status

### Automated Discovery (LLD)
- Fans (RPM)
- Temperature sensors (°C)
- Power supplies (status/redundancy)
- RAID drives (status/last error)
- Update services (success/failure counters)
- Feature keys (perpetual + seconds-to-expire)

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Cisco ESA/MGA: **SNMP enabled** and reachable from Zabbix
- Network: UDP **161** allowed from Zabbix → ESA/MGA
- Optional (recommended): ICMP allowed from Zabbix → ESA/MGA

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Cisco IronPort ESA by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (ESA IP/DNS + port)
- Link template: **Cisco IronPort ESA by SNMP**

### 3) Configure Macros (Recommended)
Macros are included in the template. Review thresholds and adjust based on your environment.

---

## Macros

The template includes the following macros (defaults shown):

| Macro | Default | Description |
|------|---------|-------------|
| `{$CPU.UTIL.MAX}` | `90` | CPU utilization threshold (%) |
| `{$MEM.UTIL.MAX}` | `90` | Memory utilization threshold (%) |
| `{$QUEUE.UTIL.MAX}` | `90` | Queue utilization threshold (%) |
| `{$TEMP.MAX}` | `70` | Temperature threshold (°C) |
| `{$KEY.EXPIRE.WARN}` | `2592000` | Warn if a feature key expires within this many seconds (default: 30 days) |
| `{$ICMP_LOSS_WARN}` | `20` | ICMP loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP RTT warning threshold (seconds) |
| `{$SNMP.TIMEOUT}` | `5m` | Window used to detect missing SNMP polling |
| `{$PING.THRESOLD}` | `3m` | Window used for ICMP availability evaluation |

---

## Monitored Items (Summary)

### Connectivity
- `icmpping`
- `icmppingloss` (%)
- `icmppingsec` (s)
- `zabbix[host,snmp,available]`

### ASYNCOS Performance / Capacity
- CPU utilization: `ironport.cpu.util` (OID: `1.3.6.1.4.1.15497.1.1.1.2.0`)
- Memory utilization: `ironport.mem.util` (OID: `1.3.6.1.4.1.15497.1.1.1.1.0`)
- Disk I/O utilization: `ironport.diskio.util` (OID: `1.3.6.1.4.1.15497.1.1.1.3.0`)
- DNS outstanding: `ironport.dns.outstanding` (OID: `...1.1.1.15.0`)
- DNS pending: `ironport.dns.pending` (OID: `...1.1.1.16.0`)
- Mail transfer threads: `ironport.mail.transfer.threads` (OID: `...1.1.1.20.0`)
- Open files/sockets: `ironport.open.files.sockets` (OID: `...1.1.1.19.0`)

### Queue / Operational
- Queue utilization: `ironport.queue.util` (OID: `...1.1.1.4.0`)
- Queue availability status: `ironport.queue.availability` (OID: `...1.1.1.5.0`)
- Oldest message age: `ironport.queue.oldest.age` (OID: `...1.1.1.14.0`)
- Work queue messages: `ironport.workqueue.messages` (OID: `...1.1.1.11.0`)
- Resource conservation reason: `ironport.resource.conservation.reason` (OID: `...1.1.1.6.0`)

> Note on enums: Some items return numeric enum values as defined in **ASYNCOS-MAIL-MIB**. If you want human-readable states, you can add/attach a Zabbix value map.

---

## Low-Level Discovery (LLD)

Discovery rules included:

- **Fans**  
  Rule key: `ironport.fan.discovery`  
  Prototype: `Fan [{#FAN_NAME}] RPM` → `ironport.fan.rpm[{#SNMPINDEX}]`

- **Temperature sensors**  
  Rule key: `ironport.temp.discovery`  
  Prototype: `Temperature [{#TEMP_NAME}]` → `ironport.temp.c[{#SNMPINDEX}]`

- **Power supplies**  
  Rule key: `ironport.psu.discovery`  
  Prototypes:
  - `Power supply [{#PS_NAME}] status (enum)` → `ironport.psu.status[{#SNMPINDEX}]`
  - `Power supply [{#PS_NAME}] redundancy (enum)` → `ironport.psu.redundancy[{#SNMPINDEX}]`

- **RAID drives**  
  Rule key: `ironport.raid.discovery`  
  Prototypes:
  - `RAID drive [{#RAID_ID}] status (enum)` → `ironport.raid.status[{#SNMPINDEX}]`
  - `RAID drive [{#RAID_ID}] last error` → `ironport.raid.last_error[{#SNMPINDEX}]`

- **Update services**  
  Rule key: `ironport.updates.discovery`  
  Prototypes:
  - `Update [{#UPD_NAME}] successes` → `ironport.update.ok[{#SNMPINDEX}]`
  - `Update [{#UPD_NAME}] failures` → `ironport.update.fail[{#SNMPINDEX}]`

- **Feature keys**  
  Rule key: `ironport.keys.discovery`  
  Prototypes:
  - `Key [{#KEY_DESC}] perpetual (TruthValue)` → `ironport.key.perpetual[{#SNMPINDEX}]`
  - `Key [{#KEY_DESC}] seconds to expire` → `ironport.key.seconds_to_expire[{#SNMPINDEX}]`

---

## Triggers (Included)

### Availability / Connectivity
- **Unavailable by ICMP ping** (DISASTER)  
  `max(icmpping, {$PING.THRESOLD}) = 0`
- **High ICMP ping loss** (WARNING)  
  `min(loss, 5m) > {$ICMP_LOSS_WARN}` and `< 100`
- **High ICMP ping response time** (WARNING)  
  `avg(rtt, 5m) > {$ICMP_RESPONSE_TIME_WARN}`

### SNMP Polling
- **No SNMP data collection** (DISASTER)  
  `max(zabbix[host,snmp,available], {$SNMP.TIMEOUT}) = 0`

### Capacity / Queue
- **High CPU utilization** (DISASTER)  
  `max(ironport.cpu.util, 5m) > {$CPU.UTIL.MAX}`
- **High memory utilization** (DISASTER)  
  `max(ironport.mem.util, 5m) > {$MEM.UTIL.MAX}`
- **High queue utilization** (DISASTER)  
  `max(ironport.queue.util, 5m) > {$QUEUE.UTIL.MAX}`
- **Mail queue is full** (DISASTER)  
  `last(ironport.queue.availability) = 3`
- **Resource conservation mode active** (HIGH)  
  `last(ironport.resource.conservation.reason) <> 1`

### Informational
- **Host has been restarted (uptime < 10m)** (HIGH)  
  Uses hardware uptime when available; falls back to network uptime.  
  Dependency: **No SNMP data collection**

---

## Validation & Troubleshooting

From your Zabbix server/proxy, validate SNMP access:

~~~bash
snmpwalk -v2c -c <COMMUNITY> <ESA_IP> 1.3.6.1.2.1.1
snmpwalk -v2c -c <COMMUNITY> <ESA_IP> 1.3.6.1.4.1.15497.1.1
~~~

### If you see "No SNMP data collection"
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP community and port.
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether ESA/MGA restricts SNMP by source IP.

---

## Security Notes

SNMPv2c uses community strings in plaintext. Reduce exposure by applying:
- Source IP allow-lists
- Network segmentation
- Firewall policies

If you require SNMPv3, you can adapt the host SNMP interface settings accordingly (the template OIDs remain the same).

---

## Contributing

Contributions are welcome, including:
- OID corrections and coverage improvements
- Additional value maps for enum items (readability)
- New triggers (e.g., temperature/fan/RAID status thresholds)
- Documentation improvements and validation examples

Please open an issue with:
- ESA/MGA model and AsyncOS version
- Zabbix version
- Sanitized `snmpwalk` output for relevant OIDs
- Expected vs. actual behavior
