# Tenable Scan JSON Template (Zabbix)

This repository provides a Zabbix template to monitor **Tenable scan findings** by consuming a **JSON feed over HTTP**.  
It is designed for environments where scan results are exported/aggregated to a single JSON endpoint and then ingested by Zabbix.

- Template name: **Tenable Scan JSON Template**
- Zabbix export: **7.0**
- File: **Tenable Scan JSON Template.yaml**
- Collection method: **HTTP Agent (bulk)** + **Dependent LLD** + **Calculated item prototypes** + **Trigger prototypes**

> Note: This is a community template and is not an official Tenable release.

---

## What’s Included

### Bulk JSON Collection (HTTP Agent)
- A single master HTTP item fetches the JSON payload on a schedule.
- The discovery rule (LLD) is **dependent** on the master item (efficient, low overhead).

### Automated Discovery (LLD) for Findings
Each JSON record is discovered as a separate entity using the following LLD macros:
- `{#HOST}`, `{#SCANID}`, `{#NO}`, `{#RISK}`, `{#PLUGIN}`, `{#CVES}`, `{#DESC}`, `{#SEGMENT}`, `{#VLAN}`

### Finding Representation in Zabbix
For each discovered record, the template creates:
- A **calculated TEXT item** that stores the risk level (using `{#RISK}`).
- A **trigger prototype** that raises a problem when the risk is **High** or **Critical**.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- An HTTP/HTTPS endpoint reachable from Zabbix that returns a JSON payload in the expected format
- Network access: Zabbix → endpoint (TCP 80/443 or custom port)

---

## Data Format (Expected JSON)

Your endpoint must return a **JSON array** where each element represents a single finding and contains the fields below:

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
    "ScanID": "2026-02-24-01",
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

> If your feed uses different field names, you must adjust the LLD macro paths in the template accordingly.

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Tenable Scan JSON Template.yaml`

### 2) Create/Update a Host
Zabbix UI → **Data collection → Hosts → Create host**
- Create a host (e.g., `Tenable-Scan-Feed`)
- Link the template: **Tenable Scan JSON Template**

### 3) Configure the URL Macro
Set the JSON feed URL at **host level**:

| Macro | Default | Description |
|------|---------|-------------|
| `{$TENABLE.URL}` | `https://sms.kalekalip.com.tr/combined_critical_high.json` | Full URL to the JSON feed |

---

## How It Works (Design)

### Master Item
- Name: **Tenable Bulk item**
- Type: **HTTP agent**
- Key: `tenable.bulk.item`
- Interval: **1h**
- Value type: **Text**
- Output format: **JSON** (Zabbix wraps the HTTP response; body is extracted in preprocessing)

### Discovery Rule
- Name: **Tenable Scan Discovery**
- Key: `tenable.scan.discovery`
- Type: **Dependent**
- Master item: `tenable.bulk.item`

Preprocessing steps:
1. JSONPath: `$.body` (extract response body)
2. JavaScript: removes BOM/leading noise and parses the JSON string reliably
3. JSONPath: `$[*]` (iterate over the array to produce LLD entities)

### Item Prototype
- Name: `SCAN - {#HOST} - {#RISK} - {#PLUGIN}`
- Type: **Calculated**
- Key: `scan.[{#SCANID},{#NO}]`
- Value type: **Text**
- Value: `{#RISK}` (risk level is stored as the item value)
- Description includes full finding context (host, scan id, segment, vlan, plugin, CVEs, description)

### Trigger Prototype
- Name: `{#HOST} - {#RISK} - {#PLUGIN}`
- Severity: **AVERAGE**
- Expression:
  - Triggers when item value is `"High"` OR `"Critical"`
- Manual close: **Enabled**
- Trigger description repeats the full context (helpful for incident handling)

---

## Operational Notes

- Since the master item polls hourly, plan your JSON feed refresh accordingly (e.g., regenerate the JSON file every hour).
- LLD lifetime is set to **1 hour**; findings that disappear from the feed may be removed/expired quickly. If you want longer retention of discovered entities, increase LLD lifetime in the rule settings.

---

## Validation & Troubleshooting

Validate the endpoint from your Zabbix server/proxy:

~~~bash
curl -sS -m 10 "<TENABLE_JSON_URL>" | head -n 50
~~~

Recommended checks:
- Confirm HTTP **200** response.
- Confirm the response is a **JSON array** (`[` as the first meaningful character).
- Confirm each element contains the required keys (Host, ScanID, No, Risk, Plugin, etc.).

### If you see "No data", "Unsupported", or the discovery produces no entities
- Confirm network reachability to the endpoint (routing/firewall/NAT/proxy).
- Verify `{$TENABLE.URL}` is correct (including scheme `http/https`).
- Ensure the endpoint returns a JSON **array** and not a wrapped object.
- Confirm the response body is accessible as `$.body` (used by the preprocessing).
  - If your HTTP agent returns raw body (not wrapped), you may need to remove/adjust the `$.body` preprocessing step.

---

## Security Notes

The JSON feed may include sensitive vulnerability information. Reduce exposure by applying:
- Source IP allow-lists (only allow Zabbix server/proxy)
- Network segmentation (private network/VPN)
- Firewall policies and logging
- TLS (HTTPS) with proper certificate management
- Access control (reverse proxy authentication, if required by your security posture)

Avoid exposing the feed publicly on the internet.

---

## Contributing

Contributions are welcome, including:
- Enhancements to parsing/preprocessing for alternative JSON formats
- Additional trigger logic (e.g., include Medium, or custom severities)
- Better retention/LLD behavior recommendations
- Documentation improvements and examples

Please open an issue with:
- Zabbix version
- Sample JSON payload (sanitized)
- Expected vs. actual behavior
- Any preprocessing errors from the item/discovery rule
