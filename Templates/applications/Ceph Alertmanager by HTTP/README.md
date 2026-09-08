# Ceph Alertmanager Monitoring for Zabbix 7.0

Zabbix 7.0 template for monitoring Ceph alerts through the Prometheus Alertmanager API v2 using a Zabbix HTTP Agent master item, dependent items, Low-Level Discovery (LLD), and automatically generated trigger prototypes.

The template provides agentless alert monitoring for Ceph environments. No Zabbix Agent installation is required on Ceph nodes for this integration.

Alertmanager is queried through:

```text
/api/v2/alerts
```

The returned JSON payload is processed inside Zabbix to discover active alerts, create per-alert items, map Alertmanager severity levels to Zabbix severities, and automatically recover Zabbix problems when alerts disappear from Alertmanager.

---

## Features

- Designed for Zabbix 7.0
- Agentless Ceph alert monitoring
- Uses the Alertmanager API v2
- Single HTTP Agent master request
- Dependent item architecture
- Low-Level Discovery of active alerts
- Individual Zabbix problem generation for each Alertmanager alert
- Alertmanager fingerprint used as the unique alert identifier
- Automatic recovery when an Alertmanager alert disappears
- Alert severity mapping through LLD overrides
- API availability monitoring
- Aggregate alert counters
- Common Ceph labels automatically discovered
- Missing labels safely normalized
- No scripts or external collectors required

---

## Contents

```text
.
├── zabbix_7.0_ceph_alertmanager_by_http_v1.0.yaml
├── LICENSE
└── README.md
```

---

## Monitoring architecture

The template uses one HTTP Agent master item to retrieve all alerts from Alertmanager.

```text
Ceph
  │
  │
  ▼
Prometheus / Ceph Monitoring Stack
  │
  │
  ▼
Alertmanager
  │
  │  HTTP API v2
  │  GET /api/v2/alerts
  ▼
Zabbix Server / Zabbix Proxy
  │
  ├── HTTP Agent master item
  │
  ├── Dependent aggregate items
  │
  └── Low-Level Discovery
        │
        ├── Per-alert raw data
        ├── Alert state
        ├── Alert status
        ├── Summary
        ├── Description
        ├── Start time
        └── Trigger prototype
```

Only one HTTP request is sent to Alertmanager for each polling interval.

All additional metrics and discovered alerts are processed as dependent items inside Zabbix.

---

## Requirements

- Zabbix Server or Zabbix Proxy 7.0
- Network connectivity from the Zabbix Server or Proxy to Alertmanager
- Alertmanager API v2
- HTTP access to the Alertmanager endpoint
- JSON response from:

```text
/api/v2/alerts
```

The template does not require:

- Zabbix Agent on Ceph nodes
- External scripts
- Python collectors
- SNMP access to Ceph nodes
- Direct Ceph API access

---

## 1. Verify Alertmanager API access

Before importing the template, verify that the Zabbix Server or Proxy can reach Alertmanager.

Example:

```bash
curl -sS http://172.16.100.3:9093/api/v2/alerts
```

For formatted JSON output:

```bash
curl -sS http://172.16.100.3:9093/api/v2/alerts | jq .
```

A successful response should return a JSON array.

Example:

```json
[
  {
    "annotations": {
      "description": "Ceph cluster health is in ERROR state.",
      "summary": "Ceph health error"
    },
    "labels": {
      "alertname": "CephHealthError",
      "severity": "critical",
      "cluster": "ceph"
    },
    "startsAt": "2026-09-08T10:00:00Z",
    "status": {
      "state": "active"
    },
    "fingerprint": "abcdef1234567890"
  }
]
```

An empty Alertmanager instance may return:

```json
[]
```

This is also a valid response.

---

## 2. Import the Zabbix template

In the Zabbix frontend:

```text
Data collection → Templates → Import
```

Import:

```text
zabbix_7.0_ceph_alertmanager_by_http_v1.0.yaml
```

After a successful import, the template name should be:

```text
Ceph Alertmanager by HTTP
```

The template is created under:

```text
Templates/Applications
```

---

## 3. Create the Zabbix host

Create a logical host for the Ceph Alertmanager integration.

In the Zabbix frontend:

```text
Data collection → Hosts → Create host
```

