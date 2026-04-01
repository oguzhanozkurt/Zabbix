# Cisco AppDynamics SLA Monitoring by HTTP (Zabbix Template)

This repository provides a Zabbix template to monitor **Cisco AppDynamics Business Transactions (BT)** and compute multiple **SLA indicators** using the **AppDynamics Controller REST API** (`/rest/applications/<app>/metric-data`) via **HTTP Agent** items.

- Template name: **Cisco Appdynamics SLA Monitoring by HTTP**
- Zabbix export: **7.0**
- File: `Cisco Appdynamics SLA Monitoring by HTTP.yaml`
- Collection method: HTTP Agent (bulk metric-data) → Dependent LLD → Dependent items + Calculated SLA items

> Note: This is a community template and is not an official Cisco/AppDynamics release.

---

## What’s Included

### Bulk Metric Retrieval (HTTP Agent)
The template retrieves AppDynamics metric data (JSON) using multiple master HTTP items:
- `appd.sla.raw.discovery` (used by BT discovery)
- `appd.sla.raw.cpm` (Calls per Minute)
- `appd.sla.raw.epm` (Errors per Minute)
- `appd.sla.raw.art` (Average Response Time)
- `appd.sla.raw.slowcalls` (Number of Slow Calls)
- `appd.sla.raw.veryslowcalls` (Number of Very Slow Calls)

All master items use:
- **Basic Authentication** (`{$APPD.USER}` / `{$APPD.PASS}`)
- A configurable timeout: `{$APPD.TIMEOUT}`
- A configurable time window: `{$APPD.TIMERANGETYPE}` + `{$APPD.DURATIONINMINUTES}`
- App/controller scope: `{$APPD.URL}` + `{$APPD.APP}`

---

## Business Transaction Discovery (LLD)

### How discovery works
- Discovery rule key: `appd.sla.discovery` (Dependent)
- Master item: `appd.sla.raw.discovery`
- Preprocessing: JavaScript parses `metricPath` values and extracts:
  - `{#TIER}`
  - `{#BT}`
  - `{#ARTPATH}` = “Average Response Time (ms)”
  - `{#CPMPATH}` = “Calls per Minute”
  - `{#EPMPATH}` = “Errors per Minute”

Discovery only includes metric paths matching:
- `Business Transaction Performance|Business Transactions|<TIER>|<BT>|...`

This creates per-BT item prototypes.

---

## Monitored Metrics (Per Business Transaction)

Dependent items (from master JSON via JSONPath):
- **Calls per Minute**: `appd.bt.cpm.sum[{#BT}]` (units: rpm)
- **Errors per Minute**: `appd.bt.epm.sum[{#BT}]` (units: rpm)
- **Average Response Time**: `appd.bt.art.sum[{#BT}]` (units: ms)
- **Number of Slow Calls**: `appd.bt.slowcalls.sum[{#BT}]`
- **Number of Very Slow Calls**: `appd.bt.veryslowcalls.sum[{#BT}]`

> The JSONPath preprocessing uses the BT-specific `{#...PATH}` macros or fixed metric paths (slow/very slow calls) and returns `0` on missing data.

---

## SLA Calculations (Per Business Transaction)

The template calculates the following SLA indicators:

### 1) Availability SLA (%)
Key: `appd.bt.availability.sla.pct[{#BT}]`

Formula (concept):
- If CPM > 0: `(CPM - EPM) / CPM * 100`
- If CPM = 0: `100`

### 2) Error SLA (%)
Key: `appd.bt.error.sla.pct[{#BT}]`

Formula (concept):
- If CPM > 0: `EPM / CPM * 100`
- If CPM = 0: `0`

### 3) Performance SLA (%)
Key: `appd.bt.performance.sla.pct[{#BT}]`

Formula (concept):
- If CPM > 0: `(CPM - Slow - VerySlow) / CPM * 100`
- If CPM = 0: `100`

