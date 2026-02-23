# StoreOnce Health by HTTP

Zabbix template for monitoring **HPE StoreOnce** appliances via **HTTPS REST API** (XML/JSON), including:

- **Cluster health & status**
- **Capacity metrics** (Local / Cloud / Combined) + deduplication ratio
- **Replication health & status**
- **CPU and Memory utilization** (resourceMonitoring)
- **Hardware monitoring (LLD)**: Drives, Fans, Power Supplies, Temperature sensors

Template name: **StoreOnce Health by HTTP**  
Export format: **Zabbix 7.0 YAML**

---

## Requirements

- Zabbix Server/Proxy **7.0**
- Network connectivity from the Zabbix Server/Proxy to the StoreOnce management interface over HTTPS
- StoreOnce API credentials (Basic Auth)
- (Recommended) A trusted certificate chain on Zabbix Server/Proxy OS if the appliance uses a self-signed certificate

> Tested with StoreOnce Gen3 / 3.18.x firmware (3.x series). If you’re on a different major firmware, endpoints or payload formats may vary.

---

## What this template collects

### Master items

| Name | Key | Type | Notes |
|---|---|---:|---|
| StoreOnce: Cluster (raw) | `storeonce.cluster.raw` | HTTP agent | Reads cluster XML from `/storeonceservices/cluster/` |
| StoreOnce: Server hardware (raw) | `storeonce.server.hardware.raw` | HTTP agent | Reads hardware JSON from `/fusion/chassis/*all*/serverhardware/*all*` |
| StoreOnce CPU Usage raw | `storeonce.cpu.raw` | Script | Queries resourceMonitoring CPU samples (fallbacks: 5sec/min/hour + xml/json) |
| StoreOnce Memory Usage raw | `storeonce.memory.raw` | Script | Queries resourceMonitoring Memory samples (fallbacks: 5sec/min/hour + xml/json) |

### Key dependent metrics (examples)

- Cluster identity: appliance name, network name, serial number, software version, product class
- Health: health level + health text + status
- Replication: replication health level + health text + status
- Capacity (bytes): local/cloud/combined capacity, disk, free, user, and R/W licensed disk capacity
- Efficiency: dedupe ratio, user data stored, size on disk, uptime (seconds)
- Resource monitoring: CPU usage (%), Memory usage (%)
- Hardware overall: HW overall status

### Calculated items

| Name | Key | Formula |
|---|---|---|
| StoreOnce: Local Free % | `storeonce.local.free.in.percent` | `100*(last(//storeonce.local.free)/last(//storeonce.local.capacity))` |
| StoreOnce: Local Used Bytes | `storeonce.local.used.in.bytes` | `last(//storeonce.local.capacity)-last(//storeonce.local.free)` |

### Low-Level Discovery (LLD)

| Discovery | Discovered metrics |
|---|---|
| Drives | Status per drive |
| Fans | Status and speed (%) per fan |
| Power supplies | Status per PSU |
| Temperature sensors | Temperature (°C) per sensor |

---

## Built-in trigger prototypes

The template includes the following LLD trigger prototypes:

- **Drive status has problem** (Severity: **Disaster**) when drive status is not `OK`
- **Fan status has problem** (Severity: **High**) when fan status is not `OK`
- **Powersupply status has problem** (Severity: **High**) when PSU status is not `OK`

> All trigger prototypes are configured for **manual close**.

---

## Installation

1. **Import the template**
   - *Zabbix UI* → **Data collection** → **Templates** → **Import**
   - Import: `StoreOnce Health by HTTP.yaml`

2. **Create/Select the host**
   - Set the host interface / DNS so `{HOST.CONN}` points to the StoreOnce management IP/FQDN.
   - (Recommended) Use the StoreOnce **management** address.

3. **Link the template**
   - Host → **Templates** → Link **StoreOnce Health by HTTP**

4. **Configure macros**
   - Host → **Macros** → Set values listed below

5. **Validate**
   - Host → **Latest data** → ensure raw items return XML/JSON (not HTML)
   - Verify CPU/Memory items return values (may take a couple of collection cycles)

---

