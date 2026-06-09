# Kafka Debezium Monitoring by HTTP (Zabbix Template)

This repository provides a Zabbix template to monitor **Kafka consumer group lag** (commonly used for **Debezium / Kafka Connect CDC** pipelines) via an **HTTP metrics endpoint** that exposes **Prometheus text format**.

- Template name: **Kafka Debezium Monitoring by HTTP**
- Zabbix export: **7.0**
- File: `Kafka Debezium Monitoring by HTTP.yaml`
- Data source: **HTTP Agent (master raw)** → **Dependent LLD** → **Dependent items** + **Calculated item** + **Trigger prototypes**

> Note: This is a community template and is not an official Apache Kafka / Debezium release.

---

## What’s Included

### Raw Metrics Collection (HTTP Agent)
A single master item fetches the full Prometheus exposition text:
- **Item name:** `ConsumerGroup raw`
- **Key:** `consumergroup.raw`
- **Type:** HTTP agent
- **Value type:** Text
- **History:** 1 day

### Automated Discovery (LLD)
The template automatically discovers **consumer group + topic** pairs and creates per-pair items.

- **Discovery name:** `Kafka consumer group metrics discovery`
- **Key:** `kafka.consumergroup.metrics.discovery`
- **Type:** Dependent (master: `consumergroup.raw`)
- **LLD lifetime:** 2 days
- **Disable after:** 1 hour (if no longer discovered)

Discovery output macros:
- `{#CONSUMERGROUP}`
- `{#TOPIC}`

**Important:** The discovery logic includes only pairs where **both** metrics exist:
- `kafka_consumergroup_lag_sum`
- `kafka_consumergroup_current_offset_sum`

This prevents partial/invalid entities.

### Per-Entity Items
For each `{#CONSUMERGROUP} / {#TOPIC}` pair, the template creates:

1) **Consumer group lag (sum)**
- Type: Dependent
- Key: `kafka.consumergroup.lag.sum["{#CONSUMERGROUP}","{#TOPIC}"]`
- Extracted from: `kafka_consumergroup_lag_sum{consumergroup="...",topic="..."} <value>`
- History: 7 days

2) **Current offset (sum)**
- Type: Dependent
- Key: `kafka.consumergroup.current_offset_sum["{#CONSUMERGROUP}","{#TOPIC}"]`
- Extracted from: `kafka_consumergroup_current_offset_sum{consumergroup="...",topic="..."} <value>`
- History: 7 days

3) **Lag / offset ratio**
- Type: Calculated
- Key: `kafka.consumergroup.lag.offset.ratio["{#CONSUMERGROUP}","{#TOPIC}"]`
- History: 7 days
- Formula:
  - `last(lag.sum) / (last(current_offset_sum) + 0.001)`

> The ratio item is used as a “delay/health proxy” in triggers. If you prefer a different model (e.g., lag-only thresholds), you can adjust triggers accordingly.

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- A reachable HTTP/HTTPS endpoint that returns **Prometheus text format**
- The endpoint must expose at least these metrics:
  - `kafka_consumergroup_lag_sum{consumergroup="...",topic="..."} <number>`
  - `kafka_consumergroup_current_offset_sum{consumergroup="...",topic="..."} <number>`
- Network access: Zabbix → endpoint (TCP 80/443 or custom port)

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `Kafka Debezium Monitoring by HTTP.yaml`

### 2) Create/Update a Host
Create a host representing your Kafka monitoring endpoint, then link the template:
- Template: **Kafka Debezium Monitoring by HTTP**

### 3) Configure the Endpoint Macro (Required)
Set at host level:

| Macro | Example | Description |
|------|---------|-------------|
| `{$KAFKA.ENDPOINT.URL}` | `http://kafka-exporter.company.local/metrics` | Full URL to the Prometheus metrics endpoint |

---

## Triggers (Included)

### Master Item Data Availability
- **No data ConsumerGroup for 30 minutes** (HIGH)
  - Expression: `nodata(consumergroup.raw, 30m)=1`
  - Manual close: enabled

### Per ConsumerGroup/Topic Trigger Prototypes
These triggers are generated per `{#CONSUMERGROUP}/{#TOPIC}`:

1) **Ratio delay is higher than 1h** (DISASTER)
- Problem (example logic):
  - `min(ratio, 5m) > 3600` AND `min(lag_sum, 5m) > 100`
- Recovery:
  - `max(ratio, 5m) < 1800`
- Description note in template:
  - “1-hour delay…”

2) **Ratio is higher than for 10 minutes** (HIGH)
- Problem:
  - `min(ratio, 5m) > 600` AND `min(lag_sum, 5m) > 100`
- Recovery:
  - `max(ratio, 5m) < 300`
- Description note in template:
  - “Delay 10 minutes…”

> Tip: Thresholds are hardcoded in trigger expressions. If you need different thresholds per topic/group, consider cloning triggers and using macros.

---

## Validation & Troubleshooting

### Validate the Metrics Endpoint
From your Zabbix server/proxy:

~~~bash
curl -sS -m 10 "<KAFKA_METRICS_URL>" | head -n 80
~~~

You should see lines similar to:
- `kafka_consumergroup_lag_sum{consumergroup="...",topic="..."} 123`
- `kafka_consumergroup_current_offset_sum{consumergroup="...",topic="..."} 456`

### If LLD discovers no entities
- Confirm the endpoint returns **Prometheus text** (not JSON).
- Confirm both required metrics exist and include these labels:
  - `consumergroup="..."`
  - `topic="..."`
- The discovery intentionally keeps only pairs where **both metrics exist**.

### If dependent items show “unsupported” / “metric not found”
- Check whether label values include escaped quotes or backslashes; the preprocessing accounts for escaped values, but verify the output format is standard Prometheus exposition.
- Verify that `{#CONSUMERGROUP}` and `{#TOPIC}` exactly match the label values in the metrics output.

### If you want to exclude anonymous consumer groups
The discovery preprocessing includes an optional filter (commented out) for `anonymous.*` consumer groups.  
You can enable this by editing the discovery preprocessing JavaScript in Zabbix and uncommenting the block.

---

## Security Notes

Prometheus metrics endpoints are often **unauthenticated** by default. Reduce exposure by applying:
- Source IP allow-lists (only allow Zabbix server/proxy)
- Network segmentation (private network/VPN)
- Firewall policies and rate limiting
- Optional: place the endpoint behind a reverse proxy with authentication (if required)

---

## Contributing

Contributions are welcome, including:
- Additional metrics (connector/task state, throughput, error counters)
- Alternative “delay” models (lag-only, lag delta, rate-based delay estimation)
- More flexible trigger thresholds (macro-based)
- Documentation improvements and examples

Please open an issue with:
- Zabbix version
- Sample sanitized metrics output (a few lines)
- Expected vs. actual behavior (include preprocessing errors if any)

---

## License

Licensed under the MIT License. See the LICENSE file for details.

## Trademarks

All product names and trademarks are property of their respective owners.
This project is not affiliated with, endorsed by, or sponsored by Apache Kafka or Debezium.