### 4) Slow Transaction SLA (%)
Key: `appd.bt.slow.transaction.sla.pct[{#BT}]`

Formula (concept):
- If CPM > 0: `Slow / CPM * 100`
- If CPM = 0: `0`

### 5) Apdex-style SLA (0..1)
Key: `appd.bt.apdex.sla[{#BT}]`

Formula (as implemented):
- If CPM > 0:
  - `((CPM - Slow - VerySlow) + (Slow * 0.5)) / CPM`
- If CPM = 0:
  - `1`

Interpretation:
- `0` = bad
- `1` = good

> Apdex-like SLA treats **Slow** calls as half-satisfied and **Very Slow** calls as unsatisfied.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- AppDynamics Controller reachable from Zabbix via HTTPS/HTTP
- A valid AppDynamics user account with permission to read metric data
- Network access: Zabbix → AppDynamics Controller (TCP 443/80)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Cisco Appdynamics SLA Monitoring by HTTP.yaml`

### 2) Create/Update a Host
Create a host representing your AppDynamics application/controller scope and link the template.

### 3) Configure Macros (Required)
Set the macros at host level:

| Macro | Example | Description |
|------|---------|-------------|
| `{$APPD.URL}` | `https://apm.company.local/controller` | AppDynamics Controller base URL |
| `{$APPD.APP}` | `MyApplication` | Application name (as in AppDynamics) |
| `{$APPD.USER}` | `api-user` | AppDynamics username |
| `{$APPD.PASS}` | *(secret)* | AppDynamics password (store as Secret macro) |
| `{$APPD.PATH}` | `Business Transaction Performance|Business Transactions|mytier|*|*` | Metric path scope used by the master items |
| `{$APPD.TIMERANGETYPE}` | `BEFORE_NOW` | Time range mode |
| `{$APPD.DURATIONINMINUTES}` | `60` | Time window size (minutes) |
| `{$APPD.TIMEOUT}` | `30s` | HTTP timeout |

> Tip: `{$APPD.PATH}` should be broad enough to include all tiers/BTs you want discovered.

---

## Validation & Troubleshooting

### Validate API Access (from Zabbix server/proxy)

~~~bash
curl -sS -u "<USER>:<PASS>" \
  "<APPD_URL>/rest/applications/<APP_NAME>/metric-data?metric-path=<METRIC_PATH>&time-range-type=BEFORE_NOW&duration-in-mins=60&output=JSON" | head -n 50
~~~

Expected:
- HTTP 200
- JSON array containing objects with `metricPath` and `metricValues`

### If discovery returns no BTs
- Confirm `{$APPD.PATH}` matches your environment (tier/BT naming).
- Ensure the response contains `Business Transaction Performance|Business Transactions|...` metric paths.
- Check the discovery rule preprocessing (JavaScript) for errors.

### If items show 0 unexpectedly
- Confirm the metric path exists for the selected time window (`{$APPD.DURATIONINMINUTES}`).
- If there was no traffic (CPM=0), some SLA items intentionally return:
  - Availability/Performance = 100
  - Error/Slow = 0
  - Apdex SLA = 1

---

## Security Notes

- Basic authentication credentials are sensitive:
  - Store `{$APPD.PASS}` as a **Secret macro**
  - Restrict host/template permissions in Zabbix
- Use HTTPS and keep certificates valid/trusted where possible.
- Consider using a dedicated read-only API user in AppDynamics.

---

## Contributing

Contributions are welcome, including:
- Additional SLA models (e.g., pure ratio 0..1 for performance/error)
- Additional BT metrics (stalls, errors by type, percentile response times)
- Trigger prototypes and dashboards for SLA thresholds
- Documentation improvements and tested examples

Please open an issue with:
- Zabbix version
- AppDynamics Controller version
- Sanitized sample metric-data response
- Expected vs. actual behavior

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by Cisco/AppDynamics.
