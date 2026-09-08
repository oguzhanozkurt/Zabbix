# OpenShift Alertmanager by HTTP (Zabbix 7.0 Template)

This repository provides a Zabbix template to collect and monitor **OpenShift Alertmanager alerts** through the **Alertmanager v2 API** using a Zabbix **HTTP agent** master item.

- Template name: **OpenShift Alertmanager by HTTP**
- Zabbix export: **7.0**
- File: `zabbix_7.0_openshift_alertmanager_by_http_v1.1.yaml`
- API endpoint: `/api/v2/alerts`
- Collection method: **HTTP agent master item** → **Dependent counters** → **Dependent LLD** → **Per-alert dependent items** → **Trigger prototypes**

> Note: This is a community template and is not an official Red Hat, OpenShift, Prometheus Alertmanager, or Zabbix release.

---

## What’s Included

### Alertmanager API Collection
- Collects raw Alertmanager alert data from `/api/v2/alerts`
- Uses Bearer token authentication
- Stores the raw JSON response for troubleshooting
- Polling interval and timeout are macro-driven

### Aggregate Alert Counters
The template creates dependent counters from the raw Alertmanager response:

- Returned alert count
- Active alert count
- Active critical alert count
- Active warning alert count

### Alert Discovery (LLD)
The template discovers individual Alertmanager alerts using the alert fingerprint as the unique identifier.

Discovered LLD macros include:

- `{#FINGERPRINT}`
- `{#ALERTNAME}`
- `{#SEVERITY}`
- `{#NAMESPACE}`
- `{#POD}`
- `{#INSTANCE}`
- `{#STATUS}`
- `{#STARTSAT}`

### Per-Alert Items
For each discovered alert, the template creates:

- Raw alert JSON
- Numeric active state
- Alert status
- Alert summary
- Alert description
- Alert start timestamp

### Trigger Prototype
A trigger is created for each active Alertmanager alert.

Trigger severity is automatically adjusted by LLD overrides based on Alertmanager severity:

- `critical` / `error` → High
- `warning` → Warning
- `info` / `information` / `none` → Information
- Other values → Default trigger severity

---

## Requirements

- Zabbix Server/Proxy: **7.0** or compatible newer versions
- Zabbix Proxy preferably running inside the OpenShift/Kubernetes network
- Network access from Zabbix Proxy to Alertmanager:
  - Default internal service URL: `https://alertmanager-main.openshift-monitoring.svc:9094`
- A valid Bearer token with permission to access Alertmanager API
- HTTP/HTTPS access to:
  - `/api/v2/alerts`

---

## Quick Start

### 1) Import the Template

Zabbix UI:

~~~text
Data collection → Templates → Import
~~~

Import:

~~~text
zabbix_7.0_openshift_alertmanager_by_http_v1.1.yaml
~~~

After import, the template name should be:

~~~text
OpenShift Alertmanager by HTTP
~~~

---

### 2) Create or Select the Monitoring Host

Create a logical host for Alertmanager monitoring.

Example:

~~~text
Host name: OpenShift Alertmanager
Visible name: OpenShift Alertmanager
Host group: Templates/Applications or your OpenShift/Kubernetes group
Monitored by: Zabbix Proxy running in OpenShift
Interface: Not required for HTTP agent, but can be added for inventory consistency
~~~

Link the template:

~~~text
OpenShift Alertmanager by HTTP
~~~

---

### 3) Configure Required Macros

Set these macros at host level:

| Macro | Default | Description |
|---|---|---|
| `{$OPENSHIFT.ALERTMANAGER.URL}` | `https://alertmanager-main.openshift-monitoring.svc:9094` | Base URL of the OpenShift Alertmanager service. |
| `{$OPENSHIFT.ALERTMANAGER.TOKEN}` | empty / secret | Bearer token used to access Alertmanager API. Store as a **Secret macro**. |
| `{$OPENSHIFT.ALERTMANAGER.INTERVAL}` | `1m` | Polling interval for the master HTTP item. |
| `{$OPENSHIFT.ALERTMANAGER.TIMEOUT}` | `10s` | HTTP request timeout. |
| `{$OPENSHIFT.ALERTMANAGER.LLD.STATUS.MATCHES}` | `^active$` | Regex for Alertmanager `status.state` values that should be discovered. |

Recommended host-level configuration:

~~~text
{$OPENSHIFT.ALERTMANAGER.URL}=https://alertmanager-main.openshift-monitoring.svc:9094
{$OPENSHIFT.ALERTMANAGER.TOKEN}=<SECRET_BEARER_TOKEN>
{$OPENSHIFT.ALERTMANAGER.INTERVAL}=1m
{$OPENSHIFT.ALERTMANAGER.TIMEOUT}=10s
{$OPENSHIFT.ALERTMANAGER.LLD.STATUS.MATCHES}=^active$
~~~

---

## Token / RBAC Preparation

