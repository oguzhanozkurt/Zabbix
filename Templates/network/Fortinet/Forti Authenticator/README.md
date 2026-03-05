# Forti Authenticator by SNMP (Zabbix Template)

This repository provides a Zabbix template to monitor **FortiAuthenticator** appliances via **SNMP**.

- Template name: **Forti Authenticator by SNMP**
- Zabbix export: **6.0**
- File: **Forti Authenticator by SNMP.yaml**
- Vendor enterprise OID: **12356.113**

> Note: This is a community template and is not an official Fortinet release.

---

## What’s Included

### Availability & Connectivity
- ICMP ping, packet loss, and response time
- SNMP agent availability (Zabbix internal check)

### System Information
- System name
- System description
- System location
- System contact details
- System model
- System version
- Serial number
- System uptime

### Appliance Health
- CPU usage
- Memory usage
- Log disk usage
- RAID status
- HA status

### Authentication & Service Counters
- Authentication events and failures
- LDAP logins and failures
- RADIUS logins, failures, and accounting
- RADIUS proxy in/out totals

### Capacity / License-Related Metrics
- Local users count and remaining capacity
- Local users utilization
- Group count and remaining capacity
- FortiToken count and remaining capacity
- RADIUS NAS count and remaining capacity
- FSSO user count and remaining capacity
- User certificate count

---

## Requirements

- Zabbix Server/Proxy: **6.0** (or compatible newer versions)
- FortiAuthenticator appliance with **SNMP enabled**
- Network access: Zabbix → FortiAuthenticator **UDP/161**
- Optional but recommended: ICMP allowed from Zabbix → device
- Zabbix host must have an **SNMP interface** configured

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Forti Authenticator by SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (device IP/DNS + port 161)
- Configure the SNMP community
- Link template: **Forti Authenticator by SNMP**

### 3) Review Macros
Default operational thresholds are included in the template. Review and adjust them to match your environment.

---

## Macros

| Macro | Default | Description |
|------|---------|-------------|
| `{$FAC.USER.REMAIN.HIGH}` | `20` | Critical low remaining local user threshold |
| `{$FAC.USER.REMAIN.WARN}` | `40` | Warning low remaining local user threshold |
| `{$ICMP_LOSS_WARN}` | `20` | ICMP packet loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP response time warning threshold (seconds) |
| `{$SNMP.TIMEOUT}` | `5m` | Time window used to detect missing SNMP polling |
| `{$SNMP_COMMUNITY}` | `public` | Default SNMP community string |

---

## Value Maps (Included)

### HA Status
- `1` = Unknown or Determining
- `2` = Cluster Primary
- `3` = Cluster Secondary
- `4` = Standalone Primary
- `5` = Load Balancer
- `255` = Disabled

### RAID Status
- `0` = None
- `1` = OK
- `2` = Degraded
- `3` = Failed
- `4` = Initializing
- `5` = Verifying
- `6` = Rebuilding

---

## Monitored Items (Summary)

### Connectivity
- `icmpping`
- `icmppingloss`
- `icmppingsec`
- `zabbix[host,snmp,available]`

### System Information
- `system.name`
- `system.descr[sysDescr.0]`
- `system.contact[sysContact.0]`
- `system.location[sysLocation.0]`
- `system.model`
- `system.version`
- `serial.number`
- `system.uptime[sysUpTime.0]`

### Health & Status
- `cpu.usage`
- `memory.usage`
- `log.disk.usage`
- `ha.status`
- `raid.status`

### Authentication / Directory / RADIUS
- `auth.events.total`
- `auth.events.5.min`
- `auth.failures.total`
- `auth.failures.5.min`
- `ldap.logins.total`
- `ldap.logins.5.min`
- `LDAP.failures.total`
- `ldap.failures.5.min`
- `radius.logins.total`
- `radius.logins.5.min`
- `radius.failures.total`
- `radius.failures.5.min`
- `radius.accounting.total`
- `radius.accounting.5.min`
- `radius.proxy.in.total`
- `radius.proxy.out.total`

### Capacity / Counts
- `user.count`
- `user.remaining`
- `user.utilization`
- `group.count`
- `group.remaining`
- `forti.token.count`
- `forti.token.remaining`
- `radius.nas.count`
- `radius.nas.remaining`
- `fsso.user.count`
- `fsso.user.remaining`
- `user.cert.count`

---

## Key OIDs (Examples)

### System / Inventory
- System model: `1.3.6.1.4.1.12356.113.1.1.0`
- Serial number: `1.3.6.1.4.1.12356.113.1.2.0`
- System version: `1.3.6.1.4.1.12356.113.1.3.0`
- CPU usage: `1.3.6.1.4.1.12356.113.1.4.0`
- Memory usage: `1.3.6.1.4.1.12356.113.1.5.0`
- Log disk usage: `1.3.6.1.4.1.12356.113.1.6.0`

### HA / Storage
- HA status: `1.3.6.1.4.1.12356.113.1.201.1.0`
- RAID status: `1.3.6.1.4.1.12356.113.1.202.28.0`

