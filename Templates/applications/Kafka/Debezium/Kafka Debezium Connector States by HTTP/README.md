# Debezium Connector States by HTTP (Zabbix Template)

This repository provides a Zabbix template to monitor **Kafka Connect / Debezium connector and task states** by calling the Kafka Connect REST API and converting results into **LLD-based items**.

- Template name: **Debezium Connector States by HTTP**
- Zabbix export: **7.0**
- File: `Debezium Connector States by HTTP.yaml`
- Collection method: **Zabbix Script item (HttpRequest)** → **Dependent LLD** → **Dependent items** (+ state code mapping)

> Note: This is a community template and is not an official Apache Kafka / Debezium release.

---

## What’s Included

## REST API Collection (Master Script Item)
The template uses a single master item that:
1) Calls `GET /connectors` to retrieve the connector list  
2) Calls `GET /connectors/<connector>/status` for each connector
3) Produces a consolidated JSON payload containing connector and task states

Master item:
- **Name:** Kafka Connect: Raw connector statuses  
- **Key:** `kafka.connect.status.raw`  
- **Type:** Script  
- **Value type:** Text (JSON)  
- **History:** 1 day

The master output is shaped as:
- `connectors[]` array
  - connector name, type, state, worker_id
  - tasks[] array (task id, state, worker_id)
  - `error` field if a connector status call fails

---

## Automated Discovery (LLD)

## 1) Connector Discovery
- **Discovery name:** Kafka Connect: Connector discovery  
- **Key:** `kafka.connect.connector.discovery`  
- **Type:** Dependent (master: `kafka.connect.status.raw`)  
- **Lifetime:** 2 days

LLD macros:
- `{#CONNECTOR}`
- `{#CONNECTOR_TYPE}`
- `{#CONNECTOR_WORKER}`

Created items per connector:
- **Connector state (text):** `kafka.connect.connector.state["{#CONNECTOR}"]`
- **Connector worker (text):** `kafka.connect.connector.worker["{#CONNECTOR}"]`
- **Connector state code (numeric):** `kafka.connect.connector.state.code["{#CONNECTOR}"]`  
  Uses value map **Connector State** (see below).

## 2) Task Discovery
- **Discovery name:** Kafka Connect: Task discovery  
- **Key:** `kafka.connect.task.discovery`  
- **Type:** Dependent (master: `kafka.connect.status.raw`)  
- **Lifetime:** 2 days

LLD macros:
- `{#CONNECTOR}`
- `{#CONNECTOR_TYPE}`
- `{#TASK_ID}`
- `{#TASK_WORKER}`

Created items per task:
- **Task state (text):** `kafka.connect.task.state["{#CONNECTOR}","{#TASK_ID}"]`
- **Task worker (text):** `kafka.connect.task.worker["{#CONNECTOR}","{#TASK_ID}"]`
- **Task state code (numeric):** `kafka.connect.task.state.code["{#CONNECTOR}","{#TASK_ID}"]`  
  The numeric mapping is derived from task state strings.

---

## State Mapping

The template standardizes states to numeric values:

| Code | State |
|---:|---|
| 0 | FAILED |
| 1 | RUNNING |
| 2 | PAUSED |
| 3 | UNASSIGNED |
| 4 | UNKNOWN |
| 5 | OTHER |

Value map included:
- **Connector State** (applied to connector “state code” item)

> Task “state code” uses the same mapping logic but is not value-mapped by default. You may optionally apply the same value map to task state codes after import.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- Kafka Connect REST API reachable from Zabbix (TCP 8083 by default)
- API endpoints available:
  - `GET /connectors`
  - `GET /connectors/<name>/status`
- Network access: Zabbix → Kafka Connect (HTTP/HTTPS)

> Authentication is not configured in this template (no headers). If your Connect endpoint is protected (basic auth, mTLS, reverse proxy), you must adapt the script accordingly.

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Debezium Connector States by HTTP.yaml`

### 2) Create/Update a Host
Create a host representing your Kafka Connect cluster endpoint and link the template:
- **Debezium Connector States by HTTP**

### 3) Configure the Required Macro
Set the base URL at host level:

| Macro | Example | Description |
|------|---------|-------------|
| `{$KAFKA.CONNECT.URL}` | `http://172.17.17.41:8083` | Kafka Connect base URL (no trailing slash required) |

The script normalizes trailing slashes automatically.

---

## Validation & Troubleshooting

### Validate the Kafka Connect API (from Zabbix server/proxy)
~~~bash
curl -sS -m 10 "http://<CONNECT_HOST>:8083/connectors" | head -n 50
curl -sS -m 10 "http://<CONNECT_HOST>:8083/connectors/<CONNECTOR_NAME>/status" | head -n 80
~~~

### If LLD discovers no connectors/tasks
- Confirm `{$KAFKA.CONNECT.URL}` points to the correct Connect instance/cluster.
- Ensure `/connectors` returns a JSON array (e.g., `["c1","c2"]`).
- Ensure `/connectors/<name>/status` returns a JSON object containing:
  - `connector.state`
  - `connector.worker_id`
  - `tasks[]` (task objects with `id`, `state`, `worker_id`)

### If the master item fails (unsupported / error)
- Verify connectivity (routing/firewall/NAT) to the Connect port.
- If Connect is behind a proxy/WAF, confirm it does not block frequent polling.
- If TLS is used, ensure the endpoint is reachable and compatible with your Zabbix environment.

### About partial failures
If a connector status endpoint fails, the script stores the connector state as `UNKNOWN` and captures the error message in the master JSON (`error` field). This helps troubleshooting even if some connectors are temporarily unavailable.

---

## Security Notes

Kafka Connect endpoints often expose operational details. Reduce exposure by applying:
- Source IP allow-lists (only allow Zabbix server/proxy)
- Network segmentation (private network/VPN)
- Firewall policies and rate limiting
- Optional: reverse proxy authentication (basic auth/OIDC) if required by your security posture

If you add authentication, avoid hardcoding secrets in the script; prefer Zabbix macros (and mark secrets as **Secret**).

---

## Recommended Enhancements (Optional)

- Add trigger prototypes, for example:
  - Connector state code = FAILED for N minutes
  - Task state code = FAILED for N minutes
  - Connector state not RUNNING (excludes PAUSED/UNASSIGNED based on policy)
- Add a dependent item to extract the `error` field per connector for faster incident triage.

---

## Contributing

Contributions are welcome, including:
- Authentication support (headers, bearer token, basic auth)
- Trigger prototypes and dashboards
- Improved error extraction and reporting
- Documentation improvements and tested examples

Please open an issue with:
- Zabbix version
- Kafka Connect / Debezium version
- Sanitized `/connectors` and `/status` outputs
- Expected vs. actual behavior (include preprocessing errors if any)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Apache Kafka or Debezium.
