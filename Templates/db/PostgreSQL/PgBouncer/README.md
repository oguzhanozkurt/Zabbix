# PgBouncer Template by HTTP (Zabbix)

This repository provides a Zabbix template to monitor **PgBouncer** using a **Prometheus-compatible `/metrics` endpoint** via **HTTP**.

- Template name: **PgBouncer Template by HTTP**
- Zabbix export: **7.0**
- File: **PGbouncer Template by HTTP.yaml**

The template retrieves the raw Prometheus text once (master item) and extracts individual metrics using dependent items and LLD.

---

## Key Capabilities

### HTTP Metrics Collection (Prometheus format)
- Single master HTTP item pulls the full Prometheus exposition text from the metrics endpoint
- Dependent items parse and store individual values (efficient and scalable)

### Core PgBouncer Metrics
- PgBouncer availability (`pgbouncer_up`)
- PgBouncer version info (`pgbouncer_version_info`)
- Used clients / used servers
- Max client connections (config)
- Process health metrics (open/max file descriptors, resident memory)

### Database-Level Monitoring (LLD)
Automatically discovers databases based on Prometheus labels and creates per-database items for:
- Client waiting time (seconds total)
- Database disabled / paused state
- Database pool size
- Client waiting connections
- Server used connections
- Query duration (seconds total)
- Server in transaction (seconds total)
- Received / sent bytes totals

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- PgBouncer metrics endpoint reachable from Zabbix via HTTP/HTTPS
  - Typically provided by a PgBouncer Prometheus exporter or a metrics endpoint exposing the metrics used by this template
- Network access: Zabbix → metrics endpoint (TCP 80/443 or custom port)

> The template expects the Prometheus text format and specific metric names (see “Monitored Metrics”).

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `PGbouncer Template by HTTP.yaml`

### 2) Create/Update a Host
Zabbix UI → **Data collection → Hosts → Create host**
- Add a host interface if you use one (optional for HTTP agent)
- Link the template: **PgBouncer Template by HTTP**

### 3) Configure the Metrics URL Macro
Set the macro at **host level** (recommended):

| Macro | Example | Description |
|------|---------|-------------|
| `{$PGBOUNCER.METRICS.URL}` | `http://pgbouncer-metrics.local/metrics` | Full URL to the Prometheus metrics endpoint |

---

## How It Works (Design)

### Master Item (HTTP Agent)
- **Prometheus Bulk Item**
  - Key: `pgbouncer.prometheus.bulk`
  - Type: HTTP agent
  - URL: `{$PGBOUNCER.METRICS.URL}`
  - Value type: **Text**

### Dependent Items
All core metrics are parsed from the master item using preprocessing (REGEX / JavaScript where needed).  
This approach minimizes HTTP calls while keeping data granularity.

---

## Monitored Metrics (Summary)

### Core PgBouncer / Process Metrics
- **PgBouncer state (Up/Down)**  
  Item key: `pgbouncer.state`  
  Source metric: `pgbouncer_up`  
  Value map: **PgBouncer State** (0=Down, 1=Up)

- **PgBouncer version**  
  Item key: `pgbouncer.version`  
  Source metric: `pgbouncer_version_info{version="x.y.z"} ...`

- **Used clients**  
  Item key: `pgbouncer.used.clients`  
  Source metric: `pgbouncer_used_clients`

- **Used servers**  
  Item key: `pgbouncer.used.servers`  
  Source metric: `pgbouncer_used_servers`

- **Max client connections (config)**  
  Item key: `pgbouncer.max.client.connections`  
  Source metric: `pgbouncer_config_max_client_connections`

- **Process open file descriptors**  
  Item key: `pgbouncer.process.open.fds`  
  Source metric: `process_open_fds`

- **Process max file descriptors**  
  Item key: `pgbouncer.process.max.fds`  
  Source metric: `process_max_fds`

- **Process resident memory (bytes)**  
  Item key: `pgbouncer.process.resident.memory.bytes`  
  Source metric: `process_resident_memory_bytes`

---

## Low-Level Discovery (LLD)

The template includes database discovery based on the `database="..."` label found in relevant metrics.  
Each discovery rule uses JavaScript preprocessing to generate LLD JSON and then creates per-database item prototypes.

### Discovery Macro
- `{#DATABASE}`

### Discovery Rules and Item Prototypes
- **Client Waiting Seconds Total**  
  Rule key: `pgbouncer.client.waiting.seconds.total`  
  Prototype key: `client.wait.seconds.total.[{#DATABASE}]`  
  Source metric: `pgbouncer_stats_client_wait_seconds_total{database="..."} ...`

