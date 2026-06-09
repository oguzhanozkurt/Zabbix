# Raritan PDU by SNMP (Zabbix 7.0 Template)

This repository provides a Zabbix template to monitor **Raritan intelligent PDUs** via **SNMP**, using numeric OIDs from the vendor **PDU2-MIB** (no MIB import required in Zabbix).

- Template name: **Raritan PDU by SNMP**
- Zabbix export: **7.0**
- File: `Raritan PDU by SNMP.yaml`
- Vendor enterprise OID: `1.3.6.1.4.1.13742` (Raritan)

> Note: This is a community template and is not an official Raritan release.

---

## What’s Included

## Inventory (PDU Unit Discovery)
Discovers each PDU unit and collects low-change inventory data:
- Manufacturer, model, serial number, unit name
- Counts: inlet count, outlet count, external sensor count, managed sensor count

## Outlet Monitoring
Discovers outlets and collects:
- Outlet label and outlet name (inventory)
- Outlet **switching state** (on/off/open/closed depending on device)
- Outlet **switchable** capability (yes/no)

## Electrical Measurements
## Inlet measurements (LLD)
- **Current** (A)
- **Voltage** (V)
- **Active power** (W)
- Per-metric **sensor state** (warning/critical) based on device-reported state

## Outlet measurements (LLD)
- **Current** (A)
- **Active power** (W)
- Per-metric **sensor state** (warning/critical) based on device-reported state

## External Sensors (LLD)
Automatically discovers external sensors and monitors:
- **Temperature**
- **Humidity**
- **Airflow**
- **Air pressure**
- **Water leak** (state/alarm)
- **Smoke** (state/alarm)

## Automatic Scaling (Decimal Digits)
Many Raritan sensors report values as integer + “decimal digits”.  
This template automatically normalizes values using JavaScript preprocessing:

- `scaled_value = raw_value / (10 ^ digits)`

So the displayed values match the device UI without manual multipliers.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Raritan PDU reachable via SNMP (UDP/161)
- Zabbix host must have an **SNMP interface** configured (SNMPv2c or SNMPv3)
- Network access: Zabbix → PDU **UDP/161**
- Optional: ICMP checks are not included in this template (SNMP-only).

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Raritan PDU by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (PDU IP/DNS + port 161)
- Configure SNMP credentials (v2c community or v3 user/auth/priv)
- Link template: **Raritan PDU by SNMP**

### 3) Review Macros (Polling/Discovery Cadence)
The template uses these macros to control polling:

| Macro | Default | Description |
|------|---:|-------------|
| `{$RARITAN.PDU.POLL}` | `5m` | Default polling interval for live measurements (values/states). |
| `{$RARITAN.PDU.DISCOVERY}` | `1h` | Discovery interval for outlets and sensors. |
| `{$RARITAN.PDU.INVENTORY}` | `1d` | Refresh interval for low-change inventory data. |

---

## Low-Level Discovery (LLD) Coverage

### PDU Unit Discovery
- Key: `raritan.pdu.unit.discovery`
- Macros:
  - `{#PDUNAME}`, `{#MODEL}`, `{#SERIAL}`, `{#SNMPINDEX}`

### Outlet Discovery
- Key: `raritan.pdu.outlet.discovery`
- Macros:
  - `{#OUTLETLABEL}`, `{#OUTLETNAME}`, `{#SWITCHABLE}`, `{#SNMPINDEX}`

### Inlet Measurements (per inlet sensor index)
- Current: `raritan.pdu.inlet.current.discovery`
- Voltage: `raritan.pdu.inlet.voltage.discovery`
- Active power: `raritan.pdu.inlet.power.discovery`
- Macros:
  - `{#TYPE}`, `{#DIGITS}`, `{#SNMPINDEX}`

### Outlet Measurements (per outlet sensor index)
- Current: `raritan.pdu.outlet.current.discovery`
- Active power: `raritan.pdu.outlet.power.discovery`
- Macros:
  - `{#OUTLETLABEL}`, `{#TYPE}`, `{#DIGITS}`, `{#SNMPINDEX}`

### External Sensors (per sensor index; filtered by sensor type)
- Temperature: `raritan.pdu.ext.temperature.discovery` (type `10`)
- Humidity: `raritan.pdu.ext.humidity.discovery` (type `11`)
- Airflow: `raritan.pdu.ext.airflow.discovery` (type `12`)
- Air pressure: `raritan.pdu.ext.airpressure.discovery` (type `13`)
- Water leak: `raritan.pdu.ext.water.discovery` (type `17`)
- Smoke: `raritan.pdu.ext.smoke.discovery` (type `18`)
- Macros:
  - `{#NAME}`, `{#TYPE}`, `{#DIGITS}`, `{#SNMPINDEX}`

> Sensor type filtering avoids mixing different sensor classes from the same underlying Raritan sensor table.

---

## Alerts (Included)

This template is designed around **device-reported sensor states**, not hardcoded thresholds.  
In practice, you should configure thresholds/alarms on the Raritan side; Zabbix will alert when the PDU reports warning/critical state.

### State-based trigger prototypes (common pattern)
For inlet/outlet measurements and external analog sensors:
- **Warning** trigger when state indicates “below lower warning / above upper warning / warning”
- **High** trigger when state indicates “below lower critical / above upper critical / fail / fault / critical”

### Discrete safety alarms
- **Water leak alarm** (HIGH) when state indicates detection/alarm
- **Smoke alarm** (HIGH) when state indicates detection/alarm

---

## Value Maps (Included)

### Raritan sensor state
Maps state codes to human-readable status, including (examples):
- `4` = normal
- `3` = below lower warning
- `2` = below lower critical
- `5` = above upper warning
- `6` = above upper critical
- `9` = detected
- `11` = alarmed
- `26` = fault
- `27` = warning
- `28` = critical
- `-1` = unavailable

### Raritan switchable
- `0` = no
- `1` = yes

---

## Validation & Troubleshooting

### Validate SNMP connectivity and base subtree
~~~bash
# Basic SNMP system info
snmpwalk -v2c -c <COMMUNITY> <PDU_IP> 1.3.6.1.2.1.1

# Raritan enterprise subtree
snmpwalk -v2c -c <COMMUNITY> <PDU_IP> 1.3.6.1.4.1.13742 | head -n 50
~~~

### Validate key tables (spot checks)
~~~bash
# PDU units / inventory
snmpwalk -v2c -c <COMMUNITY> <PDU_IP> 1.3.6.1.4.1.13742.6.3.2

# Outlets
snmpwalk -v2c -c <COMMUNITY> <PDU_IP> 1.3.6.1.4.1.13742.6.3.5

# External sensors
snmpwalk -v2c -c <COMMUNITY> <PDU_IP> 1.3.6.1.4.1.13742.6.3.6
snmpwalk -v2c -c <COMMUNITY> <PDU_IP> 1.3.6.1.4.1.13742.6.5.5
~~~

### If items are unsupported
- Confirm the PDU firmware exposes the expected PDU2-MIB tables (sensor coverage varies by model and installed sensors).
- Confirm SNMP version/credentials and any source-IP ACL on the PDU.
- If you see unexpected scaling, verify the `digits` value; the template already normalizes using digits.

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
- Adding more PDU2-MIB coverage (energy counters, environmental alarms, per-outlet control where appropriate)
- Improving state-to-severity mapping (if your firmware uses additional state codes)
- Documentation improvements and tested examples

Please open an issue with:
- PDU model and firmware version
- Zabbix version
- Sanitized `snmpwalk` excerpts for the relevant OIDs
- Expected vs. actual behavior (including any preprocessing errors)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Raritan.
