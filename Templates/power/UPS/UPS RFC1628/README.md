# UPS Monitoring (RFC1628 UPS-MIB) by SNMP — Zabbix 7.0 Template

This repository provides a Zabbix 7.0 SNMP template based on **RFC1628 UPS-MIB** (`1.3.6.1.2.1.33`) to monitor UPS devices in a vendor-neutral way.

- Template name: **Template UPS RFC1628 SNMP**
- Zabbix export: **7.0**
- File: `template_ups_rfc1628_snmp_zabbix_7_0.yaml`
- Protocol: **SNMP** (UPS-MIB / RFC1628)

> Community template — not affiliated with any UPS vendor.

---

## Key Capabilities

## Availability
- SNMP agent availability check (Zabbix internal item)
- Alert on SNMP unavailability using a configurable timeout window

## Identification / Inventory
- Manufacturer, model
- UPS software version and agent software version
- UPS name and attached devices

## Battery Monitoring
- Battery status (normal/low/depleted/unknown)
- Seconds on battery (detects running on battery)
- Estimated runtime (minutes)
- Battery charge (%)
- Battery voltage/current/temperature

## Power Lines (LLD)
Discovers and monitors multi-line UPS models:
- **Input lines** (frequency, voltage, current, true power)
- **Output lines** (voltage, current, true power, percent load)
- **Bypass lines** (voltage, current, true power) — where supported

## Active Alarms (LLD)
- Detects whether alarms are present
- Discovers active alarm table entries (description + time)