Example configuration:

```text
Host name: ceph-alertmanager
Visible name: Ceph Alertmanager
Host groups: Applications
Monitored by: Zabbix Server or the appropriate Zabbix Proxy
Status: Enabled
```

No Agent, SNMP, JMX, or IPMI interface is required.

Link the following template:

```text
Ceph Alertmanager by HTTP
```

> The HTTP request is executed by the Zabbix Server or Proxy responsible for monitoring this host. Make sure that system can reach the Alertmanager endpoint.

---

## 4. Template macros

The template uses the following macros:

| Macro | Default | Description |
|---|---|---|
| `{$CEPH.ALERTMANAGER.URL}` | `http://172.16.100.3:9093` | Alertmanager base URL. Do not append `/api/v2/alerts`. |
| `{$CEPH.ALERTMANAGER.INTERVAL}` | `1m` | Alertmanager polling interval. |
| `{$CEPH.ALERTMANAGER.TIMEOUT}` | `10s` | HTTP request timeout. |
| `{$CEPH.ALERTMANAGER.LLD.STATUS.MATCHES}` | `^active$` | Alert states that should be discovered by LLD. |

The complete API URL is automatically built as:

```text
{$CEPH.ALERTMANAGER.URL}/api/v2/alerts
```

For example:

```text
http://172.16.100.3:9093/api/v2/alerts
```

For environments using a different Alertmanager address, override the macro on the host:

```text
{$CEPH.ALERTMANAGER.URL}
```

Example:

```text
http://alertmanager.example.local:9093
```

---

## 5. Master item

The main HTTP Agent item is:

```text
Ceph Alertmanager: Get alerts
```

Item key:

```text
ceph.alertmanager.alerts.get
```

Request:

```text
GET {$CEPH.ALERTMANAGER.URL}/api/v2/alerts
```

Expected HTTP status:

```text
200
```

Expected response:

```text
JSON array
```

The master item stores the raw Alertmanager response and acts as the data source for all dependent items and the discovery rule.

---

## 6. Aggregate alert items

The template creates the following dependent items from the master Alertmanager response.

### Returned alert count

```text
Ceph Alertmanager: Returned alert count
```

Key:

```text
ceph.alertmanager.alerts.total.count
```

Returns the total number of alert objects contained in the API response.

---

### Active alert count

```text
Ceph Alertmanager: Active alert count
```

Key:

```text
ceph.alertmanager.alerts.active.count
```

Counts alerts where:

```text
status.state = active
```

---

### Active critical alert count

```text
Ceph Alertmanager: Active critical alert count
```

Key:

```text
ceph.alertmanager.alerts.critical.count
```

Counts alerts matching:

```text
status.state = active
labels.severity = critical
```

---

### Active warning alert count

```text
Ceph Alertmanager: Active warning alert count
```

Key:

```text
ceph.alertmanager.alerts.warning.count
```

Counts alerts matching:

```text
status.state = active
labels.severity = warning
```

---

## 7. Alert discovery

Low-Level Discovery is performed by:

```text
Ceph Alertmanager: Alert discovery
```

Key:

```text
ceph.alertmanager.alert.discovery
```

By default, only alerts matching the following status are discovered:

```text
^active$
```

This behavior can be changed using:

```text
{$CEPH.ALERTMANAGER.LLD.STATUS.MATCHES}
```

The Alertmanager `fingerprint` value is used as the unique identifier for each discovered alert.

---

## Discovered labels

The discovery process extracts common Ceph and Prometheus Alertmanager labels.

| LLD macro | Source |
|---|---|
| `{#FINGERPRINT}` | Alertmanager alert fingerprint |
| `{#ALERTNAME}` | `labels.alertname` |
| `{#SEVERITY}` | `labels.severity` |
| `{#CLUSTER}` | `labels.cluster` |
| `{#INSTANCE}` | `labels.instance` |
| `{#HOSTNAME}` | `labels.hostname`, `labels.nodename`, or `labels.host` |
| `{#CEPH_DAEMON}` | `labels.ceph_daemon` or `labels.daemon` |
| `{#DEVICE}` | `labels.device` |
| `{#TYPE}` | `labels.type` |
| `{#STATUS}` | `status.state` |
| `{#STARTSAT}` | `startsAt` |
| `{#TARGET}` | Automatically selected alert target |

