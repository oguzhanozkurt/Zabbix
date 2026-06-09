# Trend Micro Deep Security / Workload Security — Computers by HTTP (Zabbix 7.0 Template)

This repository provides a Zabbix template for **per-computer monitoring** of **Trend Micro Deep Security Manager (DSM)** / **Workload Security Manager** using the DSM **REST API** and **dependent LLD**.

- Template name: **Template Trend Micro Deep Security Computers by HTTP**
- Zabbix export: **7.0**
- File: `template_trend_micro_dsm_computers_http.yaml`
- Collection method: **HTTP Agent (master)** → **Dependent LLD** → **Per-computer raw dependent item** → **Dependent per-field items** → **Trigger prototypes**

> Note: This is a community template and is not an official Trend Micro release.

---

## What’s Included

## 1) Full Computer Inventory Pull (Master Item)
One HTTP master item retrieves the full computers list with expanded objects:
- Endpoint: `GET /api/computers?expand=computerStatus,allSecurityModules`
- Authentication: API secret key header (`api-secret-key`)
- Output: raw JSON (stored as TEXT)

## 2) Per-Computer Discovery (LLD)
A dependent discovery rule generates one entity per computer with these macros:
- `{#ID}` (computer ID)
- `{#HOSTNAME}`
- `{#DISPLAYNAME}` (displayName, fallback hostName, fallback `ID-<ID>`)
- `{#POLICYID}`
- `{#PLATFORM}`
- `{#AGENTVER}`
- `{#LASTIP}`

LLD filtering is supported via regex macros on `{#DISPLAYNAME}`.

## 3) Per-Computer Telemetry (Dependent Items)
For each discovered computer, the template creates:
- A **per-computer raw object** item (TEXT) extracted from the master list
- Dependent items for operational status:
  - Agent status + status message
  - Agent version, platform, policy ID, last IP used
  - “No agent/appliance” flag (derived)
- Security module visibility:
  - Anti-Malware (state, status, message)
  - Firewall (state, status, message)
  - Intrusion Prevention (state, status, message)
  - Integrity Monitoring (state, status, message)
  - Log Inspection (state, status, message)

## 4) Alerting (Trigger Prototypes)
Per-computer trigger prototypes for:
- No agent/appliance detected
- Agent not active
- Agent appears offline (message match)
- Agent upgrade recommended (message match)
- Each module unhealthy when module **state = "on"** but module **status != "active"**

All triggers are configured with **manual close enabled**.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Trend Micro DSM / Workload Security Manager reachable from Zabbix via HTTP/HTTPS
- A DSM API secret key with read permissions
- Network access: Zabbix → DSM (commonly TCP 4119, depending on your deployment)

---

## Quick Start

### Import the template
Zabbix UI → **Data collection → Templates → Import**  
Import: `template_trend_micro_dsm_computers_http.yaml`

### Create a host and link the template
Create a host representing your DSM manager endpoint and link:
- **Template Trend Micro Deep Security Computers by HTTP**

### Configure macros (required)
Set these at host level:

| Macro | Default | Description |
|------|---------|-------------|
| `{$TM.DSM.URL}` | `https://dsm.example.com:4119` | DSM base URL |
| `{$TM.DSM.API.KEY}` | *(empty)* | API secret key (**store as Secret macro**) |
| `{$TM.DSM.API.VERSION}` | `v1` | API version header value |
| `{$TM.DSM.COMPUTERS.DELAY}` | `10m` | Interval for the full computers collection |
| `{$TM.DSM.TIMEOUT}` | `30s` | HTTP timeout for DSM requests |
| `{$TM.DSM.COMPUTER.MATCHES}` | `.*` | LLD include regex for `{#DISPLAYNAME}` |
| `{$TM.DSM.COMPUTER.NOT_MATCHES}` | `^$` | LLD exclude regex for `{#DISPLAYNAME}` |

> Note: `{$TM.DSM.LLD.DELAY}` exists in the template as a convenience macro, but discovery is **dependent**, so its cadence follows the master item refresh interval.

---

## How It Works

