# Template Ruijie Networks (Zabbix Template)

This repository provides a Zabbix template to monitor **Ruijie Networks** devices via **SNMP**.

- Template name: **Template Ruijie Networks**
- Zabbix export: **7.0**
- File: **Template Ruijie Networks.yaml**
- Vendor enterprise OID: **Ruijie (4881)**

> Note: This is a community template and is not an official Ruijie release.

---

## What’s Included

### Device Health & Utilization
- CPU utilization
- Memory utilization + total/used/free
- System temperature (°C)
- Fan status (value map)

### Inventory / Identification
- System model
- Software version
- Hardware version
- Serial number

### Automated Discovery (LLD)
- **Power supplies**: status + serial number
- **Temperature sensors**: status

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Target device: Ruijie device with SNMP enabled and accessible from Zabbix
- Network access: Zabbix → device **UDP/161**
- Zabbix host must have an **SNMP interface** configured

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Template Ruijie Networks.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (device IP/DNS + port 161)
- Configure SNMP credentials (v2c community or SNMPv3)
- Link template: **Template Ruijie Networks**

### 3) Review Thresholds (Macros)
Default trigger thresholds are provided as macros (see below). Adjust to match your environment.

---

## Macros

| Macro | Default | Description |
|------|---------|-------------|
| `{$CPU.UTIL.CRIT}` | `90` | CPU utilization critical threshold (%) |
| `{$MEMORY.UTIL.CRIT}` | `90` | Memory utilization critical threshold (%) |
| `{$TEMP.UTIL.CRIT}` | `65` | Temperature critical threshold (°C) |

---

## Value Maps (Included)

### Fan Status
- `1` = noexist  
- `2` = existnopower  
- `3` = existreadypower  
- `4` = normal  
- `5` = powerbutabnormal  
- `6` = unknown  
- `7` = linefail  

### Power Status
- `1` = noLink  
- `2` = linkAndNoPower  
- `3` = linkAndReadyForPower  
- `4` = linkAndPower  
- `5` = linkAndPowerAbnormal  

### Temperature Status
- `1` = tempNormal  
- `2` = tempWarning  

---

## Monitored Items (Summary)

### Utilization / Health
- **CPU Utilization**  
  Key: `cpu.utilization`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.36.1.1.10.0`  
  Unit: `%`

- **Memory Utilization**  
  Key: `memory.utilization`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.35.1.1.1.3.0`  
  Unit: `%`

- **Memory Total / Used / Free**  
  Keys: `memory.size`, `memory.used`, `memory.free`  
  OIDs:
  - Total: `...1.1.1.12.0`
  - Used:  `...1.1.1.13.0`
  - Free:  `...1.1.1.14.0`

- **System Temperature**  
  Key: `system.temperature`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.1.1.16.0`  
  Unit: `°C`

- **Fan Status**  
  Key: `fan1.status`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.1.1.21.1.2.0`  
  Value map: `Fan Status`

### Inventory
- **System Model**  
  Key: `system.model`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.1.1.26.0`

- **Software Version**  
  Key: `software.version`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.1.1.2.0`

- **Hardware Version**  
  Key: `hardware.version`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.1.1.1.0`

- **Serial Number**  
  Key: `serial.number`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.1.1.24.0`

---

## Low-Level Discovery (LLD)

### Power Discovery
- Rule name: `Power Discovery`
- Rule key: `power.discovery`
- Discovers:
  - `{#PSNAME}` (power supply name)
  - `{#SNMPINDEX}`

Item prototypes:
- `Power Supply [{#PSNAME}] Status`  
  Key: `PowerStatus.[{#SNMPINDEX}]`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.21.1.5.1.3.{#SNMPINDEX}`  
  Value map: `Power Status`

- `Power Supply [{#PSNAME}] Serial Number`  
  Key: `PowerSerialNo.[{#SNMPINDEX}]`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.21.1.5.1.5.{#SNMPINDEX}`

### Temperature Discovery
- Rule name: `Temperature Discovery`
- Rule key: `temperature.discovery`

Item prototypes:
- `Temperature [{#SNMPINDEX}] Status`  
  Key: `TemperatureStatus.[{#SNMPINDEX}]`  
  OID: `1.3.6.1.4.1.4881.1.1.10.2.21.1.4.1.3.{#SNMPINDEX}`  
  Value map: `Temperature Status`

---

## Triggers (Included)

- **High CPU utilization (over {$CPU.UTIL.CRIT}% for 15m)** (HIGH)  
  Problem: `min(cpu.utilization, 15m) > {$CPU.UTIL.CRIT}`  
  Recovery: `min(cpu.utilization, 5m) < {$CPU.UTIL.CRIT}`

- **High Memory utilization (over {$MEMORY.UTIL.CRIT}% for 15m)** (HIGH)  
  Problem: `min(memory.utilization, 15m) > {$MEMORY.UTIL.CRIT}`  
  Recovery: `min(memory.utilization, 5m) < {$MEMORY.UTIL.CRIT}`

- **High System Temperature (threshold {$TEMP.UTIL.CRIT} for 15m)** (HIGH)  
  Problem: `min(system.temperature, 15m) > {$TEMP.UTIL.CRIT}`  
  Recovery: `min(system.temperature, 5m) < {$TEMP.UTIL.CRIT}`

- **Fan status problem {ITEM.LASTVALUE}** (HIGH)  
  Problem: `last(fan1.status) <> 4`  
  Recovery: `last(fan1.status) = 4`

> Note: The template’s temperature trigger name may display a `%` symbol in some exports, but the threshold is **°C**.

---

## Validation & Troubleshooting

From your Zabbix server/proxy, validate SNMP reachability and OIDs:

~~~bash
# Basic SNMP system info (optional quick check)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.1

# Ruijie enterprise subtree (template-specific)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.4881.1.1.10.2

# Spot-check a few template OIDs
snmpget  -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.4881.1.1.10.2.36.1.1.10.0
snmpget  -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.4881.1.1.10.2.35.1.1.1.3.0
~~~

### If you see "No data" / "Timeout" in Zabbix
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP credentials (v2c community or SNMPv3 user/auth/priv).
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether the device restricts SNMP access by source IP.

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
- Adding more Ruijie health metrics (interfaces, PSU redundancy, detailed sensors)
- Value map improvements and additional enums
- Trigger tuning and threshold recommendations
- Documentation and validation examples

Please open an issue with:
- Device model and firmware version
- Zabbix version
- Sanitized `snmpwalk` output for relevant OIDs
- Expected vs. actual behavior
