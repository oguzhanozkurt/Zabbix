# Trend Micro Deep Security / Workload Security Manager by HTTP (Zabbix 7.0 Template)

This repository provides a Zabbix 7.0 template to monitor **Trend Micro Deep Security Manager (DSM)** / **Workload Security Manager** via **HTTP**, using the newer `/api` endpoints (API key headers) and a legacy `/rest/apiVersion` endpoint as a secondary liveness check.

- Template name: **Template Trend Micro Deep Security Manager by HTTP**
- Zabbix export: **7.0**
- File: `template_trend_micro_dsm_manager_http.yaml`
- Collection method: **HTTP Agent (raw JSON)** → **Dependent items** → **Triggers**

> Note: This is a community template and is not an official Trend Micro release.

---

## Scope / Coverage

### 1) Manager/API Availability
- Authenticated API check against the **newer** DSM API (`/api/policies`)
- Secondary unauthenticated endpoint check (`/rest/apiVersion`) for basic liveness and version visibility

### 2) Workload/Computer Status Summary
Retrieves a summarized list of computers from:
- `/api/computers?expand=computerStatus`

And derives the following counts:
- Total computers returned
- Computers without agent/appliance fingerprint (unprotected)
- Computers with non-active agent status
- Computers “Managed (Online)” (based on agent status messages)
- Computers with “Upgrade Recommended” status message

---

## Assumptions

This template assumes:
- DSM exposes the newer `/api` endpoints and accepts headers:
  - `api-secret-key`
  - `api-version`
- Legacy `/rest/apiVersion` is available for a lightweight check.
- `/api/computers?expand=computerStatus` returns an array with `computerStatus` fields.

If your DSM version returns different JSON fields, adjust the JSONPath / JavaScript preprocessing accordingly.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Trend Micro DSM / Workload Security Manager reachable from Zabbix via HTTP/HTTPS
- A DSM API secret key (read-only is recommended) and API version header value
- Network access: Zabbix → DSM (typically TCP 4119 for DSM console/API)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `template_trend_micro_dsm_manager_http.yaml`

### 2) Create/Update a Host
Create a host representing your DSM manager endpoint and link the template:
- **Template Trend Micro Deep Security Manager by HTTP**

### 3) Configure Macros (Required)
Set these at **host level**:

| Macro | Default | Description |
|------|---------|-------------|
| `{$TM.DSM.URL}` | `https://dsm.example.com:4119` | Base URL of Trend Micro DSM / Workload Security Manager |
| `{$TM.DSM.API.KEY}` | *(empty)* | API secret key (**store as Secret macro**) |
| `{$TM.DSM.API.VERSION}` | `v1` | API version header value |
| `{$TM.DSM.API.DELAY}` | `5m` | Polling interval for authenticated API check |
| `{$TM.DSM.COMPUTERS.DELAY}` | `10m` | Polling interval for computers status retrieval |
| `{$TM.DSM.TIMEOUT}` | `15s` | HTTP timeout for DSM requests |

---

## How It Works

### Authenticated API Health (New API)
**Master item**
- Name: `Trend Micro DSM: API health raw`
- Key: `tm.dsm.api.health.raw`
- Type: HTTP agent
- URL: `{$TM.DSM.URL}/api/policies`
- Headers:
  - `api-secret-key: {$TM.DSM.API.KEY}`
  - `api-version: {$TM.DSM.API.VERSION}`
- TLS verification: **disabled** in the template (pilot-friendly)

**Dependent item**
- Key: `tm.dsm.api.health`
- Returns `1` when the authenticated request succeeds and valid JSON is received.

### Legacy REST apiVersion (Secondary Check)
**Master item**
- Name: `Trend Micro DSM: Legacy REST apiVersion raw`
- Key: `tm.dsm.rest.apiversion.raw`
- URL: `{$TM.DSM.URL}/rest/apiVersion`

**Dependent item**
- Key: `tm.dsm.rest.apiversion`
- Extracts version text.

