# Infoblox Template by API (Zabbix)

This repository provides a Zabbix template to monitor **Infoblox DNS threat events** by consuming the **Infoblox Cloud Services Portal (CSP) DNS Data API** endpoint and generating **event-based alerts** via LLD.

- Template name: **Infoblox Template by API**
- Zabbix export: **7.0**
- File: **Infoblox Template by API.yaml**
- Collection method: **Script (HTTP request)** → **Dependent LLD** → **Calculated item prototypes** → **Trigger prototypes**
- API endpoint: `/api/dnsdata/v2/dns_event`

> Note: This is a community template and is not an official Infoblox release.

---

## What’s Included

### Bulk Event Collection (Script Item)
- A single **Script** item fetches DNS events from Infoblox CSP.
- Uses a token-based authorization header: `Authorization: Token <token>`.
- Pulls events within the last **N hours** and filters by **threat level** and **network**.

### Automated Discovery (LLD) for DNS Events
- Discovery rule is **dependent** on the master script item (efficient).
- Each returned event is deduplicated and converted into an LLD entity.

LLD macros created per event:
- `{#DEVICE}`, `{#EVENT_TIME}`, `{#NETWORK}`, `{#QNAME}`, `{#RDATA}`, `{#SEVERITY}`, `{#HASH}`

### Event Items & Alerts
For each discovered event, the template creates:
- A **calculated text item** that stores `{#QNAME}` (query name).
- A **trigger prototype** that opens a problem for each discovered event (manual close enabled).

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Access to Infoblox CSP DNS Data API (`/api/dnsdata/v2/dns_event`)
- A valid Infoblox API token with permission to query DNS events
- Network connectivity: Zabbix → `https://csp.infoblox.com` (or your CSP base URL)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Infoblox Template by API.yaml`

### 2) Create/Update a Host
Zabbix UI → **Data collection → Hosts → Create host**
- Create a host (e.g., `Infoblox-CSP`)
- Link the template: **Infoblox Template by API**

### 3) Configure Macros (Required)
Set macros at **host level** (recommended). See the table below.

---

## Macros

| Macro | Example | Description |
|------|---------|-------------|
| `{$INFOBLOX_BASEURL}` | `https://csp.infoblox.com` | Infoblox CSP base URL |
| `{$INFOBLOX_TOKEN}` | *(secret)* | API token (store as **Secret macro**) |
| `{$INFOBLOX_NETWORK}` | `Customer NAT IP` | Network filter value **in plain text** (do **not** pre-encode) |
| `{$INFOBLOX_HOURS}` | `9` | How many past hours of events to query |
| `{$INFOBLOX_THREAT}` | `3` | Threat level filter passed to API |
| `{$INFOBLOX_TIMEOUT}` | `30` | Timeout value (note: template item uses 30s by default; see note below) |

**Important note on `{$INFOBLOX_NETWORK}`**  
Enter the network value exactly as Infoblox expects it (plain text). The script will URL-encode it automatically.

**Timeout note**  
The master item uses a built-in item timeout of **30 seconds** in the template export. If you need a different timeout, adjust the item’s *Timeout* field in Zabbix (or update the script to reference `{$INFOBLOX_TIMEOUT}`).

---

## How It Works

### Master Item (Script)
- Name: **Infoblox Script Raw Data**
- Key: `infoblox.script.raw.data`
- Type: `SCRIPT`
- Interval: **15m**
- Output: JSON (validated by the script)

The script builds a request like:
- `GET {BASEURL}/api/dnsdata/v2/dns_event?t0=<unix>&t1=<unix>&threat_level=<level>&network=<network>`

### Discovery Rule (Dependent LLD)
- Name: **Infoblox Discovery**
- Key: `infoblox.dns.events.lld`
- Type: Dependent
- Master item: `infoblox.script.raw.data`
- LLD lifetime: **3d**
- Deduplication key: `device|event_time|network|qname|rdata|severity`
- `{#HASH}` is generated to provide a stable identifier for item/trigger keys.

### Item Prototype (Calculated)
- Name: `{#DEVICE} - {#SEVERITY} - {#HASH}`
- Key: `device.severity.[{#HASH}]`
- Type: Calculated (TEXT)
- Value: `{#QNAME}`

### Trigger Prototype (Event Alert)
- Name: `{#DEVICE} - {#SEVERITY} - {#NETWORK} - {#RDATA} - {#QNAME}`
- Severity: **AVERAGE**
- Manual close: **Enabled**
- Expression: opens a problem when the event item is not empty (i.e., event exists)

---

## Operational Notes

- The master item polls every **15 minutes**, querying the last `{$INFOBLOX_HOURS}` hours.
- If you want near-real-time alerting, reduce the item interval (and consider tightening `{$INFOBLOX_HOURS}`).
- LLD lifetime is **3 days**. If events stop appearing, the corresponding discovered entities expire after that period.

---

## Validation & Troubleshooting

### Validate API Access from Zabbix Server/Proxy

Generate timestamps:
~~~bash
t1=$(date +%s)
t0=$((t1-9*3600))
echo "t0=$t0 t1=$t1"
~~~

Test the API call (example):
~~~bash
curl -sS -H "Authorization: Token <TOKEN>" -H "Accept: application/json" \
"https://csp.infoblox.com/api/dnsdata/v2/dns_event?t0=<t0>&t1=<t1>&threat_level=3&network=$(python3 -c 'import urllib.parse; print(urllib.parse.quote(\"Customer NAT IP\"))')"
~~~

### If you see errors in the master item
- **HTTP 401/403**: token invalid/expired or missing permissions.
- **HTTP 404**: incorrect base URL or API path not available for your tenant.
- **HTTP 5xx**: CSP/API transient issue; retry and check service status.
- **Invalid JSON**: upstream response is not JSON; validate proxy/WAF responses and headers.

### If discovery produces no entities
- Confirm the API returns a non-empty array for your chosen time window.
- Verify `{$INFOBLOX_NETWORK}` matches Infoblox event data exactly.
- Adjust `{$INFOBLOX_HOURS}` to a larger window temporarily (e.g., 24) to confirm data exists.

---

## Security Notes

The API token is sensitive and may provide access to security telemetry. Reduce exposure by applying:
- Store `{$INFOBLOX_TOKEN}` as a **Secret macro**
- Restrict Zabbix UI access to authorized administrators
- Use HTTPS only (recommended by default with CSP)
- Apply source IP allow-lists and firewall policies where feasible
- Avoid logging the token in scripts, external logs, or screenshots

---

## Contributing

Contributions are welcome, including:
- Support for additional API parameters/filters
- Improved severity mapping and trigger logic (e.g., different severities per `{#SEVERITY}`)
- Enhancements to deduplication logic and event retention behavior
- Documentation improvements and tested examples

Please open an issue with:
- Zabbix version
- Sanitized sample API response (remove sensitive data)
- Expected vs. actual behavior
- Any relevant error output from the master item
