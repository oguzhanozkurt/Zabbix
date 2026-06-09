# HWg Poseidon2 3268 by SNMP (Zabbix Template)

This repository provides a Zabbix template to monitor the **HW group HWg-Poseidon2 3268** environment monitoring device via **SNMP**.

- Template name: **HWg Poseidon2 3268 by SNMP**
- Zabbix export: **7.0**
- File: `hwg_poseidon2_3268_snmp_zabbix_7_template_v1_2.yaml`
- MIB: **POSEIDON-MIB 2.10** (base OID: `1.3.6.1.4.1.21796.3.3`)

> Community template — not affiliated with HW group.

---

## What’s Included

## Availability & Baseline Health
- ICMP ping / loss / response time
- SNMP agent availability (Zabbix internal item)
- Basic inventory (sysName/sysDescr/sysObjectID) and device MAC address

## Sensors (LLD from `sensTable`)
Automatic discovery of sensors including:
- State (`sensState`) and string state mapping
- Value (`sensValue`) + raw value
- Unit code + unit string
- Sensor ID, port ID
- Configured limits (min/max) and hysteresis (from device setup)
- Alarm flags

**Important scaling note:** `sensValue`, configured limits, and hysteresis are reported as **decimal × 10** by the device; the template applies a **0.1 multiplier**.  
This ensures values match the device UI. (Example: “235” becomes “23.5”.)

## Digital Inputs (LLD from `inpTable`)
- Input value
- Alarm setup and alarm state
- Pulse counter
- Alarm trigger prototype per input

## Relay Outputs (LLD from `outTable`)
- Output value (ON/OFF)
- Output type and mode
- Optional “Output is ON” trigger (disabled by default via macro)

## Alarms
- Active alarm count / presence
- Dynamic active alarm table discovery (description + sensor/input + time)

## Device Logs (Operational Visibility)
- Log record count
- Log time remaining
- Log period
- Log I/O enabled
- Configured display unit type

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- HWg Poseidon2 3268 reachable via SNMP (UDP/161)
- Zabbix host must have an **SNMP interface** configured (SNMPv2c or SNMPv3)
- Optional (recommended): ICMP allowed from Zabbix to the device

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `hwg_poseidon2_3268_snmp_zabbix_7_template_v1_2.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (device IP/DNS + port 161)
- Configure SNMP credentials (community for v2c or user/auth/priv for v3)
- Link template: **HWg Poseidon2 3268 by SNMP**

### 3) (Optional) Enable Configured-Limit Alerts Per Sensor
Configured-limit triggers are **disabled by default** to avoid false positives when limits are not configured on the device.
To enable for specific sensors, create context macros at **host level**, for example:

- `{$POSEIDON.SENSOR.LIMIT.ALERT:"Temperature"} = 1`
- `{$POSEIDON.SENSOR.LIMIT.ALERT:"Humidity"} = 1`

### 4) (Optional) Enable “Relay Output ON” Alerts Per Output
Relay “Output is ON” alerts are **disabled by default**.
To enable for a specific output, set:

- `{$POSEIDON.OUTPUT.ON.ALERT:"Relay 1"} = 1`

---

## Macros

| Macro | Default | Description |
|------|---------|-------------|
| `{$SNMP.TIMEOUT}` | `5m` | Time window used by SNMP availability trigger |
| `{$ICMP_LOSS_WARN}` | `20` | ICMP loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP response time warning threshold (seconds) |
| `{$POSEIDON.SENSOR.LIMIT.ALERT}` | `0` | Default control for configured-limit alerts (use context macros per sensor name) |
| `{$POSEIDON.OUTPUT.ON.ALERT}` | `0` | Default control for relay output ON alerts (use context macros per output name) |

---

## Low-Level Discovery (LLD)

### Sensor discovery
- Rule key: `hwg.poseidon.sensor.discovery`
- Discovers `{#SENSOR.NAME}`, `{#SENSOR.STATE}`, `{#SENSOR.UNIT}`, `{#SENSOR.UNITSTRING}`, `{#SENSOR.ID}` and more (sensTable + setup OIDs)
- Creates item prototypes:
  - State, Value, Raw value, String value
  - Unit code/string, Sensor ID, Port ID, Alarm flags
  - Configured low/high limits, hysteresis

Includes a graph prototype:
- **Sensor {#SENSOR.NAME}: Value** (value + configured min/max)

### Digital input discovery
- Rule key: `hwg.poseidon.input.discovery`
- Discovers `{#INPUT.NAME}` plus alarm setup/state metadata
- Creates item prototypes: value, alarm setup, alarm state, pulse counter

### Relay output discovery
- Rule key: `hwg.poseidon.output.discovery`
- Discovers `{#OUTPUT.NAME}`
- Creates item prototypes: value (ON/OFF), type, mode

### Active alarm table discovery
- Rule key: `hwg.poseidon.alarm.discovery`
- Polls frequently and discovers active alarm rows
- Creates item prototypes: alarm description (mapped), sensor/input name, alarm time

---

## Triggers (Included)

## Connectivity / Availability
- **Unavailable by ICMP ping** (HIGH)
- **High ICMP ping loss** (WARNING)
- **High ICMP response time** (WARNING)
- **No SNMP data collection** (WARNING)
- **Active alarm present on device** (AVERAGE)

## Sensors (Trigger Prototypes)
- **Sensor alarm** (HIGH) when `sensState=3`
- **Warning alarm state** (WARNING) when `sensState=2`  
  (means alarm condition exists, but may not be enabled or delay has not elapsed)
- **Invalid sensor** (AVERAGE) when `sensState=0`
- **Value below configured low limit** (WARNING) — gated by `{$POSEIDON.SENSOR.LIMIT.ALERT:"{#SENSOR.NAME}"}=1` (manual close)
- **Value above configured high limit** (WARNING) — gated by `{$POSEIDON.SENSOR.LIMIT.ALERT:"{#SENSOR.NAME}"}=1` (manual close)

## Digital Inputs (Trigger Prototypes)
- **Digital input alarm** (AVERAGE) when alarm state indicates configured alarm condition

## Relay Outputs (Trigger Prototypes)
- **Relay output is ON** (INFO) — gated by `{$POSEIDON.OUTPUT.ON.ALERT:"{#OUTPUT.NAME}"}=1` (manual close)

---

## Validation & Troubleshooting

### Validate SNMP Reachability
~~~bash
snmpget  -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.2.1.1.5.0
snmpwalk -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.4.1.21796.3.3 | head -n 50
~~~

### Validate Key Tables
~~~bash
# Sensors (sensTable)
snmpwalk -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.4.1.21796.3.3.3.1

# Inputs (inpTable)
snmpwalk -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.4.1.21796.3.3.1.1

# Outputs (outTable)
snmpwalk -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.4.1.21796.3.3.2.1

# Alarms
snmpget  -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.4.1.21796.3.3.50.1.0
snmpwalk -v2c -c <COMMUNITY> <POSEIDON_IP> 1.3.6.1.4.1.21796.3.3.50.2
~~~

### If you see “No SNMP data collection”
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP community/v3 credentials.
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether the device restricts SNMP by source IP.

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
- Additional value maps for alarm descriptions (if your firmware exposes new codes)
- Extended alerting models (e.g., thresholds per sensor type)
- Documentation improvements and tested examples

Please include:
- Device firmware version
- Zabbix version
- Sanitized `snmpwalk` excerpts (relevant OIDs)
- Expected vs. actual behavior (include preprocessing errors if any)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
