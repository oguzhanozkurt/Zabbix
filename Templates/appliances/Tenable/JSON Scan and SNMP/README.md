# Tenable Scan JSON and SNMP (Zabbix Template)

This repository provides a Zabbix template that combines:
- **SNMP monitoring** (system health + interface monitoring), and
- **Tenable scan findings ingestion** from a **JSON feed** via **HTTP Agent** + **LLD**.

- Template name: **Tenable Scan JSON and SNMP**
- Zabbix export: **7.0**
- File: `Tenable Scan JSON and SNMP.yaml`

> Note: This is a community template and is not an official Tenable release.

---

## What’s Included

### Availability & Connectivity
- ICMP ping, packet loss, and response time
- SNMP agent availability (Zabbix internal check)
- Host restart detection using SNMP uptime

### System Health (SNMP)
- CPU idle (UCD-SNMP-MIB) + calculated CPU utilization
- Memory metrics (UCD-SNMP-MIB + HOST-RESOURCES-MIB) + calculated memory utilization
- System name / location / description
- Logged-in users, process count, host uptime

### Interface Monitoring (SNMP LLD, IF-MIB)
- LLD discovery of network interfaces
- Per-interface traffic, errors, discards, speed, operational status, interface type
- Trigger prototypes for:
  - Link down (with IFCONTROL)
  - High bandwidth utilization
  - High error rate
  - Speed downgrade detection
- Graph prototype: per-interface traffic + errors/discards

### Tenable Findings (JSON over HTTP + LLD)
- One master HTTP item retrieves a JSON payload (typically “combined high/critical findings”)
- Dependent LLD discovers each finding and creates:
  - A calculated TEXT item representing **Risk** (High/Critical/etc.)
  - A trigger prototype that opens a problem for **High** or **Critical** findings

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Target host reachable via:
  - ICMP (recommended)
  - SNMP (UDP/161)
- A reachable JSON endpoint that returns Tenable findings in the expected format (see “JSON Feed Format”)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Tenable Scan JSON and SNMP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add an **SNMP interface** (device IP/DNS + port 161)
- (Optional) Ensure ICMP is allowed from Zabbix to the host
- Link template: **Tenable Scan JSON and SNMP**

### 3) Configure the Tenable JSON URL
Set macro at **host level**:

| Macro | Example | Description |
|------|---------|-------------|
| `{$TENABLE.URL}` | `https://tenable.company.local/combined_critical_high.json` | Full URL to the JSON feed |

---

## Macros (Defaults)

### CPU / Memory Thresholds
| Macro | Default | Description |
|------|---------|-------------|
| `{$CPU.UTIL.HIGH}` | `80` | High CPU utilization threshold (%) |
| `{$CPU.UTIL.CRIT}` | `90` | Critical CPU utilization threshold (%) |
| `{$MEMORY.UTIL.HIGH}` | `80` | High memory utilization threshold (%) |
| `{$MEMORY.UTIL.CRIT}` | `90` | Critical memory utilization threshold (%) |

### ICMP / SNMP
| Macro | Default | Description |
|------|---------|-------------|
| `{$ICMP_LOSS_WARN}` | `20` | ICMP loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP response time warning threshold (seconds) |
| `{$SNMP.TIMEOUT}` | `5m` | Window used to detect missing SNMP polling |
| `{$SNMP_COMMUNITY}` | `public` | SNMPv2c community (if you use v2c) |

### Interface LLD Filters / Thresholds
| Macro | Default | Description |
|------|---------|-------------|
| `{$IFCONTROL}` | `1` | Controls whether “Link down” triggers should fire per interface |
| `{$IF.UTIL.MAX:"{#IFNAME}"}` | `90` | Bandwidth utilization threshold (%) |
| `{$IF.ERRORS.WARN:"{#IFNAME}"}` | `2` | Error rate warning threshold |
| `{$NET.IF.IFNAME.NOT_MATCHES}` | (predefined) | Excludes loopbacks/docker/veth by default |

> Tip: If you want to exclude additional interfaces, extend `{$NET.IF.IFNAME.NOT_MATCHES}` or use alias/descr filters.

---

## JSON Feed Format (Expected)

The Tenable JSON feed must return a **JSON array** where each element contains at least the fields below:

- `Host`
- `ScanID`
- `No`
- `Risk` (e.g., `Critical`, `High`, `Medium`, `Low`)
- `Plugin`
- `CVEs`
- `Description`
- `Segment`
- `Vlan`

Example:

~~~json
[
  {
    "Host": "server01",
    "ScanID": "2026-03-01-01",
    "No": 1,
    "Risk": "Critical",
    "Plugin": "SSL Certificate Expired",
    "CVEs": "CVE-XXXX-YYYY",
    "Description": "Certificate is expired on the target service.",
    "Segment": "DMZ",
    "Vlan": "100"
  }
]
~~~

---

## Monitored Items (Highlights)

### ICMP
- `icmpping`, `icmppingloss`, `icmppingsec`

