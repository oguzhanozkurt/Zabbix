# Symantec SMG Hardware Appliance by SNMP (Zabbix Template)

This repository provides a Zabbix template to monitor **Symantec Messaging Gateway (SMG) Hardware Appliance** via **SNMP**.

- Template name: **Symantec SMG Hardware Appliance by SNMP**
- Export format: **Zabbix 7.0**
- File: **Symantec SMG Hardware Appliance by SNMP.yaml**

Monitors SMG using **SYMANTEC-EMAIL-SECURITY MIB (mailSecurityAppliance)** in addition to standard **RFC1213 system OIDs**.

> Note: This is a community template and is not an official Broadcom/Symantec release.

---

## What’s Included

### Availability & Connectivity
- ICMP ping, packet loss, and response time
- SNMP agent availability (Zabbix internal check)

### System Information (SNMP system MIB)
- System name, description, contact, location
- Uptime (sysUpTime)

### Hardware Health (Appliance MIB)
- CPU internal temperature status
- Internal ambient temperature status
- Fan status (blower, memory, PCI)
- Power supply redundancy status
- Fan redundancy status

### Automated Discovery (LLD)
- SMG MTA instance discovery (hourly)
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
- SMG Hardware Appliance: **SNMP enabled** and reachable from Zabbix
- Network: UDP **161** allowed from Zabbix → SMG

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Symantec SMG Hardware Appliance by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (SMG IP/DNS + port)
- Link template: **Symantec SMG Hardware Appliance by SNMP**

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

### System (RFC1213 / SNMPv2-MIB)
- `system.descr` (OID: `1.3.6.1.2.1.1.1.0`)
- `system.contact[sysContact.0]` (OID: `1.3.6.1.2.1.1.4.0`)
- `system.name` (OID: `1.3.6.1.2.1.1.5.0`)
- `system.location[sysLocation.0]` (OID: `1.3.6.1.2.1.1.6.0`)
- `system.uptime` / `system.uptime[sysUpTime.0]` (OID: `1.3.6.1.2.1.1.3.0`)

### Hardware Health (mailSecurityAppliance)
Pass/Fail status value map:
- `1=pass`, `2=fail`, `3=unknown`, `4=unavailable`

Redundancy status value map:
- `1=fullyRedundant`, `2=redundancyLost`, `3=redundancyUnknown`

Monitored OIDs:
- CPU internal temperature status: `1.3.6.1.4.1.393.200.130.2.1.1.5.0`
- Internal ambient temperature status: `1.3.6.1.4.1.393.200.130.2.1.1.4.0`
- System blower fan status: `1.3.6.1.4.1.393.200.130.2.1.1.1.0`
- System memory fan status: `1.3.6.1.4.1.393.200.130.2.1.1.2.0`
- System PCI fan status: `1.3.6.1.4.1.393.200.130.2.1.1.3.0`
- Power supply redundancy status: `1.3.6.1.4.1.393.200.130.2.1.2.1.0`
- Fan redundancy status: `1.3.6.1.4.1.393.200.130.2.1.2.2.0`

---

## Discovery Details (LLD)

Discovery rule key: `smg.mta.discovery`  
Discovery definition:
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

### Connectivity / Data Collection
- **Unavailable by ICMP ping** (DISASTER)  
  Last three ping checks failed.
- **High ICMP ping loss** (WARNING)  
  `min(loss, 5m) > {$ICMP_LOSS_WARN}` and `< 100`
- **High ICMP ping response time** (WARNING)  
  `avg(rtt, 5m) > {$ICMP_RESPONSE_TIME_WARN}`
- **No SNMP data collection** (DISASTER)  
  `max(snmp_available, {$SNMP.TIMEOUT}) = 0`
- **Host has been restarted (uptime < 10m)** (HIGH)  
  Uptime is below 10 minutes.

### Hardware Health
- **CPU internal temperature failure** (HIGH)  
  Status equals `fail`.
- **Internal ambient temperature failure** (HIGH)  
  Status equals `fail`.
- **System blower fan failure** (HIGH)  
  Status equals `fail`.
- **System memory fan failure** (HIGH)  
  Status equals `fail`.
- **System PCI fan failure** (HIGH)  
  Status equals `fail`.
- **Power supply redundancy lost** (HIGH)  
  Redundancy equals `redundancyLost`.
- **Fan redundancy lost** (HIGH)  
  Redundancy equals `redundancyLost`.

---

## Validation & Troubleshooting

From your Zabbix server/proxy, validate SNMP access:

~~~bash
snmpwalk -v2c -c <COMMUNITY> <SMG_IP> 1.3.6.1.2.1.1
snmpwalk -v2c -c <COMMUNITY> <SMG_IP> 1.3.6.1.4.1.393.200.130.2.1
snmpwalk -v2c -c <COMMUNITY> <SMG_IP> 1.3.6.1.4.1.393.200.130.2.2.1.1
~~~

### If you see "No SNMP data collection"
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP community and port.
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether SMG restricts SNMP by source IP.

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
- Discovery (LLD) enhancements
- Trigger tuning and threshold recommendations
- Documentation improvements (examples, validation steps, known issues)

Please open an issue with:
- SMG version
- Zabbix version
- Sample `snmpwalk` output (sanitized)
- A clear description of expected vs. actual behavior