## Host macros

### `{$STOREONCE.HOST}`
**Purpose:** StoreOnce appliance management address used for Script-based API calls (CPU/Memory resourceMonitoring).  
**What to enter:** IP address or FQDN reachable from the Zabbix Server/Proxy, e.g. `10.10.101.210` or `storeonce01.company.local`.  
**Best practice:** Use the same address as the host interface `{HOST.CONN}` to keep configuration consistent.

---

### `{$STOREONCE.PORT}`
**Purpose:** HTTPS port for StoreOnce REST API.  
**Typical value:** `443`  
**Change only if:** your environment uses a non-standard port.

---

### `{$STOREONCE.USER}`
**Purpose:** Username used for StoreOnce API authentication (Basic Auth).  
**What to enter:** A dedicated monitoring account with permissions to read cluster status, hardware inventory, and resource monitoring metrics.  
**Recommended:** Use a least-privilege/read-only account where possible.

---

### `{$STOREONCE.PASS}`
**Purpose:** Password for `{$STOREONCE.USER}`.  
**Security:** Store as a **Secret macro** in Zabbix.  
**Operational note:** Update this macro after password rotations.

---

### `{$STOREONCE.NODE}`
**Purpose:** Cluster node index used by `resourceMonitoring` endpoints (CPU/Memory).  
**Default:** `1`  
**Notes:**
- Some StoreOnce Gen3 systems reject node `0` with `Zero is not a valid node number`.
- If CPU/Memory raw returns empty payloads, verify the correct node index and adjust this value.

---

### `{$STOREONCE_CPU_WINDOW_MIN}`
**Purpose:** Rolling time window (minutes) used to query CPU samples from `resourceMonitoring`.  
**Default:** `5`  
**How it works:** The Script item requests data for `now - window` → `now`, then extracts the latest datapoint.  
**Troubleshooting tip:** If the endpoint returns empty results, increase to `15`, `30`, or `60`.

---

## Optional macro (recommended)

### `{$STOREONCE_MEM_WINDOW_MIN}` *(optional)*
**Purpose:** Rolling time window (minutes) used to query Memory samples.  
**Default behavior:** If not defined, the Memory script falls back to `{$STOREONCE_CPU_WINDOW_MIN}`.  
**Why use it:** Allows different collection windows for CPU and Memory.

---

## Troubleshooting

### HTTP 401/403 or HTML response
If a raw item contains `<!DOCTYPE html ...>` or login HTML:
- Verify URL and credentials
- Ensure you are calling the **API endpoint**, not the UI
- Confirm the account has API access

### CPU/Memory returns empty payload
Example: `<cpuStats></cpuStats>` / `<memoryStats></memoryStats>`
- Increase `{$STOREONCE_CPU_WINDOW_MIN}` (or `{$STOREONCE_MEM_WINDOW_MIN}`)
- Verify `{$STOREONCE.NODE}` (node `1` is common for Gen3 3.x)
- Confirm time sync between Zabbix and StoreOnce (NTP recommended)

### SSL certificate errors
If Script items fail with certificate/SSL verification errors:
- Install the StoreOnce CA (or appliance certificate) into the Zabbix Server/Proxy OS trust store
- Restart Zabbix server/proxy services after updating trust, if required by your OS

---

## Suggested additional triggers (optional)

- **StoreOnce API Data Missing for 30 Minutes**  
  `nodata(//storeonce.cluster.raw,30m)=1` *(or any core metric item such as `storeonce.local.capacity`)*

- **Local free space low**  
  `last(//storeonce.local.capacity)>0 and 100*last(//storeonce.local.free)/last(//storeonce.local.capacity)<10`

- **High CPU / Memory utilization**  
  `avg(//cpu.usage,10m)>85`  
  `avg(//memory.usage,10m)>90`

- **Temperature threshold breaches** (if you add thresholds as additional items)

---

## Contributing

Issues and pull requests are welcome:
- Endpoint/payload differences across models/firmware
- Additional metrics (network interfaces, replication throughput, servicesets, etc.)
- More trigger prototypes (temperature, HW overall status, replication)

---