Missing labels are normalized to:

```text
-
```

This prevents empty values from creating unusable item names, trigger names, or tags.

---

## Target selection

The template automatically determines the most useful target for the Zabbix problem name.

The priority is:

```text
hostname
   │
   ▼
instance
   │
   ▼
ceph_daemon
   │
   ▼
device
   │
   ▼
cluster
```

The selected value becomes:

```text
{#TARGET}
```

For example:

```text
[Ceph] CephHealthError: ceph-node01
```

or:

```text
[Ceph] CephOSDDown: osd.12
```

---

## 8. Discovered items

Six dependent item prototypes are created for every discovered Alertmanager alert.

### Raw alert

```text
[Alertmanager] {#ALERTNAME}: Raw alert
```

Key:

```text
ceph.alertmanager.alert.raw[{#FINGERPRINT}]
```

Contains the complete JSON object for the individual Alertmanager alert.

---

### Active state

```text
[Alertmanager] {#ALERTNAME}: Active state
```

Key:

```text
ceph.alertmanager.alert.active[{#FINGERPRINT}]
```

Values:

| Value | Meaning |
|---:|---|
| `0` | RESOLVED |
| `1` | ACTIVE |

The template includes the following value map:

```text
Ceph Alertmanager alert state
```

---

### Status

```text
[Alertmanager] {#ALERTNAME}: Status
```

Key:

```text
ceph.alertmanager.alert.status[{#FINGERPRINT}]
```

Typical values:

```text
active
resolved
```

---

### Summary

```text
[Alertmanager] {#ALERTNAME}: Summary
```

Key:

```text
ceph.alertmanager.alert.summary[{#FINGERPRINT}]
```

Returns:

```text
annotations.summary
```

---

### Description

```text
[Alertmanager] {#ALERTNAME}: Description
```

Key:

```text
ceph.alertmanager.alert.description[{#FINGERPRINT}]
```

Returns:

```text
annotations.description
```

---

### Starts at

```text
[Alertmanager] {#ALERTNAME}: Starts at
```

Key:

```text
ceph.alertmanager.alert.startsat[{#FINGERPRINT}]
```

Returns the Alertmanager:

```text
startsAt
```

timestamp.

---

## 9. Trigger prototype

Each discovered active alert generates an individual Zabbix problem.

Trigger name:

```text
[Ceph] {#ALERTNAME}: {#TARGET}
```

Trigger expression:

```text
last(/Ceph Alertmanager by HTTP/ceph.alertmanager.alert.active[{#FINGERPRINT}])=1
```

Example problems:

```text
[Ceph] CephHealthError: ceph-node01
[Ceph] CephOSDDown: osd.12
[Ceph] CephPoolNearFull: ceph-cluster
```

The trigger also contains useful Alertmanager information in its description:

```text
Alert name
Alertmanager severity
Cluster
Target
Instance
Hostname
Ceph daemon
Device
Type
Fingerprint
Starts at
```

---

## Severity mapping

The default trigger prototype severity is:

```text
Average
```

LLD overrides automatically map Alertmanager severity labels to Zabbix severities.

| Alertmanager severity | Zabbix severity |
|---|---|
| `critical` | High |
| `error` | High |
| `warning` | Warning |
| `info` | Information |
| `information` | Information |
| `none` | Information |
| Unknown / other | Average |

This allows the severity provided by the Ceph monitoring stack to be preserved when the corresponding Zabbix problem is created.

---

## Trigger tags

Generated alert problems contain tags that can be used for event filtering, actions, services, dashboards, and reporting.

Main tags include:

```text
alertname
cluster
fingerprint
instance
platform
severity
source
type
```

Example:

```text
alertname = CephHealthError
cluster   = ceph
platform  = ceph
severity  = critical
source    = alertmanager
```

---

## 10. Automatic recovery behavior

Alert recovery is handled automatically.

When an alert is present in Alertmanager:

```text
status.state = active
```

the discovered Active state item becomes:

```text
1
```

and the Zabbix trigger enters the PROBLEM state.

When the alert disappears from the `/api/v2/alerts` response, the per-alert raw dependent item generates a synthetic response:

