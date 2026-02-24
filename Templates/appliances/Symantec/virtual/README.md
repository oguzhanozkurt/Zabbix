# Symantec SMG Virtual Appliance by SNMP (Zabbix Template)

This repository provides a Zabbix template to monitor **Symantec Messaging Gateway (SMG) Virtual Appliance** via **SNMP**.

- Template name: **Symantec SMG Virtual Appliance by SNMP**
- Export format: **Zabbix 7.0**
- File: **Symantec SMG Virtual Appliance by SNMP.yaml**

> Note: This is a community template and is not an official Broadcom/Symantec release.

---

## What’s Included

### Availability & Connectivity
- **ICMP ping**, **packet loss**, and **response time**
- **SNMP agent availability** (Zabbix internal check)

### System Information (SNMP system MIB)
- System name, description, contact, location
- Uptime (sysUpTime)

### Automated Discovery (LLD)
- **SMG MTA instance discovery** (hourly)
- Automatically creates item prototypes per MTA instance for:
  - Connections
  - Data rate
  - Message rate
  - Deferred messages
  - Queued messages
  - Queue size
  - Instance description

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- SMG: **SNMP enabled** and reachable from Zabbix
- Network: UDP **161** allowed from Zabbix → SMG

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Symantec SMG Virtual Appliance by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (SMG IP/DNS + port)
- Link template: **Symantec SMG Virtual Appliance by SNMP**

### 3) Configure Macros (Recommended)
Set macros at **Host** level (or globally), as appropriate.

---

## Macros

### Template Macros (Included)
| Macro | Default | Description |
|------|---------|-------------|
| `{$SNMP_COMMUNITY}` | `public` | SNMP community for SNMPv2c |
| `{$SNMP_PORT}` | `161` | SNMP port |

> Tip: You can reference these macros directly in the host’s SNMP interface fields (community/port).

### Threshold Macros (Required for Triggers to Evaluate Correctly)
The template’s trigger expressions reference the macros below. Define them at host or global level:

| Macro | Example | Purpose |
|------|---------|---------|
| `{$ICMP_LOSS_WARN}` | `20` | Packet loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | RTT warning threshold (seconds) |
| `{$SNMP.TIMEOUT}` | `5m` | Time window used to detect missing SNMP polling |

---

## Monitored Items (Summary)

### Connectivity
- `icmpping`
- `icmppingloss` (%)
- `icmppingsec` (s)
- `zabbix[host,snmp,available]`

### System (SNMP)
- `system.descr` (OID: `1.3.6.1.2.1.1.1.0`)
- `system.contact[sysContact.0]` (OID: `1.3.6.1.2.1.1.4.0`)
- `system.name` (OID: `1.3.6.1.2.1.1.5.0`)
- `system.location[sysLocation.0]` (OID: `1.3.6.1.2.1.1.6.0`)
- `system.uptime` (OID: `1.3.6.1.2.1.1.3.0`, seconds)
- `system.uptime[sysUpTime.0]` (OID: `1.3.6.1.2.1.1.3.0`, uptime format)

---

## Discovery Details (LLD)

Discovery rule key: `smg.mta.discovery`  
SNMP discovery OID:
- `{#SMG.INDEX}` → `1.3.6.1.4.1.393.200.130.2.2.1.1.1`
- `{#SMG.INSTANCE}` → `1.3.6.1.4.1.393.200.130.2.2.1.1.2`

Item prototype OIDs (per `{#SMG.INDEX}`):
- Connections: `1.3.6.1.4.1.393.200.130.2.2.1.1.3.{#SMG.INDEX}`
- Data rate: `1.3.6.1.4.1.393.200.130.2.2.1.1.4.{#SMG.INDEX}`
- Deferred messages: `1.3.6.1.4.1.393.200.130.2.2.1.1.5.{#SMG.INDEX}`
- Message rate: `1.3.6.1.4.1.393.200.130.2.2.1.1.6.{#SMG.INDEX}`
- Queue size: `1.3.6.1.4.1.393.200.130.2.2.1.1.7.{#SMG.INDEX}`
- Queued messages: `1.3.6.1.4.1.393.200.130.2.2.1.1.8.{#SMG.INDEX}`

---

## Triggers (Included)

- **Unavailable by ICMP ping** (DISASTER)  
  Last three ping checks failed.
- **High ICMP ping loss** (WARNING)  
  `min(loss, 5m) > {$ICMP_LOSS_WARN}` and `< 100`
- **High ICMP ping response time** (WARNING)  
  `avg(rtt, 5m) > {$ICMP_RESPONSE_TIME_WARN}`
- **No SNMP data collection** (DISASTER)  
  `max(snmp_available, {$SNMP.TIMEOUT}) = 0`
- **Host has been restarted (uptime < 10m)** (HIGH)  
  Uptime is below 10 minutes (depends on SNMP availability trigger)

---

## Validation & Troubleshooting

From your Zabbix server/proxy, validate SNMP access:

```bash
snmpwalk -v2c -c <COMMUNITY> <SMG_IP> 1.3.6.1.2.1.1
snmpwalk -v2c -c <COMMUNITY> <SMG_IP> 1.3.6.1.4.1.393.200.130.2.2.1.1