### Computers Status (Summarized Inventory/Health)
**Master item**
- Name: `Trend Micro DSM: Computers status raw`
- Key: `tm.dsm.computers.status.raw`
- URL: `{$TM.DSM.URL}/api/computers?expand=computerStatus`
- Headers:
  - `api-secret-key: {$TM.DSM.API.KEY}`
  - `api-version: {$TM.DSM.API.VERSION}`

**Dependent items**
- `tm.dsm.computers.total` — total array length
- `tm.dsm.computers.noagent` — computers without agent/appliance fingerprint
- `tm.dsm.computers.nonactive` — computers where `agentStatus != active`
- `tm.dsm.computers.managed.online` — “Managed (Online)” found in agent status messages
- `tm.dsm.computers.upgrade.recommended` — “Upgrade Recommended” found in agent status messages

---

## Triggers (Included)

### Availability
- **Trend Micro DSM: Authenticated API is unavailable** (HIGH)  
  Fires when `tm.dsm.api.health` has no data for 10 minutes (manual close enabled).

- **Trend Micro DSM: Legacy REST apiVersion endpoint is unavailable** (WARNING)  
  Fires when `tm.dsm.rest.apiversion` has no data for 1 hour (manual close enabled).

### Security / Health Signals
- **Trend Micro DSM: Unprotected computers detected** (HIGH)  
  Fires when `tm.dsm.computers.noagent > 0` (manual close enabled).

- **Trend Micro DSM: Computers with non-active agent status detected** (AVERAGE)  
  Fires when `tm.dsm.computers.nonactive > 0` (manual close enabled).

- **Trend Micro DSM: Computers with agent upgrade recommended detected** (WARNING)  
  Fires when `tm.dsm.computers.upgrade.recommended > 0` (manual close enabled).

---

## Validation & Troubleshooting

### Validate API health with curl (from Zabbix server/proxy)
~~~bash
curl -k -sS \
  -H "api-secret-key: <API_KEY>" \
  -H "api-version: v1" \
  "https://<DSM_HOST>:4119/api/policies" | head -n 30
~~~

### Validate legacy endpoint
~~~bash
curl -k -sS "https://<DSM_HOST>:4119/rest/apiVersion"
~~~

### Validate computers payload
~~~bash
curl -k -sS \
  -H "api-secret-key: <API_KEY>" \
  -H "api-version: v1" \
  "https://<DSM_HOST>:4119/api/computers?expand=computerStatus" | head -n 30
~~~

### If the authenticated check fails
- Confirm the API key is valid and has the required permissions.
- Confirm `{$TM.DSM.API.VERSION}` matches your DSM API expectations.
- Check for proxy/WAF blocks between Zabbix and DSM.

### If computers-derived counts look incorrect
- Inspect the raw payload (`tm.dsm.computers.status.raw`) in Latest data.
- Verify your DSM returns:
  - `computerStatus.agentStatus`
  - `computerStatus.agentStatusMessages`
  - `agentFingerPrint` / `applianceFingerPrint`
- Adjust the JavaScript preprocessing if field names differ in your DSM build.

---

## Security Notes

- The API key is sensitive. Store `{$TM.DSM.API.KEY}` as a **Secret macro**.
- This template disables TLS peer/host verification by default for easier pilots.  
  **Recommendation:** Install a trusted certificate on DSM and enable TLS verification after initial validation.
- Restrict API exposure:
  - Source IP allow-lists (only Zabbix server/proxy)
  - Network segmentation
  - Firewall policies and logging

---

## Contributing

Contributions are welcome, including:
- Additional endpoints (alerts, policies, events, computers by state)
- More robust field handling for DSM version differences
- Trigger tuning (severity and suppression rules)
- Dashboards and trend-friendly items

Please include:
- DSM / Workload Security version
- Zabbix version
- Sanitized sample JSON (relevant parts)
- Expected vs. actual behavior (and any preprocessing errors)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Trend Micro.