```json
{
  "fingerprint": "<fingerprint>",
  "status": {
    "state": "resolved"
  },
  "labels": {},
  "annotations": {},
  "startsAt": ""
}
```

The Active state item then becomes:

```text
0
```

and the Zabbix problem automatically returns to OK.

This avoids waiting for the LLD lifetime before recovering the Zabbix problem.

---

## LLD lifetime

The discovery rule uses:

```text
Lost resources period: 7d
Disable lost resources: 1h
```

This means a discovered alert can remain in Zabbix temporarily after it disappears from Alertmanager.

The alert itself is still recovered immediately through the synthetic resolved-state mechanism.

---

## 11. Alertmanager API availability trigger

The template also monitors whether usable data continues to arrive from Alertmanager.

Trigger:

```text
Ceph Alertmanager: API data not received for 5 minutes
```

Expression:

```text
nodata(/Ceph Alertmanager by HTTP/ceph.alertmanager.alerts.active.count,5m)=1
```

Severity:

```text
High
```

This trigger protects against cases such as:

- Alertmanager is unavailable
- Network connectivity is lost
- TCP port 9093 is blocked
- The Alertmanager URL is incorrect
- HTTP authentication is required
- TLS configuration is incorrect
- Alertmanager returns an unexpected response
- The JSON payload cannot be processed

An API communication failure does **not** automatically resolve existing Ceph problems.

If the HTTP Agent master item receives no new value, existing alert states remain unchanged and the dedicated API availability trigger is generated instead.

This prevents false recovery of Ceph alerts during an Alertmanager outage.

---

## 12. Verify monitoring after import

After linking the template, open:

```text
Monitoring → Latest data
```

Check the following item first:

```text
Ceph Alertmanager: Get alerts
```

It should contain a valid JSON array.

Then verify:

```text
Ceph Alertmanager: Returned alert count
Ceph Alertmanager: Active alert count
Ceph Alertmanager: Active critical alert count
Ceph Alertmanager: Active warning alert count
```

If active alerts exist, check the discovered items:

```text
[Alertmanager] <alert name>: Raw alert
[Alertmanager] <alert name>: Active state
[Alertmanager] <alert name>: Status
[Alertmanager] <alert name>: Summary
[Alertmanager] <alert name>: Description
[Alertmanager] <alert name>: Starts at
```

Generated problems can be checked under:

```text
Monitoring → Problems
```

---

## 13. Manual API tests

### Basic connectivity test

```bash
curl -v http://172.16.100.3:9093/api/v2/alerts
```

### Display formatted JSON

```bash
curl -sS http://172.16.100.3:9093/api/v2/alerts | jq .
```

### Count returned alerts

```bash
curl -sS http://172.16.100.3:9093/api/v2/alerts | jq 'length'
```

### Show active alerts

```bash
curl -sS http://172.16.100.3:9093/api/v2/alerts \
  | jq '.[] | select(.status.state == "active")'
```

### Display selected labels

```bash
curl -sS http://172.16.100.3:9093/api/v2/alerts \
  | jq '.[] | {
      alertname: .labels.alertname,
      severity: .labels.severity,
      cluster: .labels.cluster,
      instance: .labels.instance,
      ceph_daemon: .labels.ceph_daemon,
      device: .labels.device,
      status: .status.state,
      fingerprint: .fingerprint
    }'
```

---

## Authentication

The current template is configured for an Alertmanager endpoint that does not require authentication.

The master HTTP Agent item sends:

```text
Accept: application/json
```

No username, password, Bearer token, or other authentication information is included in the template.

If Alertmanager requires authentication, edit:

```text
Data collection
  → Templates
  → Ceph Alertmanager by HTTP
  → Items
  → Ceph Alertmanager: Get alerts
```

and configure the appropriate authentication mechanism.

For Basic Authentication, it is recommended to create host/template macros such as:

```text
{$CEPH.ALERTMANAGER.USER}
{$CEPH.ALERTMANAGER.PASSWORD}
```

and store the password as a secret macro.

---

## HTTPS and TLS

The current example endpoint uses HTTP:

```text
http://172.16.100.3:9093
```

If Alertmanager is exposed through HTTPS, change:

```text
{$CEPH.ALERTMANAGER.URL}
```

for example:

```text
https://alertmanager.example.local:9093
```