## Master item
- **Key:** `tm.dsm.computers.full.raw`
- **URL:** `{$TM.DSM.URL}/api/computers?expand=computerStatus,allSecurityModules`
- **Headers:**
  - `api-secret-key: {$TM.DSM.API.KEY}`
  - `api-version: {$TM.DSM.API.VERSION}`
- **TLS verification:** disabled by default (`verify_peer=NO`, `verify_host=NO`)
- **Preprocessing:**
  - Checks JSON error at `$.error.message`
  - Discards unchanged responses with a 1h heartbeat

## LLD rule
- **Key:** `tm.dsm.computers.discovery`
- **Type:** Dependent (master: `tm.dsm.computers.full.raw`)
- **Output:** a list of macro objects created from each computer entry
- **Lifetime:** configured as “never delete/disable” (entities are retained)

## Per-computer fan-out
A dependent item extracts the single computer object by ID:
- **Key:** `tm.computer.raw[{#ID}]`
- This raw object feeds all other per-computer dependent items via JSONPath.

This design minimizes repeated parsing across the full list and keeps item prototypes clean.

---

## Triggers (Prototype Logic)

Per `{#DISPLAYNAME}`:

- **No agent/appliance detected** (HIGH)  
  Fires when no `agentFingerPrint` AND no `applianceFingerPrint` is present.

- **Agent is not active** (AVERAGE)  
  Fires when `computerStatus.agentStatus <> "active"`.

- **Agent appears offline** (AVERAGE)  
  Fires when agent status message matches `Offline` (case-insensitive regex).

- **Agent upgrade recommended** (WARNING)  
  Fires when agent status message matches `Upgrade Recommended` (case-insensitive regex).

- **Module unhealthy** (HIGH)  
  For each module (AM/FW/IPS/IM/LI):  
  Fires when `module.state="on"` and `module.moduleStatus.agentStatus <> "active"`.

---

## Validation & Troubleshooting

### Validate DSM API from Zabbix server/proxy
~~~bash
curl -k -sS \
  -H "api-secret-key: <API_KEY>" \
  -H "api-version: v1" \
  "https://<DSM_HOST>:4119/api/computers?expand=computerStatus,allSecurityModules" | head -n 40
~~~

Expected:
- HTTP 200
- JSON array of computers
- Each element includes fields like `ID`, `hostName`, `displayName`, `computerStatus`, and module objects.

### If discovery returns no computers
- Confirm `{$TM.DSM.URL}` and port are correct.
- Confirm the API key is valid and permitted.
- Review LLD filters:
  - Set `{$TM.DSM.COMPUTER.MATCHES}` to `.*`
  - Set `{$TM.DSM.COMPUTER.NOT_MATCHES}` to `^$` (default)
- Check the master item latest value and preprocessing errors.

### If module items are unsupported
Module paths can vary across DSM/Workload Security versions. Verify the raw object contains:
- `antiMalware`, `firewall`, `intrusionPrevention`, `integrityMonitoring`, `logInspection`
and adjust JSONPath if your environment uses different naming.

### Scaling note (large environments)
`/api/computers` may be paginated in large deployments. This template uses a single HTTP request and does not handle paging.
For large estates, consider replacing the master HTTP agent item with a **Script item** that iterates pages and returns a merged JSON array.

---

## Security Notes

- Store `{$TM.DSM.API.KEY}` as a **Secret macro**.
- TLS peer/host verification is disabled by default for pilot convenience.  
  **Recommendation:** install a trusted certificate on DSM and enable TLS verification once validated.
- Restrict API exposure:
  - Source IP allow-lists (only allow Zabbix server/proxy)
  - Network segmentation
  - Firewall policies and logging

---

## Contributing

Contributions are welcome, including:
- Paging support (script-based master item)
- Additional module coverage (Web Reputation, Application Control, etc.)
- Better state normalization/value maps
- Dashboards and trend-friendly rollups

Please open an issue with:
- DSM / Workload Security version
- Zabbix version
- Sanitized sample `computer` JSON object
- Expected vs. actual behavior (including preprocessing errors)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by Trend Micro.