### SNMP System / Health
- `cpu.idle` (SNMP) → `cpu.utilization` (calculated: `100 - last(cpu.idle)`)
- `tenable.hrMemorySize` (Memory Total; multiplied by 1024 to bytes)
- `tenable.memTotalFree` (Total Free; multiplied by 1024 to bytes)
- `memory.utilization` (calculated)
- `tenable.memTotalReal`, `tenable.memAvailReal` → `memory.utilization.physical` (calculated)
- `system.uptime[sysUpTime.0]`, `tenable.hrSystemUptime` (uptime)
- `tenable.sysname`, `tenable.syslocation`, `sysdescr`

### Tenable JSON (HTTP)
- Master item: `tenable.json.bulk.item` (HTTP agent, JSON output)
- Discovery: `tenable.scan.discovery` (dependent LLD)
- Finding item prototype: `scan.[{#SCANID},{#NO}]` (calculated TEXT = `{#RISK}`)

---

## Low-Level Discovery (LLD)

### 1) Network Interfaces (IF-MIB)
- Discovery key: `net.if.discovery`
- Discovers: `{#IFNAME}`, `{#IFALIAS}`, `{#IFDESCR}`, `{#IFTYPE}`, `{#IFOPERSTATUS}`, `{#IFADMINSTATUS}`, `{#SNMPINDEX}`

Creates per-interface items:
- Traffic: `net.if.in[...]`, `net.if.out[...]`
- Errors: `net.if.in.errors[...]`, `net.if.out.errors[...]`
- Discards: `net.if.in.discards[...]`, `net.if.out.discards[...]`
- Speed: `net.if.speed[...]`
- Status: `net.if.status[...]` (value map: IF-MIB::ifOperStatus)
- Type: `net.if.type[...]`

### 2) Tenable Scan Findings (JSON)
- Discovery key: `tenable.scan.discovery` (dependent on `tenable.json.bulk.item`)
- LLD macros:
  - `{#HOST}`, `{#SCANID}`, `{#NO}`, `{#RISK}`, `{#PLUGIN}`, `{#CVES}`, `{#DESC}`, `{#SEGMENT}`, `{#VLAN}`

---

## Triggers (Included)

### Availability
- **Unavailable by ICMP ping** (DISASTER)
- **High ICMP ping loss** (WARNING)
- **High ICMP ping response time** (WARNING)
- **No SNMP data collection** (DISASTER)
- **{HOST.NAME} has been restarted (uptime < 10m)** (HIGH)

### CPU / Memory
- **High CPU utilization** (HIGH) and **Critical CPU utilization** (DISASTER)
- **High Memory utilization** (HIGH) and **Critical Memory utilization** (DISASTER)

### Tenable JSON
- **No data from Tenable JSON for 30 minutes** (DISASTER)

### Interfaces (Trigger Prototypes)
- **Link down** (DISASTER) — controlled by `{$IFCONTROL:"{#IFNAME}"}`
- **High bandwidth usage** (WARNING)
- **High error rate** (WARNING)
- **Ethernet speed downgraded** (INFO)

---

## Validation & Troubleshooting

### SNMP Validation
From your Zabbix server/proxy:

~~~bash
# Basic SNMP system info
snmpwalk -v2c -c <COMMUNITY> <HOST_IP> 1.3.6.1.2.1.1

# CPU idle (UCD-SNMP-MIB)
snmpget  -v2c -c <COMMUNITY> <HOST_IP> 1.3.6.1.4.1.2021.11.11.0

# Memory totals (HOST-RESOURCES-MIB) and UCD memory
snmpget  -v2c -c <COMMUNITY> <HOST_IP> 1.3.6.1.2.1.25.2.2.0
snmpget  -v2c -c <COMMUNITY> <HOST_IP> 1.3.6.1.4.1.2021.4.11.0
~~~

### JSON Feed Validation
Test the JSON endpoint from the Zabbix server/proxy:

~~~bash
curl -sS -m 10 "<TENABLE_JSON_URL>" | head -n 50
~~~

Recommended checks:
- HTTP 200
- Response begins with `[` and is a JSON array
- Fields exist: `Host`, `ScanID`, `No`, `Risk`, `Plugin`, `CVEs`, `Description`, `Segment`, `Vlan`

### If Tenable LLD discovers no findings
- Confirm `{$TENABLE.URL}` is correct (including `http/https` and path).
- Confirm the response is not wrapped (must be a plain JSON array).
- If the endpoint adds leading characters/BOM, the preprocessing removes BOM and trims leading noise; validate the output is still valid JSON.

---

## Security Notes

- SNMPv2c uses community strings in plaintext. Reduce exposure by applying:
  - Source IP allow-lists
  - Network segmentation
  - Firewall policies
- The Tenable JSON feed may contain sensitive vulnerability data. Reduce exposure by applying:
  - HTTPS (TLS)
  - Access controls (reverse proxy authentication where needed)
  - Source IP allow-lists (only allow Zabbix server/proxy)
  - Do not expose the feed publicly

---

## Contributing

Contributions are welcome, including:
- Enhancements to JSON preprocessing (different feed formats)
- Additional SNMP metrics for the target Tenable host/appliance
- Improved interface filters and thresholds
- Documentation improvements and tested examples

Please open an issue with:
- Zabbix version
- Sanitized sample JSON payload (remove sensitive data)
- Sanitized SNMP walk output (relevant OIDs)
- Expected vs. actual behavior

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Tenable.