The template currently has:

```text
Verify peer: No
Verify host: No
```

For production HTTPS environments, certificate validation should be enabled after the appropriate CA certificate has been installed and trusted by the Zabbix Server or Proxy.

---

## Troubleshooting

### `Ceph Alertmanager: Get alerts` is unsupported

Verify connectivity from the Zabbix Server or Proxy:

```bash
curl -v http://172.16.100.3:9093/api/v2/alerts
```

Check:

- Alertmanager address
- TCP port
- Firewall rules
- Routing
- HTTP/HTTPS protocol
- Authentication requirements

---

### HTTP 401 Unauthorized

The Alertmanager endpoint requires authentication.

Configure the master HTTP Agent item with the authentication mechanism required by the environment.

---

### HTTP 403 Forbidden

The endpoint is reachable, but access is not permitted.

Check the reverse proxy, authentication configuration, or access-control rules in front of Alertmanager.

---

### Connection refused

Example:

```text
curl: (7) Failed to connect
```

Check whether Alertmanager is listening on the configured address and port.

Useful tests:

```bash
ss -lntp | grep 9093
```

or from the Zabbix Server/Proxy:

```bash
nc -vz 172.16.100.3 9093
```

---

### Request times out

Check:

- Firewall rules
- Network routing
- Alertmanager availability
- Proxy-to-Ceph network access
- `{$CEPH.ALERTMANAGER.TIMEOUT}`

Default:

```text
10s
```

---

### Master item works but no alerts are discovered

First inspect:

```text
Ceph Alertmanager: Get alerts
```

Verify that alerts contain:

```json
"status": {
  "state": "active"
}
```

The default LLD filter is:

```text
{$CEPH.ALERTMANAGER.LLD.STATUS.MATCHES} = ^active$
```

Also verify that each alert contains a valid:

```text
fingerprint
```

Alerts without a fingerprint are not discovered.

---

### Severity is not mapped as expected

Inspect:

```text
labels.severity
```

Expected values handled by the default overrides are:

```text
critical
error
warning
info
information
none
```

Any other value keeps the default Zabbix trigger severity:

```text
Average
```

---

### Problem target shows `-`

Not every Ceph alert contains host, instance, daemon, or device information.

The template attempts to determine the target using:

```text
hostname
→ instance
→ ceph_daemon
→ device
→ cluster
```

If none of these labels are present, the target may be displayed as:

```text
-
```

The original labels can always be inspected in the corresponding:

```text
Raw alert
```

item.

---

## Known limitations

- This template monitors alerts exposed by Alertmanager; it does not directly collect Ceph performance or capacity metrics.
- Alert discovery depends on the Alertmanager API v2 JSON structure.
- Alert uniqueness depends on the Alertmanager `fingerprint`.
- The quality of Zabbix problem names depends on the labels provided by Ceph/Prometheus alert rules.
- Custom Ceph alert rules may use different label names.
- Alerts without a fingerprint are ignored by discovery.
- Only `active` alerts are discovered by default.
- The current template does not include authentication credentials.
- HTTP is used by the supplied example endpoint.
- Alertmanager silencing and inhibition behavior is controlled by Alertmanager and is not managed by this template.

For additional Ceph metrics such as OSD utilization, pool capacity, PG state, latency, throughput, MON status, or cluster performance, a dedicated Ceph monitoring template should be used alongside this Alertmanager integration.

---

## Security notes

- Do not expose the Alertmanager API directly to untrusted networks.
- Restrict TCP/9093 access to required monitoring systems.
- Prefer HTTPS for communication across untrusted network segments.
- Enable authentication where supported by the environment.
- Store passwords and tokens as Zabbix secret macros.
- Do not commit credentials to a public GitHub repository.
- Replace environment-specific addresses and values before publishing reusable templates.
- Restrict Zabbix Server/Proxy network access according to the principle of least privilege.

---

## Compatibility

Prepared for:

```text
Zabbix 7.0
Prometheus Alertmanager API v2
Ceph monitoring environments
```

Template:

```text
Ceph Alertmanager by HTTP
```

Template file:

```text
zabbix_7.0_ceph_alertmanager_by_http_v1.0.yaml
```

---

## License

Licensed under the MIT License. See the LICENSE file for details.
