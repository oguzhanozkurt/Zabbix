# Ruijie Reyee SNMP Unified Package (Zabbix 7.0)

This repository provides a **multi-template package** for monitoring **Ruijie Reyee** devices via **SNMP** with Zabbix **7.0**.

- Zabbix export: **7.0**
- File: `ruijie_reyee_snmp_zabbix_7_template_unified_package.yaml`

The package includes a **Unified** template (standard MIBs only) plus **optional modules** (PoE / AP WLAN / EST Bridge / PON) that should be linked **only when the target device exposes the corresponding OIDs**. :contentReference[oaicite:5]{index=5} :contentReference[oaicite:6]{index=6}

> Community template — not an official Ruijie release.

---

## Included Templates

| Template | Purpose | Link When… |
|---|---|---|
| **Template Ruijie Reyee SNMP Unified** | Baseline monitoring using **standard MIBs only** (system, interfaces, CPU, storage, ENTITY inventory) | Target is a Reyee switch exposing **Net-SNMP sysObjectID** `1.3.6.1.4.1.8072.3.2.10` (the package intentionally avoids the Ruijie private OID tree for the unified baseline). :contentReference[oaicite:7]{index=7} |
| **Template Ruijie Reyee SNMP PoE** | PoE monitoring using **POWER-ETHERNET-MIB** | Device is PoE-capable and exposes `1.3.6.1.2.1.105…` tables. :contentReference[oaicite:8]{index=8} |
| **Template Ruijie Reyee SNMP AP WLAN** | AP WLAN/radio telemetry (private MIB) | Device is an RG-RAP / RG-EW / AP WLAN model that exposes the **RUIJIE-REYEE-AP-WLAN-MIB** subtree. :contentReference[oaicite:9]{index=9} |
| **Template Ruijie Reyee SNMP EST Bridge** | EST/AirMetro wireless bridge monitoring (private MIB) | Device is a Reyee EST/AirMetro bridge exposing **RUIJIE-EST-WIRELESS-MIB** OIDs. :contentReference[oaicite:10]{index=10} |
| **Template Ruijie Reyee SNMP PON** | Elighten PON monitoring (private MIB) | Device exposes **RUIJIE-ELIGHTEN-PON-MIB** subtree; many non-PON models do not. :contentReference[oaicite:11]{index=11} |

---

## Design Notes (Why “Unified” avoids private OIDs)

The **Unified** template is deliberately built with **standard SNMP MIBs** only (SNMPv2-MIB, IF-MIB/HC, HOST-RESOURCES-MIB, ENTITY-MIB) and **does not use** the Ruijie private enterprise tree (`1.3.6.1.4.1.4881`) to maximize portability across Reyee Net-SNMP-based devices. :contentReference[oaicite:12]{index=12}

Additionally, HR device status checks are intentionally excluded because the target model can expose interface rows as `down`, causing false positives. :contentReference[oaicite:13]{index=13}

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- SNMP enabled on the target device (SNMPv2c or SNMPv3)
- Network access from Zabbix → device: **UDP/161**
- Zabbix host must have an **SNMP interface** configured

---

## Quick Start

