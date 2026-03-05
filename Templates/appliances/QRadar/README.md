# QRadar by HTTP (Zabbix Template)

This repository provides a Zabbix template to monitor **IBM QRadar Offenses (OPEN)** via the **QRadar REST API** using **HTTP Agent** items and **dependent LLD**.

- Template name: **QRadar by HTTP**
- Zabbix export: **7.0**
- File: **QRadar by HTTP.yaml**
- API endpoint: `/api/siem/offenses` (filtered to `status="OPEN"`)

> Note: This is a community template and is not an official IBM release.

---

## What’s Included

### Bulk Offense Retrieval (HTTP Agent)
- A single HTTP agent master item pulls **OPEN offenses** from QRadar.
- The response is stored as **TEXT** and retained for troubleshooting (history enabled).

### Automated Discovery (LLD) for Offenses
- A dependent discovery rule parses the master JSON response and creates per-offense entities.
- Each offense is represented by LLD macros:
  - `{#OFFENSE_ID}`
  - `{#OFFENSE_SOURCE}`
  - `{#DESCRIPTION}`
  - `{#CATEGORIES}`
  - `{#TYPE_NAME}` (unique log source type names)

### Per-Offense Items (Dependent + Calculated)
For each discovered offense, the template creates:
- **Dependent TEXT items** parsed from the master JSON:
  - Offense source
  - Categories
  - Description (single-line, trimmed)
  - Log source type names (unique list)
- A **Calculated TEXT item** used for dashboard navigation/tagging:
  - `all.values[{#OFFENSE_ID}]`

### Dashboard (Included)
- A dashboard page named **“QRadar All Values”** with an **Item navigator** widget
- The widget filters items by tag:
  - `QRadar: All Values`

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- IBM QRadar with REST API access enabled
- Network access: Zabbix → QRadar (TCP 443 by default)
- A valid QRadar **Authorized Services Token** (sent via the `SEC` header)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `QRadar by HTTP.yaml`

### 2) Create/Update the Host
Zabbix UI → **Data collection → Hosts → Create host**
- Create a host (e.g., `QRadar`)
- Link the template: **QRadar by HTTP**

### 3) Configure Macros (Required)
Set macros at **host level**:

| Macro | Example | Description |
|------|---------|-------------|
| `{$QRADAR.URL}` | `https://qradar.company.local` | QRadar base URL |
| `{$QRADAR.TOKEN}` | *(secret)* | Authorized Services Token used in the `SEC` header (store as **Secret macro**) |
| `{$QRADAR.API.VERSION}` | `21.0` | QRadar API version header (use the version from your QRadar API documentation / environment) |
| `{$QRADAR.RANGE}` | `items=0-49` | Range header for pagination (e.g., `items=0-99`) |

---

## How It Works

### Master Item (HTTP Agent)
- **Name:** `QRadar: Offenses raw (OPEN)`
- **Key:** `qradar.offenses.raw`
- **Type:** HTTP agent
- **URL:**
  - `{$QRADAR.URL}/api/siem/offenses?filter=status%3D%22OPEN%22&fields=id,offense_source,categories,description,log_sources(type_name)`
- **Headers:**
  - `SEC: {$QRADAR.TOKEN}`
  - `Version: {$QRADAR.API.VERSION}`
  - `Range: {$QRADAR.RANGE}`
  - `Accept: application/json`

### Discovery Rule (Dependent LLD)
- **Name:** `QRadar: Offense discovery`
- **Key:** `qradar.offense.discovery`
- **Type:** Dependent (master: `qradar.offenses.raw`)
- **Lifetime:** 6d
- **Disable after (enabled lifetime):** 1h

**Preprocessing logic (high level):**
- Parses the JSON array of offenses
- Normalizes:
  - `categories` → `"a, b, c"`
  - `log_sources[].type_name` → unique list `"WindowsAuthServer, IIS"`
  - `description` → single line + trimmed
- Outputs LLD JSON with `{#OFFENSE_*}` macros

### Item Prototypes
Per `{#OFFENSE_ID}`:
- `qradar.offense.source[{#OFFENSE_ID}]` (dependent)
- `qradar.offense.categories[{#OFFENSE_ID}]` (dependent)
- `qradar.offense.description[{#OFFENSE_ID}]` (dependent)
- `qradar.offense.type_name[{#OFFENSE_ID}]` (dependent)
- `all.values[{#OFFENSE_ID}]` (calculated, tagged: `Qradar=All Values`)

---

## Triggers (Included)

### API Data Availability
- **No data has been retrieved from the QRadar API for the past 24 hours.** (DISASTER)
  - Problem: no data for 24h
  - Recovery: data appears again (no data for 10m = false)
  - Manual close: enabled

> This trigger is designed to catch long-term ingestion failures. If you want faster alerting, consider reducing the time window (e.g., 30m–2h) based on your polling interval and operational needs.

---

## Operational Notes

### Pagination / Range Header
The template uses the `Range` header via `{$QRADAR.RANGE}` (default: `items=0-49`).
- If you expect more than 50 open offenses, increase the range (e.g., `items=0-199`).
- For very large environments, consider:
  - multiple master items with different ranges, or
  - additional filtering to reduce payload size.

### Field Selection
The request is optimized to fetch only required fields:
- `id`, `offense_source`, `categories`, `description`, `log_sources(type_name)`

---

## Validation & Troubleshooting

Validate API connectivity and response format from your Zabbix server/proxy:

~~~bash
curl -k -sS \
  -H "SEC: <TOKEN>" \
  -H "Version: <API_VERSION>" \
  -H "Range: items=0-49" \
  -H "Accept: application/json" \
  "https://<QRADAR>/api/siem/offenses?filter=status%3D%22OPEN%22&fields=id,offense_source,categories,description,log_sources(type_name)" | head -n 50
~~~

### If you see “No data has been retrieved from the QRadar API…”
- Confirm network reachability to QRadar (routing/firewall/TLS).
- Verify the `SEC` token is valid and has the required permissions.
- Verify the API `Version` header value matches your QRadar environment.
- Confirm the `Range` header is acceptable and not rejected by a proxy/WAF.
- Check whether QRadar returns an empty array (no OPEN offenses) vs. an error response.

### If LLD creates no entities
- Confirm the master item returns a valid JSON array (`[...]`).
- Confirm offenses contain the expected fields (id, categories, description, log_sources).
- Review Zabbix preprocessing errors on the discovery rule and item prototypes.

---

## Security Notes

QRadar API tokens grant access to security telemetry and may be sensitive.
- Store `{$QRADAR.TOKEN}` as a **Secret macro**.
- Restrict access to Zabbix hosts/templates and macros to authorized administrators only.
- Use HTTPS and validate certificates where possible.
- Apply source IP allow-lists and firewall policies for API access.
- Avoid copying tokens into tickets, logs, or screenshots.

---

## Contributing

Contributions are welcome, including:
- Support for additional offense fields (e.g., magnitude, credibility, relevance)
- Additional filters (e.g., only specific domains/networks)
- Improved pagination strategies for large deployments
- Additional dashboards and problem views

Please open an issue with:
- QRadar version
- Zabbix version
- Sanitized sample API response
- Expected vs. actual behavior (including any preprocessing errors)

## License
Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks
All product names, trademarks, and registered trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by any vendor mentioned in this repository.
