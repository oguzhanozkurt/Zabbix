# Cisco Unified Communications Manager (CUCM) by SNMP — Zabbix 7.0 Template

This repository provides a Zabbix **SNMP polling** template for monitoring **Cisco Unified Communications Manager (CUCM)** using:
- Standard MIBs (**MIB-II / SNMPv2-MIB**, **HOST-RESOURCES-MIB**), and
- Cisco **CISCO-CCM-MIB** **numeric OIDs** (no MIB import required on Zabbix).

- Template name: **Cisco Unified Communications Manager UCM by SNMP**
- Zabbix export: **7.0**
- File: `Cisco Unified Communications Manager UCM by SNMP.yaml`

> Community template — not affiliated with, endorsed by, or sponsored by Cisco.

---

## Scope / Coverage

### System & Inventory
- sysName / sysDescr / sysLocation / sysContact
- SNMP uptime
- CUCM system version
- CUCM installation ID
- Total RAM (HOST-RESOURCES-MIB)

### CUCM Device Counters (CISCO-CCM-MIB)
- Phones: registered / unregistered / rejected / partially registered
- Gateways: registered / unregistered / rejected
- Media devices: registered / unregistered / rejected
- CTI devices: registered / unregistered / rejected
- Voicemail devices: registered / unregistered / rejected
- H.323 table entries count
- SIP trunk table entries count

### Low-Level Discovery (LLD)
- Cluster nodes (status + version)
- Gateways (status + description)
- SIP trunks (description + inbound/outbound port + transport)
- CPU cores (per-core load)
- Fixed disks (used/total bytes + utilization triggers)

### Availability
- ICMP ping / loss / response time
- SNMP agent availability (Zabbix internal item)

---

## Important Notes (Operational)

- This template is **polling-only** (no traps).
- **CISCO-CCM-MIB dynamic tables** return data only when the relevant CUCM services are running.
- If CUCM returns empty CCM metrics, ensure:
  - **SNMP Master Agent** is enabled, and
  - **Cisco Unified CM SNMP Service** is active.
- SIP trunk SNMP table is mainly **inventory-oriented**; it is not rich enough alone for advanced trunk-state alerting.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- CUCM reachable via SNMP (UDP/161)
- Zabbix host must have an **SNMP interface** configured (SNMPv2c or SNMPv3)
- Optional (recommended): ICMP allowed from Zabbix to CUCM

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Cisco Unified Communications Manager UCM by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (CUCM IP/DNS + port 161)
- Configure SNMP credentials (community for v2c or SNMPv3 user/auth/priv)
- Link template: **Cisco Unified Communications Manager UCM by SNMP**

### 3) Tune Macros (Recommended)
Adjust macros to match your environment (polling intervals and thresholds).

---

## Macros

### Polling & Discovery
| Macro | Default | Description |
|------|---------|-------------|
| `{$CUCM.POLL}` | `5m` | Polling interval for “live” counters (phones/gateways/etc.), CPU load, disk used |
| `{$CUCM.DISCOVERY}` | `1h` | Discovery interval for LLD rules |
| `{$CUCM.INVENTORY}` | `1d` | Low-change inventory polling interval |

### Thresholds
| Macro | Default | Description |
|------|---------|-------------|
| `{$CUCM.CPU.WARN}` | `85` | CPU core load warning threshold (min over 15m) |
| `{$CUCM.CPU.HIGH}` | `95` | CPU core load high threshold (min over 15m) |
| `{$CUCM.STORAGE.WARN.PCT}` | `80` | Fixed disk usage warning threshold (%) |
| `{$CUCM.STORAGE.HIGH.PCT}` | `90` | Fixed disk usage high threshold (%) |
| `{$CUCM.UNREGISTERED.PHONES.WARN}` | `1` | Warning threshold for unregistered phones |
| `{$CUCM.PARTIAL.PHONES.WARN}` | `1` | Warning threshold for partially registered phones |

### Availability
| Macro | Default | Description |
|------|---------|-------------|
| `{$ICMP_LOSS_WARN}` | `20` | ICMP loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP RTT warning threshold (seconds) |
| `{$SNMP.TIMEOUT}` | `5m` | Window used to detect missing SNMP polling |

---

## Low-Level Discovery (LLD)

### Cluster Node Discovery
- Key: `cucm.cluster.node.discovery`
- Discovers `{#NODENAME}`, `{#VERSION}`
- Items:
  - Node status (value map: **CUCM callmanager status**)
  - Node version (inventory)
- Trigger prototype:
  - Node down when status = `down`