The template expects a Bearer token and sends it in the HTTP header:

~~~text
Authorization: Bearer <token>
~~~

Create or use a service account that has sufficient permission to query Alertmanager alerts.

Example OpenShift workflow:

~~~bash
oc project openshift-monitoring

oc create serviceaccount zabbix-alertmanager-reader -n openshift-monitoring

oc adm policy add-cluster-role-to-user cluster-monitoring-view \
  -z zabbix-alertmanager-reader \
  -n openshift-monitoring
~~~

Create a token.

For newer OpenShift/Kubernetes versions:

~~~bash
oc create token zabbix-alertmanager-reader -n openshift-monitoring
~~~

For older versions using service account token secrets, retrieve the generated token from the related secret.

After obtaining the token, configure it in Zabbix as:

~~~text
{$OPENSHIFT.ALERTMANAGER.TOKEN}
~~~

Use a **Secret macro** and avoid storing the token in plain text documentation, screenshots, or tickets.

> RBAC requirements may vary depending on your OpenShift version, security model, and Alertmanager exposure method. Use the least-privilege role that allows reading Alertmanager alerts.

---

## How It Works

### Master Item

The template uses one HTTP agent master item:

- Name: `OpenShift Alertmanager: Get alerts`
- Key: `openshift.alertmanager.alerts.get`
- Type: HTTP agent
- URL: `{$OPENSHIFT.ALERTMANAGER.URL}/api/v2/alerts`
- Method: `GET`
- Expected status code: `200`
- Retrieve mode: Body
- Output format: Raw
- Value type: Text
- History: 1 day

Headers:

~~~text
Authorization: Bearer {$OPENSHIFT.ALERTMANAGER.TOKEN}
Accept: application/json
~~~

TLS peer and host verification are disabled by default in the template to simplify initial usage with OpenShift internal service certificates.

For production, it is recommended to trust the OpenShift service CA in the Zabbix Proxy container and then enable TLS peer/host verification.

---

## Aggregate Items

The following dependent items are calculated from the master Alertmanager response:

| Item | Key | Description |
|---|---|---|
| OpenShift Alertmanager: Returned alert count | `openshift.alertmanager.alerts.total.count` | Total number of alert objects returned by the API. |
| OpenShift Alertmanager: Active alert count | `openshift.alertmanager.alerts.active.count` | Number of alerts where `status.state` is `active`. |
| OpenShift Alertmanager: Active critical alert count | `openshift.alertmanager.alerts.critical.count` | Number of active alerts where `labels.severity` is `critical`. |
| OpenShift Alertmanager: Active warning alert count | `openshift.alertmanager.alerts.warning.count` | Number of active alerts where `labels.severity` is `warning`. |

---

## Low-Level Discovery

### Alert Discovery

- Discovery name: `OpenShift Alertmanager: Alert discovery`
- Key: `openshift.alertmanager.alert.discovery`
- Type: Dependent
- Master item: `openshift.alertmanager.alerts.get`
- Lifetime: `7d`
- Disable after: `1h`

The discovery rule parses the Alertmanager JSON array and creates one discovered entity per alert fingerprint.

Discovery filtering:

| Macro | Filter |
|---|---|
| `{#STATUS}` | `{$OPENSHIFT.ALERTMANAGER.LLD.STATUS.MATCHES}` |
| `{#FINGERPRINT}` | `.+` |

By default, only active alerts are discovered.

Missing labels are normalized to `-` so item names, trigger names, and tags remain usable even when Alertmanager labels are incomplete.

---

## Per-Alert Item Prototypes

For each discovered alert fingerprint, the template creates these items:

| Item | Key | Type |
|---|---|---|
| `[Alertmanager] {#ALERTNAME}: Raw alert` | `openshift.alertmanager.alert.raw[{#FINGERPRINT}]` | Text |
| `[Alertmanager] {#ALERTNAME}: Active state` | `openshift.alertmanager.alert.active[{#FINGERPRINT}]` | Numeric |
| `[Alertmanager] {#ALERTNAME}: Status` | `openshift.alertmanager.alert.status[{#FINGERPRINT}]` | Character |
| `[Alertmanager] {#ALERTNAME}: Summary` | `openshift.alertmanager.alert.summary[{#FINGERPRINT}]` | Text |
| `[Alertmanager] {#ALERTNAME}: Description` | `openshift.alertmanager.alert.description[{#FINGERPRINT}]` | Text |
| `[Alertmanager] {#ALERTNAME}: Starts at` | `openshift.alertmanager.alert.startsat[{#FINGERPRINT}]` | Character |

### Recovery Behavior

When an alert disappears from the Alertmanager response:

- The raw alert prototype emits a synthetic resolved JSON object.
- The active state item becomes `0`.
- The related trigger returns to OK.

If the API request itself fails:

