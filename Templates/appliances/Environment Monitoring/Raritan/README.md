# Raritan Environmental by SNMP (Zabbix 7.0 Template)

This repository provides a Zabbix template to monitor **Raritan EMX/SRC-style environmental monitoring devices** via **SNMP**, using numeric OIDs from the official **EMD-MIB** (no MIB import required in Zabbix).

- Template name: **Raritan Environmental by SNMP**
- Zabbix export: **7.0**
- File: `Raritan Environmental by SNMP.yaml`
- Vendor enterprise OID: `1.3.6.1.4.1.13742` (Raritan)

> Community template — not affiliated with, endorsed by, or sponsored by Raritan.

---

## What’s Included

## Availability & Base System
- ICMP ping / loss / response time
- SNMP agent availability (Zabbix internal item)
- Standard system fields: sysName / sysDescr / sysLocation / sysContact
- Uptime (sysUpTime)

## Device Inventory
- Device name
- Firmware version
- Hardware version
- External sensor count
- Managed external sensor count

## Peripheral Package Inventory (LLD)
Discovers connected peripheral packages/modules and collects:
- Package model
- Package firmware

## Environmental Sensors (LLD)
Discovers sensors from the Raritan environmental sensor table and monitors:

**Analog sensors**
- Temperature (type `10`)
- Humidity (type `11`)
- Airflow (type `12`)
- Air pressure (type `13`)

**Discrete sensors / alarms**
- Vibration (type `16`)
- Water leak (type `17`)
- Smoke (type `18`)
- Tamper (type `44`)
- Motion (type `45`)

> The actual sensor set depends on connected DX/DX2 / SmartSensor hardware and device firmware.

---

## How It Works

## Sensor Value Normalization (Decimal Digits)
Raritan sensors commonly return:
- a raw integer value, and
- a `decimal digits` field

This template automatically scales values using JavaScript preprocessing:

`scaled_value = raw_value / (10 ^ digits)`

This ensures Zabbix values match the device UI without manual multipliers.

## Alarm Strategy
The template primarily relies on:
- **device-reported sensor state** (warning/critical/fault), and
- for temperature/humidity, also includes **generic value thresholds** as starter rules.

For best results, configure thresholds/alarms on the **Raritan side** and let Zabbix alert on reported state.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Raritan EMX/SRC reachable via SNMP (UDP/161)
- Zabbix host must have an **SNMP interface** configured (SNMPv2c or SNMPv3)
- Optional (recommended): ICMP allowed from Zabbix to the device

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Raritan Environmental by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (device IP/DNS + port 161)
- Configure SNMP credentials (v2c community or SNMPv3 user/auth/priv)
- Link template: **Raritan Environmental by SNMP**

### 3) (Recommended) Define ICMP Threshold Macros
This template includes ICMP triggers that reference the macros below. Define them at host or global level:

- `{$ICMP_LOSS_WARN}` (example: `20`)
- `{$ICMP_RESPONSE_TIME_WARN}` (example: `0.15`)

---

## Macros

Template macros (included):
| Macro | Default | Description |
|---|---:|---|
| `{$RARITAN.ENV.POLL}` | `5m` | Default polling interval for live measurements. |
| `{$RARITAN.ENV.DISCOVERY}` | `1h` | Discovery interval for sensors and packages. |
| `{$RARITAN.ENV.INVENTORY}` | `1d` | Refresh interval for low-change inventory data. |
| `{$SNMP.TIMEOUT}` | `5m` | Window used by the “No SNMP data collection” trigger. |

Recommended (define in host/global if missing):
| Macro | Example | Description |
|---|---:|---|
| `{$ICMP_LOSS_WARN}` | `20` | ICMP packet loss warning threshold (%). |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP response time warning threshold (seconds). |

---

## Low-Level Discovery (LLD) Coverage

## Peripheral packages
- Rule: `raritan.env.package.discovery`
- Discovers `{#PKGMODEL}` and `{#PKGFW}`
- Items:
  - Package model (TEXT)
  - Package firmware (TEXT)