### Capacity / Licensing
- Local users count: `1.3.6.1.4.1.12356.113.1.202.1.0`
- Group count: `1.3.6.1.4.1.12356.113.1.202.2.0`
- FortiToken count: `1.3.6.1.4.1.12356.113.1.202.3.0`
- Local users remaining: `1.3.6.1.4.1.12356.113.1.202.4.0`
- Group remaining: `1.3.6.1.4.1.12356.113.1.202.5.0`
- FortiToken remaining: `1.3.6.1.4.1.12356.113.1.202.6.0`
- Radius NAS count: `1.3.6.1.4.1.12356.113.1.202.7.0`
- Radius NAS remaining: `1.3.6.1.4.1.12356.113.1.202.8.0`
- User certificate count: `1.3.6.1.4.1.12356.113.1.202.9.0`
- FSSO user count: `1.3.6.1.4.1.12356.113.1.202.26.0`
- FSSO user remaining: `1.3.6.1.4.1.12356.113.1.202.27.0`

---

## Calculated Items

### Local Users Utilization
The template includes a calculated item:

- **Item key:** `user.utilization`
- **Formula:** `100*last(//user.count)/(last(//user.count)+last(//user.remaining))`

This provides a percentage-based view of local user license/utilization consumption.

---

## Triggers (Included)

### Availability / Connectivity
- **Unavailable by ICMP ping** (DISASTER)  
  Last three ICMP checks failed.
- **High ICMP ping loss** (WARNING)  
  Packet loss is above `{$ICMP_LOSS_WARN}`.
- **High ICMP ping response time** (WARNING)  
  Average response time is above `{$ICMP_RESPONSE_TIME_WARN}`.
- **No SNMP data collection** (DISASTER)  
  SNMP polling is unavailable for `{$SNMP.TIMEOUT}`.

### Appliance Health
- **CPU Usage is high for 15 minutes** (HIGH)  
  `min(cpu.usage,15m) >= 80`
- **Memory Usage is high for 15 minutes** (HIGH)  
  `min(memory.usage,15m) >= 80`
- **Log Disk Usage is high for 15 minutes** (HIGH)  
  `min(log.disk.usage,15m) >= 80`

### HA / RAID / Restart
- **HA Status changed** (HIGH)  
  Triggered when the HA state changes between the last two values.
- **RAID Status is Degraded** (HIGH)  
  Triggered when RAID status equals `2`.
- **RAID Status is Failed** (DISASTER)  
  Triggered when RAID status equals `3`.
- **{HOST.NAME} has been restarted (uptime < 10m)** (HIGH)  
  Triggered when uptime is below 10 minutes.

### Capacity
- **Local Users Remaining is low** (HIGH)  
  Triggered when `user.remaining < {$FAC.USER.REMAIN.WARN}`
- **Local Users Remaining is too low** (HIGH)  
  Triggered when `user.remaining < {$FAC.USER.REMAIN.HIGH}`

### Informational
- **System name has changed** (INFO)  
  Triggered when the configured system name changes.

---

## Validation & Troubleshooting

From your Zabbix server/proxy, validate SNMP access:

~~~bash
# Basic SNMP system information
snmpwalk -v2c -c <COMMUNITY> <FAC_IP> 1.3.6.1.2.1.1

# Fortinet / FortiAuthenticator subtree
snmpwalk -v2c -c <COMMUNITY> <FAC_IP> 1.3.6.1.4.1.12356.113

# Spot-check a few template OIDs
snmpget -v2c -c <COMMUNITY> <FAC_IP> 1.3.6.1.4.1.12356.113.1.4.0
snmpget -v2c -c <COMMUNITY> <FAC_IP> 1.3.6.1.4.1.12356.113.1.5.0
snmpget -v2c -c <COMMUNITY> <FAC_IP> 1.3.6.1.4.1.12356.113.1.202.28.0
~~~

### If you see "No SNMP data collection"
- Confirm UDP/161 reachability (firewall/ACL).
- Verify the SNMP community and port.
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether FortiAuthenticator restricts SNMP by source IP.

### If items are unsupported
- Validate the OID manually with `snmpget` or `snmpwalk`.
- Confirm the FortiAuthenticator firmware exposes the same OIDs.
- Verify SNMP version and access permissions.

---

## Security Notes

SNMPv2c uses community strings in plaintext. Reduce exposure by applying:
- Source IP allow-lists
- Network segmentation
- Firewall policies

If you require SNMPv3, you can adapt the host SNMP interface settings accordingly if supported by your environment and firmware.

---

## Contributing

Contributions are welcome, including:
- Additional FortiAuthenticator OIDs and health metrics
- Improved trigger thresholds and operational recommendations
- Additional capacity/license monitoring
- Documentation improvements and validation examples

Please open an issue with:
- FortiAuthenticator model and firmware version
- Zabbix version
- Sanitized `snmpwalk` output for relevant OIDs
- Expected vs. actual behavior

## License
Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks
All product names, trademarks, and registered trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by any vendor mentioned in this repository.