### 1) Import the Package
Zabbix UI → **Data collection → Templates → Import**  
Import: `ruijie_reyee_snmp_zabbix_7_template_unified_package.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (device IP/DNS + port)
- Configure SNMP credentials (community or SNMPv3)
- Link templates based on your device type:

Recommended linking:
- Reyee switch (baseline): **Template Ruijie Reyee SNMP Unified** :contentReference[oaicite:14]{index=14}  
- PoE switch: **Unified** + **PoE** :contentReference[oaicite:15]{index=15}  
- AP WLAN: **Unified** (optional) + **AP WLAN** (required for radio metrics) :contentReference[oaicite:16]{index=16}  
- EST/AirMetro bridge: **EST Bridge** :contentReference[oaicite:17]{index=17}  
- PON device: **PON** :contentReference[oaicite:18]{index=18}  

---

## What the Unified Template Monitors

### System (SNMPv2-MIB / HOST-RESOURCES-MIB)
- sysDescr / sysName / sysLocation / sysObjectID
- sysUpTime (converted to seconds)
- Physical memory total (`hrMemorySize`, converted to bytes)
- Running processes count (`hrSystemProcesses`) :contentReference[oaicite:19]{index=19}

### Inventory (ENTITY-MIB) — LLD
- Physical entity discovery (class, description, firmware/software/hardware revision, serial, manufacturer, model, FRU flag)
- Informational triggers on firmware/software revision changes :contentReference[oaicite:20]{index=20}

### Network Interfaces (IF-MIB / IF-MIB HC) — LLD
- Admin/oper status, ifDescr/ifAlias, ifType
- In/Out traffic (HC counters → bps)
- Discards/errors (as per-second rates)
- Link down trigger when admin is up but oper is not up
- Inbound/outbound errors detected triggers :contentReference[oaicite:21]{index=21}

### CPU (HOST-RESOURCES-MIB) — LLD
- CPU utilization per processor (`hrProcessorLoad`)
- High utilization trigger using `{$REYEE.CPU.UTIL.MAX}` :contentReference[oaicite:22]{index=22}

### Storage (HOST-RESOURCES-MIB) — LLD + calculated
- Discovers selected storage/memory rows via regex filters
- Calculates size/used bytes using allocation units
- Calculates used percentage
- High utilization trigger using `{$REYEE.STORAGE.UTIL.MAX}` :contentReference[oaicite:23]{index=23}

---

## Optional Modules (Highlights)

### PoE Module (POWER-ETHERNET-MIB)
- Main PSE: nominal power, operational status, consumption
- Per-port discovery: detection status, power class, counters (MPS absent, invalid signature, etc.)
- Fault detection trigger based on detection status values :contentReference[oaicite:24]{index=24}

### AP WLAN Module (Private OIDs)
- Radio telemetry for 2.4G / 5G / (if present) 6G:
  - Channel, power, bandwidth, frequency
  - RX/TX traffic (rate) :contentReference[oaicite:25]{index=25} :contentReference[oaicite:26]{index=26}

### EST Bridge Module (Private OIDs)
- Bridge role, associated device count
- Associated device discovery (MAC / serial / host)
- Link-level metrics (RSSI, channel utilization, channel/frequencies)
- Triggers:
  - Weak RSSI (threshold macro)
  - High channel utilization (threshold macro) :contentReference[oaicite:27]{index=27}

### PON Module (Private OIDs)
- Device type, interface count
- PON interface discovery and per-interface monitoring
- Use only where the PON subtree is actually exposed (many models won’t expose it). :contentReference[oaicite:28]{index=28}

---

## Macros

### Unified (baseline)
| Macro | Default | Description |
|---|---:|---|
| `{$REYEE.CPU.UTIL.MAX}` | `85` | CPU utilization threshold (%) for per-CPU triggers. :contentReference[oaicite:29]{index=29} |
| `{$REYEE.STORAGE.UTIL.MAX}` | `85` | Storage/memory utilization threshold (%) for discovered hrStorage rows. :contentReference[oaicite:30]{index=30} |
| `{$REYEE.STORAGE.MATCHES}` | `^(Physical memory|/tmp|/overlay)$` | Include-list regex for hrStorage discovery rows. :contentReference[oaicite:31]{index=31} |
| `{$REYEE.STORAGE.NOT_MATCHES}` | *(regex)* | Exclude-list regex to avoid derived memory rows, tmpfs/device rows, firmware transfer paths. :contentReference[oaicite:32]{index=32} |

### EST Bridge (optional)
| Macro | Default | Description |
|---|---:|---|
| `{$RUIJIE.EST.RSSI.MIN}` | `-75` | Minimum acceptable RSSI (dBm) for bridge links. :contentReference[oaicite:33]{index=33} |
| `{$RUIJIE.EST.CHANNEL.UTIL.MAX}` | `80` | Maximum acceptable channel utilization (%). :contentReference[oaicite:34]{index=34} |

---

## Validation & Troubleshooting

### Verify sysObjectID (recommended for “Unified” targeting)
~~~bash
snmpget -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.1.2.0
~~~
If the device reports `1.3.6.1.4.1.8072.3.2.10`, it matches the package’s intended Net-SNMP-based baseline. :contentReference[oaicite:35]{index=35}

### Validate core SNMP reachability
~~~bash
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.1
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.2.2
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.31.1.1
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.25
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.47.1.1
~~~

### Validate optional module OIDs (only if you link them)
~~~bash
# PoE (POWER-ETHERNET-MIB)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.105

# AP WLAN (private)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.4881.1.1.10.2.196

# EST Bridge (private)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.4881.1.1.10.2.195

# PON (private)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.4881.1.1.10.2.194
~~~

### If items show as unsupported / no SNMP data
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP version and credentials (community or v3 auth/priv).
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether the device restricts SNMP by source IP.

---

## Security Notes

SNMPv2c uses community strings in plaintext. Reduce exposure by applying:
- Source IP allow-lists
- Network segmentation
- Firewall policies

If you require SNMPv3, you can adapt the host SNMP interface settings accordingly (the OIDs remain the same).

---

## Contributing

Contributions are welcome, including:
- Additional interface filters and trigger tuning
- Expanded inventory coverage (ENTITY-MIB)
- Enhancements to optional modules (PoE/AP/EST/PON) with tested OIDs
- Documentation and validation examples

Please open an issue with:
- Device model + firmware
- Zabbix version
- Sanitized `snmpwalk` output for relevant OIDs
- Expected vs. actual behavior

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by Ruijie.