## Analog sensors (value + state)
Each analog sensor discovery creates:
- Name
- Type
- Decimal digits
- **State** (value map: *Raritan sensor state*)
- **Value** (scaled using digits)

Discovery rules:
- `raritan.env.temperature.discovery` (type `10`)
- `raritan.env.humidity.discovery` (type `11`)
- `raritan.env.airflow.discovery` (type `12`)
- `raritan.env.airpressure.discovery` (type `13`)

## Discrete sensors (state-based)
Each discrete sensor discovery creates:
- Name
- Type
- **State** (value map: *Raritan sensor state*)

Discovery rules:
- `raritan.env.vibration.discovery` (type `16`)
- `raritan.env.water.discovery` (type `17`)
- `raritan.env.smoke.discovery` (type `18`)
- `raritan.env.tamper.discovery` (type `44`)
- `raritan.env.motion.discovery` (type `45`)

---

## Triggers (Included)

## Availability
- **Unavailable by ICMP ping** (DISASTER): last 3 pings failed
- **High ICMP ping loss** (WARNING): `min(loss,5m) > {$ICMP_LOSS_WARN}` and `< 100`
- **High ICMP response time** (WARNING): `avg(rtt,5m) > {$ICMP_RESPONSE_TIME_WARN}`
- **No SNMP data collection** (DISASTER): SNMP unavailable for `{$SNMP.TIMEOUT}`

## State-based sensor alerts (LLD trigger prototypes)
For Temperature / Humidity / Airflow / Air pressure:
- **Warning state** triggers when the sensor state indicates warning (e.g., below/above warning or “warning”).
- **Critical state** triggers when the sensor state indicates critical/fault (e.g., critical/fault/fail).

For Water leak / Smoke / Motion / Vibration / Tamper:
- Alarm triggers fire based on state transitions indicating detection/alarm.

> Note: Severity levels in this starter template may not match your internal incident policy. Adjust priorities after import as needed.

## Value-threshold alerts (starter defaults)
Included only for **Temperature** and **Humidity**:

**Temperature**
- Lower critical: `<= 15` (5m)
- Lower warning: `<= 18` (5m)
- Upper warning: `>= 25` (5m)
- Upper critical: `>= 28` (5m)

**Humidity**
- Lower critical: `<= 10` (5m)
- Lower warning: `<= 25` (5m)
- Upper warning: `>= 80` (5m)
- Upper critical: `>= 90` (5m)

> Recommendation: Treat these as baseline examples and tune to your site/environment (data center vs office vs warehouse).

---

## Value Maps (Included)

- **Raritan sensor state**: maps state codes to human-readable conditions (normal/warning/critical/fault/detected/alarmed/etc.)
- **Service state**: used by ICMP ping item
- **zabbix.host.available**: used by SNMP availability

---

## Validation & Troubleshooting

### Validate SNMP connectivity
~~~bash
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.2.1.1
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.13742 | head -n 50
~~~

### Spot-check environmental sensor tables (EMD-MIB)
~~~bash
# Sensor configuration table (name/type/digits)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.13742.8.1.2.1.1

# Sensor readings/state table (state/value)
snmpwalk -v2c -c <COMMUNITY> <DEVICE_IP> 1.3.6.1.4.1.13742.8.2.1.1.1
~~~

### If you see “No SNMP data collection”
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP community/v3 credentials.
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether the device restricts SNMP by source IP.

### If sensors are not discovered
- Confirm the device actually reports sensors for the relevant types (10/11/12/13/16/17/18/44/45).
- Verify that connected sensor modules are recognized by the controller and exposed via SNMP.
- Increase discovery interval temporarily (or run “Check now”) after installing new sensors.

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
- Additional supported sensor types and mappings
- Improved state-to-severity logic
- Better default thresholds per sensor class
- Documentation improvements and tested examples

Please open an issue with:
- Device model and firmware version
- Zabbix version
- Sanitized `snmpwalk` excerpts for the relevant OIDs
- Expected vs. actual behavior (include preprocessing errors if any)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Raritan.
