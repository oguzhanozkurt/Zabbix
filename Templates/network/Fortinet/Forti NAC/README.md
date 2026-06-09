# Fortinet FortiNAC by SNMP (Zabbix 7.0 Template)

This repository provides a Zabbix template to monitor **Fortinet FortiNAC** via **SNMP**, based on FortiNAC MIB reference OIDs and standard SNMP system OIDs.

- Template name: **Fortinet FortiNAC by SNMP**
- Zabbix export: **7.0**
- File: `Fortinet FortiNAC by SNMP.yaml`
- SNMP base (FortiNAC enterprise): `{$FORTINAC.BASE}` (default: `1.3.6.1.4.1.16856`)

> Note: This is a community template and is not an official Fortinet release.

---

## What’s Included

### Availability / Basic System
- **System name** (`sysName`)
- **System description** (`sysDescr`)
- **Uptime** (`sysUpTime`) normalized to seconds
- **No data** detection trigger (SNMP polling stopped or unreachable)

### License Utilization
- Concurrent license count (max)
- Concurrent licenses used
- **Concurrent license usage (%)** (calculated)

### Memory & Swap
- Memory total / free (bytes)
- **Memory free (%)** (calculated) + low free memory trigger
- Swap total / free (bytes)
- **Swap free (%)** (calculated) + low free swap trigger

### Client & User Posture Counters
Counts are provided as totals and, where available, split by **online/offline**:
- Managed clients total
- Registered clients (total/online/offline)
- Rogue clients (total/online/offline)
- At-risk clients (total/online/offline)
- Disabled clients (total/online/offline)
- Managed users (total/online/offline)
- IP phones (total/online/offline)

### Managed Device Inventory Counters
Managed device counts (total/online/offline) by type:
- Routers
- Wired switches / Wireless switches
- Servers
- Hubs
- Printers
- Interfaces
- Uplinks (total + user-defined uplinks)

### Platform Inventory
- OS version
- Database version
- Web version

### Hardware Inventory
- CPU description
- CPU count
- CPU cache

### Disk Metrics (Disabled by Default)
The template includes:
- Disk total (bytes)
- Disk free (bytes)
- Disk free (%) (calculated)

**These items are disabled by default** because Fortinet release notes mention `totalDisk/freeDisk` may return `0` on some FortiNAC-F versions. If your FortiNAC returns valid values, you can enable them.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- FortiNAC reachable via SNMP (UDP/161)
- Zabbix host must have an **SNMP interface** configured (SNMPv2c or SNMPv3)
- Network access: Zabbix → FortiNAC **UDP/161**

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Fortinet FortiNAC by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (FortiNAC IP/DNS + port 161)
- Configure SNMP credentials (community for v2c or user/auth/priv for v3)
- Link template: **Fortinet FortiNAC by SNMP**

### 3) Review Macros (Thresholds & Base OID)
The template is usable out-of-the-box, but you should review thresholds and the base OID macro.

### 4) (Optional) Enable Disk Items
If your FortiNAC reports valid disk OIDs, enable these items:
- `Disk total` (`fortinac.disk.total`)
- `Disk free` (`fortinac.disk.free`)
- `Disk free (%)` (`fortinac.disk.free.pct`)

---

## Macros

| Macro | Default | Description |
|---|---:|---|
| `{$FORTINAC.BASE}` | `1.3.6.1.4.1.16856` | FortiNAC enterprise OID prefix. Adjust if your environment resolves differently. |
| `{$FORTINAC.NODATA}` | `15m` | Alert if no SNMP data is received for this duration. |
| `{$FORTINAC.LIC.WARN}` | `80` | Warning threshold for concurrent license usage percent. |
| `{$FORTINAC.LIC.HIGH}` | `90` | High threshold for concurrent license usage percent. |
| `{$FORTINAC.MEM.FREE.MIN}` | `10` | Minimum acceptable free memory percent. |
| `{$FORTINAC.SWAP.FREE.MIN}` | `10` | Minimum acceptable free swap percent. |
| `{$FORTINAC.ROGUE.MAX}` | `0` | Maximum allowed rogue client count. |
| `{$FORTINAC.ATRISK.MAX}` | `0` | Maximum allowed at-risk client count. |
| `{$FORTINAC.DISABLED.MAX}` | `0` | Maximum allowed disabled client count. |

---

## Calculated Items

- **Concurrent license usage (%)**  
  `100 * used / max`

- **Memory free (%)**  
  `100 * free / total`

- **Swap free (%)**  
  `100 * free / total`

- **Disk free (%)** *(disabled by default)*  
  `100 * free / total`

> Note: Memory/swap/disk totals and free values are multiplied by **1024** in preprocessing (device reports in KB).

---

## Triggers (Included)

| Trigger | Severity | Notes |
|---|---:|---|
| FortiNAC: No SNMP data for `{$FORTINAC.NODATA}` | AVERAGE | Uses `nodata()` on uptime item. |
| FortiNAC: Rogue client count is above threshold | WARNING | `rogue.total > {$FORTINAC.ROGUE.MAX}` |
| FortiNAC: At-risk client count is above threshold | WARNING | `atrisk.total > {$FORTINAC.ATRISK.MAX}` |
| FortiNAC: Disabled client count is above threshold | WARNING | `disabled.total > {$FORTINAC.DISABLED.MAX}` |
| FortiNAC: Concurrent license usage high (warn) | WARNING | `usage >= {$FORTINAC.LIC.WARN}` and `< {$FORTINAC.LIC.HIGH}` |
| FortiNAC: Concurrent license usage very high | HIGH | `usage >= {$FORTINAC.LIC.HIGH}` |
| FortiNAC: Low free memory | HIGH | `avg(mem_free_pct,5m) < {$FORTINAC.MEM.FREE.MIN}` |
| FortiNAC: Low free swap | HIGH | `avg(swap_free_pct,5m) < {$FORTINAC.SWAP.FREE.MIN}` |

---

## Validation & Troubleshooting

### Validate SNMP Connectivity (from Zabbix server/proxy)
~~~bash
# Basic system checks
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.2.1.1.5.0
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.2.1.1.3.0
~~~

### Validate FortiNAC OID Subtree
~~~bash
# FortiNAC base subtree (example default base)
snmpwalk -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.4.1.16856 | head -n 50
~~~

### Spot-check Key Metrics
~~~bash
# License (example default base)
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.4.1.16856.1.4.2.1.0
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.4.1.16856.1.4.2.2.0

# Rogue / at-risk / disabled totals
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.4.1.16856.1.4.3.5.0
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.4.1.16856.1.4.3.11.0
snmpget -v2c -c <COMMUNITY> <FORTINAC_IP> 1.3.6.1.4.1.16856.1.4.3.8.0
~~~

### If you see “No SNMP data…”
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP credentials (community or SNMPv3 auth/priv).
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether FortiNAC restricts SNMP by source IP.

### If disk values are always 0
This is a known behavior on some versions/models. Keep disk items disabled unless you confirm correct values via `snmpget`.

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
- Adding more FortiNAC health metrics (services, processes, DB health if available)
- Extending device/client taxonomy counters
- Macro-driven trigger tuning and additional dashboards
- Documentation improvements and validated OID mappings

Please open an issue with:
- FortiNAC version/model
- Zabbix version
- Sanitized `snmpwalk` excerpts for relevant OIDs
- Expected vs. actual behavior

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by Fortinet.