- The master item does not receive a new value.
- Existing alert states are preserved.
- A separate API data-not-received trigger fires.
- Alerts are not falsely resolved due to API failure.

---

## Triggers Included

### API Availability

| Trigger | Severity | Description |
|---|---|---|
| `OpenShift Alertmanager: API data not received for 5 minutes` | High | Fires when processed active alert counter data is not received for 5 minutes. |

Recommended checks when this trigger fires:

- Alertmanager service URL
- DNS resolution from the Zabbix Proxy pod
- Network reachability from Zabbix Proxy to Alertmanager
- Bearer token validity
- RBAC permissions
- TLS configuration
- JSON response format

### Alert Trigger Prototype

| Trigger prototype | Default severity | Description |
|---|---|---|
| `[OpenShift] {#ALERTNAME}: {#NAMESPACE}/{#POD}` | Average | Opens when the discovered alert active state is `1`. |

The trigger description includes:

- Alert name
- Alertmanager severity
- Namespace
- Pod
- Instance
- Fingerprint
- Starts at

The full Alertmanager annotations are available in the discovered Summary, Description, and Raw alert items.

---

## Severity Mapping

LLD overrides change trigger prototype severity based on `{#SEVERITY}`.

| Alertmanager severity | Zabbix severity |
|---|---|
| `critical`, `error` | High |
| `warning` | Warning |
| `info`, `information`, `none` | Information |
| Other / unknown | Default trigger severity |

---

## Value Maps

### OpenShift Alertmanager alert state

| Value | Meaning |
|---:|---|
| `0` | RESOLVED |
| `1` | ACTIVE |

---

## Validation & Troubleshooting

### Validate Alertmanager API from the Zabbix Proxy Pod

Run from the Zabbix Proxy pod or from an equivalent debug pod in the same namespace/network path:

~~~bash
curl -k -sS \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Accept: application/json" \
  "https://alertmanager-main.openshift-monitoring.svc:9094/api/v2/alerts" | head -n 50
~~~

Expected:

- HTTP 200
- JSON array response
- Alert objects with fields such as:
  - `labels`
  - `annotations`
  - `status`
  - `startsAt`
  - `fingerprint`

### Validate JSON Shape

You can check whether the response is a JSON array:

~~~bash
curl -k -sS \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Accept: application/json" \
  "https://alertmanager-main.openshift-monitoring.svc:9094/api/v2/alerts" | jq 'type'
~~~

Expected:

~~~text
"array"
~~~

### If You See “API data not received for 5 minutes”

Check:

- `{$OPENSHIFT.ALERTMANAGER.URL}` is correct.
- Zabbix Proxy can resolve `alertmanager-main.openshift-monitoring.svc`.
- Zabbix Proxy can reach TCP/9094.
- `{$OPENSHIFT.ALERTMANAGER.TOKEN}` is valid.
- The token has permission to query Alertmanager.
- TLS/certificate behavior matches your environment.
- Alertmanager returns a valid JSON array.

### If LLD Discovers No Alerts

Check:

- The API returns active alerts.
- The Alertmanager response includes `fingerprint`.
- `status.state` matches `{$OPENSHIFT.ALERTMANAGER.LLD.STATUS.MATCHES}`.
- Default filter is `^active$`; resolved/suppressed alerts may not be discovered.
- Discovery preprocessing has no JavaScript errors.

### If Alerts Do Not Recover

Check:

- The master item is still collecting fresh data.
- The alert has disappeared from `/api/v2/alerts`.
- The raw alert item returns the synthetic resolved object.
- The active state item becomes `0`.

### If TLS Fails

The template disables TLS peer/host validation by default for initial deployment.

For production hardening:

1. Export or mount the OpenShift service CA certificate into the Zabbix Proxy container.
2. Configure the trust store in the container image/runtime.
3. Enable TLS peer verification on the HTTP master item.
4. Enable TLS host verification when the hostname and certificate SANs match.

---

## Security Notes

- Store `{$OPENSHIFT.ALERTMANAGER.TOKEN}` as a **Secret macro**.
- Use the least-privilege service account/RBAC permissions required for read-only Alertmanager access.
- Restrict access to Zabbix host/template macros.
- Avoid putting Bearer tokens into screenshots, tickets, Git history, or logs.
- Limit network access from Zabbix Proxy to OpenShift monitoring endpoints.
- For production, enable TLS certificate validation after trusting the OpenShift service CA.

---

## Contributing

Contributions are welcome, including:

- Additional aggregate counters
- Improved label/annotation extraction
- Additional severity mapping rules
- Dashboard examples
- Support for grouping by namespace, pod, service, or alertname
- Documentation improvements and tested examples

Please open an issue with:

- Zabbix version
- OpenShift version
- Alertmanager response sample with sensitive data removed
- Expected vs. actual behavior
- Preprocessing error details, if any

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by Red Hat, OpenShift, Prometheus Alertmanager, or Zabbix.