- **Database Disabled State**  
  Rule key: `pgbouncer.database.disabled.state`  
  Prototype key: `database.disabled.state.[{#DATABASE}]`  
  Value map: **Database State** (0=Up, 1=Down)  
  Source metric: `pgbouncer_databases_disabled{database="..."} ...`

- **Database Paused State**  
  Rule key: `pgbouncer.database.paused.state`  
  Prototype key: `database.paused.state.[{#DATABASE}]`  
  Value map: **Database State** (0=Up, 1=Down)  
  Source metric: `pgbouncer_databases_paused{database="..."} ...`

- **Database Pool Size**  
  Rule key: `pgbouncer.database.pool.size`  
  Prototype key: `pool.size.[{#DATABASE}]`  
  Source metric: `pgbouncer_databases_pool_size{database="..."} ...`

- **Database Pools Client Waiting Connections**  
  Rule key: `pgbouncer.database.pools.client.waiting.connections`  
  Prototype key: `client.waiting.connections.[{#DATABASE}]`  
  Source metric: `pgbouncer_pools_client_waiting_connections{database="..."} ...`

- **Pools Server Used Connections**  
  Rule key: `pgbouncer.pools.server.used.connections`  
  Prototype key: `pools.server.used.connections.[{#DATABASE}]`  
  Source metric: `pgbouncer_pools_server_used_connections{database="..."} ...`

- **Query Duration Seconds Total**  
  Rule key: `pgbouncer.query.duration.seconds.total`  
  Prototype key: `queries.duration.seconds.total.[{#DATABASE}]`  
  Source metric: `pgbouncer_stats_queries_duration_seconds_total{database="..."} ...`

- **Server in Transactions Total**  
  Rule key: `pgbouncer.server.in.transactions.total`  
  Prototype key: `server.transaction.seconds.total.[{#DATABASE}]`  
  Source metric: `pgbouncer_stats_server_in_transaction_seconds_total{database="..."} ...`

- **Stats Received Bytes Total**  
  Rule key: `pgbouncer.stats.received.bytes.total`  
  Prototype key: `stats.received.bytes.total.[{#DATABASE}]`  
  Source metric: `pgbouncer_stats_received_bytes_total{database="..."} ...`

- **Stats Sent Bytes Total**  
  Rule key: `pgbouncer.stats.sent.bytes.total`  
  Prototype key: `stats.sent.bytes.total.[{#DATABASE}]`  
  Source metric: `pgbouncer_stats_sent_bytes_total{database="..."} ...`

---

## Validation & Troubleshooting

From your Zabbix server/proxy, validate endpoint reachability and content:

~~~bash
curl -sS -m 10 "<METRICS_URL>" | head -n 50
~~~

Example checks:
- Ensure the endpoint returns **HTTP 200**.
- Confirm that the response contains expected metric names such as:
  - `pgbouncer_up`
  - `pgbouncer_used_clients`
  - `pgbouncer_used_servers`

### If items show as unsupported or return no data
- Verify the macro `{$PGBOUNCER.METRICS.URL}` points to the correct endpoint (including the `/metrics` path).
- Confirm connectivity from the Zabbix server/proxy to the endpoint (routing/firewall/NAT).
- Validate that the exporter exposes the metric names required by this template.
- If HTTPS is used, ensure the TLS setup is compatible (cert chain, SNI, etc.).

---

## Security Notes

Prometheus metrics endpoints are often **unauthenticated by default**. Reduce exposure by applying:
- Source IP allow-lists (only allow Zabbix server/proxy)
- Network segmentation (private network/VPN)
- Firewall policies and rate limiting
- Optional: place the endpoint behind a reverse proxy with authentication (if required by your security posture)

If you require HTTPS or authentication, adjust the endpoint accordingly and configure the Zabbix HTTP agent settings to match.

---

## Recommended Enhancements (Optional)

This template focuses on data collection. You may want to add triggers such as:
- PgBouncer down for 5 minutes (`pgbouncer.state`)
- Used clients approaching max connections
- Client waiting connections exceeding a threshold per database
- Database paused/disabled state changes

---

## Contributing

Contributions are welcome, including:
- Additional PgBouncer metrics coverage
- Improved discovery logic (labels, edge cases)
- Trigger recommendations and thresholds
- Documentation improvements and examples

Please open an issue with:
- PgBouncer and exporter versions
- Zabbix version
- Sanitized sample output from the `/metrics` endpoint
- Expected vs. actual behavior