## Diagnostics & Configuration
- Last self-test result summary + details
- Test start / elapsed time
- Configured input/output voltage and frequency
- Output VA rating / power rating
- Transfer points and low-battery time
- Audible alarm status

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- UPS device exposing **RFC1628 UPS-MIB** (`1.3.6.1.2.1.33`)
- Network access: Zabbix → UPS **UDP/161**
- Zabbix host must have an **SNMP interface** configured (SNMPv2c or SNMPv3)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `template_ups_rfc1628_snmp_zabbix_7_0.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (UPS IP/DNS + port 161)
- Configure SNMP credentials (community for v2c or user/auth/priv for v3)
- Link template: **Template UPS RFC1628 SNMP**

### 3) Review and Tune Macros
Adjust thresholds based on your operational requirements (see the next section).

---

## Macros

| Macro | Default | Description |
|------|---------|-------------|
| `{$SNMP.TIMEOUT}` | `5m` | Time window after which SNMP availability is considered unavailable |
| `{$UPS.ALARMS.MAX}` | `0` | Maximum acceptable number of active UPS alarms (0 triggers on any alarm) |
| `{$UPS.BATTERY.CHARGE.WARN}` | `30` | Warning threshold for battery charge (%) |
| `{$UPS.BATTERY.CHARGE.CRIT}` | `15` | Critical threshold for battery charge (%) |
| `{$UPS.BATTERY.RUNTIME.MIN.WARN}` | `10` | Warning threshold for estimated runtime (minutes) |
| `{$UPS.BATTERY.RUNTIME.MIN.CRIT}` | `5` | Critical threshold for estimated runtime (minutes) |
| `{$UPS.BATTERY.TEMP.WARN}` | `40` | Warning threshold for battery temperature (°C) |
| `{$UPS.BATTERY.TEMP.CRIT}` | `50` | Critical threshold for battery temperature (°C) |
| `{$UPS.OUTPUT.LOAD.WARN}` | `80` | Reserved for optional output load triggers (%) |
| `{$UPS.OUTPUT.LOAD.CRIT}` | `95` | Reserved for optional output load triggers (%) |

> Note: `{$UPS.OUTPUT.LOAD.*}` macros are provided for convenience. The current template collects output load per line, but does not include built-in triggers for it. You can add your own triggers using these macros.

---

## What’s Monitored (Summary)

## Identification (hourly)
- Manufacturer, model, UPS/agent software version
- UPS name, attached devices

## Battery (1 minute)
- Status (value map)
- Seconds on battery
- Runtime (minutes), charge (%)
- Voltage, current, temperature

## Input / Output / Bypass Lines (LLD, hourly discovery / 1 minute polling)
- Input lines: frequency (Hz), voltage (V), current (A), true power (W)
- Output lines: voltage (V), current (A), true power (W), load (%)
- Bypass lines: voltage (V), current (A), true power (W)

## Alarms (1 minute + alarm-table LLD)
- `upsAlarmsPresent` (0/1): whether any alarm exists
- Alarm table discovery (1 hour, lifetime 1 hour): description and time per alarm row

## Diagnostics & Configuration (mostly 5 min / 1 hour)
- Self-test summary + detail, start time, elapsed time
- Configured nominal input/output voltage and frequency
- Output VA/power ratings
- Low/high transfer points, low battery time
- Audible alarm status (value map)

---

## Low-Level Discovery (LLD)

### UPS input line discovery
- Key: `ups.input.discovery`
- Source: `upsInputTable`
- Items: frequency, voltage, current, true power (per line)

### UPS output line discovery
- Key: `ups.output.discovery`
- Source: `upsOutputTable`
- Items: voltage, current, true power, percent load (per line)

### UPS bypass line discovery
- Key: `ups.bypass.discovery`
- Source: `upsBypassTable`
- Items: voltage, current, true power (per line)
- If your UPS does not support bypass, you may disable this discovery rule.

### UPS alarm table discovery
- Key: `ups.alarm.discovery`
- Source: `upsAlarmTable`
- Items per alarm row: description, time
- Lifetime: 1 hour (alarm rows expire quickly after clearing)

---

## Triggers (Included)

### Availability
- **UPS: SNMP agent is unavailable** (HIGH)  
  Fires when SNMP availability is `0` for `{$SNMP.TIMEOUT}`.

### Battery
- **UPS: Battery is depleted** (DISASTER)
- **UPS: Battery is low** (HIGH)
- **UPS: Battery status is unknown** (WARNING)
- **UPS: Running on battery power** (HIGH) — seconds on battery > 0
- **UPS: Estimated runtime is critically low** (HIGH) — runtime < `{$UPS.BATTERY.RUNTIME.MIN.CRIT}` (and > 0)
- **UPS: Estimated runtime is low** (WARNING) — runtime < `{$UPS.BATTERY.RUNTIME.MIN.WARN}` (and > 0)
- **UPS: Battery charge is critically low** (HIGH) — charge < `{$UPS.BATTERY.CHARGE.CRIT}`
- **UPS: Battery charge is low** (WARNING) — charge < `{$UPS.BATTERY.CHARGE.WARN}`
- **UPS: Battery temperature is critically high** (HIGH) — min(temp, 5m) > `{$UPS.BATTERY.TEMP.CRIT}`
- **UPS: Battery temperature is high** (WARNING) — min(temp, 5m) > `{$UPS.BATTERY.TEMP.WARN}`

### Input / Output Source
- **UPS: Input entered an out-of-tolerance condition** (WARNING) — input bads counter increased
- **UPS: Output source is none** (DISASTER)
- **UPS: Output source is battery** (HIGH)
- **UPS: Output source is bypass** (AVERAGE)
- **UPS: Output source is booster or reducer** (WARNING)

### Alarms
- **UPS: Active alarm conditions present** (AVERAGE) — alarms present > `{$UPS.ALARMS.MAX}`

### Diagnostics
- **UPS: Last diagnostic test completed with error** (HIGH)
- **UPS: Last diagnostic test completed with warning** (WARNING)
- **UPS: Diagnostic test is in progress** (INFO)

---

## Value Maps (Included)

- **SNMP availability**: 0=not available, 1=available, 2=unknown
- **UPS battery status**: 1=unknown, 2=batteryNormal, 3=batteryLow, 4=batteryDepleted
- **UPS output source**: 1=other, 2=none, 3=normal, 4=bypass, 5=battery, 6=booster, 7=reducer
- **UPS test results summary**: donePass/doneWarning/doneError/aborted/inProgress/noTestsInitiated
- **UPS audible status**: disabled/enabled/muted

---

## Validation & Troubleshooting

### Validate SNMP and UPS-MIB availability
~~~bash
# Basic SNMP reachability
snmpget -v2c -c <COMMUNITY> <UPS_IP> 1.3.6.1.2.1.1.1.0

# UPS-MIB root (RFC1628)
snmpwalk -v2c -c <COMMUNITY> <UPS_IP> 1.3.6.1.2.1.33 | head -n 50
~~~

### Validate key UPS metrics
~~~bash
# Battery status / charge / runtime
snmpget -v2c -c <COMMUNITY> <UPS_IP> 1.3.6.1.2.1.33.1.2.1.0
snmpget -v2c -c <COMMUNITY> <UPS_IP> 1.3.6.1.2.1.33.1.2.4.0
snmpget -v2c -c <COMMUNITY> <UPS_IP> 1.3.6.1.2.1.33.1.2.3.0

# Output source
snmpget -v2c -c <COMMUNITY> <UPS_IP> 1.3.6.1.2.1.33.1.4.1.0
~~~

### Notes on scaling (device-specific)
RFC1628 defines some values in scaled units (e.g., deci-volts/deci-amps) depending on implementation.
This template stores the **raw values returned by the UPS**. If your device reports scaled values, add preprocessing multipliers on the relevant items to normalize units.

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
- Additional triggers (e.g., output load thresholds per phase)
- Improved scaling handling (vendor-specific multipliers)
- Extended diagnostics coverage
- Documentation improvements and tested examples

Please include:
- UPS vendor/model and firmware
- SNMP version and a sanitized `snmpwalk` excerpt from `1.3.6.1.2.1.33`
- Zabbix version
- Expected vs. actual behavior

---

## License

Licensed under the MIT License. See the LICENSE file for details.


## Trademarks

All product names and trademarks are property of their respective owners.