### CPU Core Discovery
- Key: `cucm.cpu.discovery`
- Source: HOST-RESOURCES-MIB hrDeviceTable (filtered to processors)
- Items:
  - Per-core CPU load (`%`)
- Trigger prototypes:
  - Warning/high thresholds using `{$CUCM.CPU.WARN}` / `{$CUCM.CPU.HIGH}` (min over 15m)

### Fixed Disk Discovery
- Key: `cucm.storage.discovery`
- Source: HOST-RESOURCES-MIB hrStorageTable (filtered to fixed disks)
- Items:
  - Disk total (bytes)
  - Disk used (bytes)
  - Values are normalized using `hrStorageAllocationUnits`
- Trigger prototypes:
  - Utilization warning/high thresholds using `{$CUCM.STORAGE.WARN.PCT}` / `{$CUCM.STORAGE.HIGH.PCT}`

### Gateway Discovery
- Key: `cucm.gateway.discovery`
- Items:
  - Gateway description (inventory)
  - Gateway status (value map: **CUCM device status**)
- Trigger prototypes:
  - Unregistered gateway
  - Rejected gateway registration

### SIP Trunk Discovery (Inventory)
- Key: `cucm.sip.discovery`
- Items:
  - SIP trunk description
  - Inbound/outbound port
  - Inbound/outbound transport (value map: **CUCM SIP transport**)

---

## Triggers (Included)

### Availability
- **Unavailable by ICMP ping** (DISASTER)
- **High ICMP ping loss** (WARNING)
- **High ICMP ping response time** (WARNING)
- **No SNMP data collection** (DISASTER, manual close)

### CUCM Counters (Examples)
- Rejected phone count > 0 (HIGH)
- Unregistered phone count above `{$CUCM.UNREGISTERED.PHONES.WARN}` (WARNING)
- Partially registered phone count above `{$CUCM.PARTIAL.PHONES.WARN}` (WARNING)
- Rejected gateway count > 0 (HIGH)
- Unregistered gateway count > 0 (WARNING)
- Rejected CTI device count > 0 (WARNING)

### LLD Trigger Prototypes
- Cluster node down (HIGH)
- CPU core load above warning/high threshold
- Storage usage above warning/high threshold
- Gateway unregistered / rejected registration

---

## Value Maps (Included)

- **CUCM callmanager status**: unknown / up / down
- **CUCM device status**: unknown / registered / unregistered / rejected / partially registered
- **CUCM SIP transport**: numeric transport mapping (applied to SIP trunk inbound/outbound transport)
- Standard Zabbix availability maps (SNMP availability) and service/ping mapping used by ICMP items

---

## Validation & Troubleshooting

### Validate SNMP Reachability
~~~bash
snmpget  -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.2.1.1.5.0
snmpget  -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.2.1.1.3.0
~~~

### Validate CUCM CCM OIDs Return Data
~~~bash
# Phones counters
snmpget -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.5.5.0
snmpget -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.5.6.0
snmpget -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.5.7.0

# Gateways counters
snmpget -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.5.8.0
snmpget -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.5.9.0
snmpget -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.5.10.0
~~~

### Validate LLD Tables (Optional)
~~~bash
# Cluster nodes table
snmpwalk -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.1.2.1

# Gateways table
snmpwalk -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.3.1.1

# SIP trunks table
snmpwalk -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.4.1.9.9.156.1.14.1.1

# CPU (HOST-RESOURCES-MIB)
snmpwalk -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.2.1.25.3.3.1.2

# Storage (HOST-RESOURCES-MIB)
snmpwalk -v2c -c <COMMUNITY> <CUCM_IP> 1.3.6.1.2.1.25.2.3.1
~~~

### If you see “No SNMP data collection”
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP credentials and version (v2c community or v3 auth/priv).
- Ensure the host has an SNMP interface configured in Zabbix.
- Confirm CUCM SNMP services are enabled (Master Agent + Unified CM SNMP Service) if CCM OIDs return empty.

---

## Security Notes

SNMPv2c uses community strings in plaintext. Reduce exposure by applying:
- Source IP allow-lists
- Network segmentation
- Firewall policies

If you require SNMPv3, configure SNMPv3 credentials on the host SNMP interface (OIDs remain the same).

---

## Contributing

Contributions are welcome, including:
- Adding additional CISCO-CCM-MIB counters (MGCP, CTI manager, call processing stats)
- Adding per-SIP-trunk state monitoring (if you have stronger data sources)
- Improved trigger thresholds and noise reduction (maintenance windows, dependencies)
- Documentation improvements and tested examples

Please open an issue with:
- CUCM version
- Zabbix version
- Sanitized `snmpwalk` excerpts for the relevant OIDs
- Expected vs. actual behavior

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Cisco.
