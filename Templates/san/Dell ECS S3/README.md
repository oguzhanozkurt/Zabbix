# Dell ECS S3 Namespace and Bucket Monitoring by HTTP API (Zabbix 7.0)

This repository provides a Zabbix template to monitor **Dell ECS S3** usage metrics (Namespaces & Buckets) using the **ECS Management REST API**.

It collects billing/metering data via the ECS API, performs **Low-Level Discovery (LLD)** for namespaces and buckets, and creates per-namespace / per-bucket items as dependent items for efficient data collection.

## Features

### Namespace monitoring (LLD)
Discovered per namespace:
- Total object count
- Total size (bytes)
- (Optional) MPU size (bytes)

### Bucket monitoring (LLD)
Discovered per bucket:
- Total object count
- Total size (bytes)
- MPU size (bytes)
- MPU parts
- Sample time / Up-to-date till

### Efficient design
- Uses **one master item** to fetch data (bulk JSON).
- All per-namespace and per-bucket metrics are **dependent items**, reducing API calls.

## Requirements

- Zabbix **7.0** (tested with 7.0.x)
- Network access from Zabbix Server/Proxy to ECS Management endpoint (default: `https://<ecs>:4443`)
- ECS user with permissions to access billing endpoints:
  - `SYSTEM_ADMIN` / `SYSTEM_MONITOR` / `NAMESPACE_ADMIN` (depending on your ECS security model)

## ECS API endpoints used

Authentication flow:
- `GET /login` (Basic Auth) → reads `X-SDS-AUTH-TOKEN` response header
- `GET /logout`

Billing / metering:
- `GET /object/billing/namespace/{namespace}/info?sizeunit=GB&include_bucket_detail=true`
  - Pagination handled via `marker` / `next_marker` when present

> Endpoint paths may vary slightly between ECS versions. If your ECS returns a different billing path, adjust the master script URL accordingly.

## Installation

1. Import the template into Zabbix:
   - **Configuration → Templates → Import**
2. Link the template to a host representing your ECS system.

## Configuration (Macros)

Set the following user macros on the host (or template):

| Macro | Description | Example |
|------|-------------|---------|
| `{$ECS.HOST}` | ECS management IP/FQDN | `10.10.10.10` |
| `{$ECS.PORT}` | ECS management port | `4443` |
| `{$ECS.USER}` | ECS username | `monitor_user` |
| `{$ECS.PASS}` | ECS password | `********` |
| `{$ECS.SIZEUNIT}` | Billing unit requested from API (KB/MB/GB) | `GB` |
| `{$ECS.NAMESPACES}` | Comma-separated namespace list | `ns1,ns2,ns3` |

### Important: macro syntax
Zabbix macros must include `$`, for example:
- ✅ `{$ECS.HOST}`
- ❌ `{ECS.HOST}`

## How it works

### Master item (bulk collector)
The template uses a **Script** type item (JavaScript + `HttpRequest`) to:
1. Login via Basic Auth
2. Fetch billing usage for each namespace in `{$ECS.NAMESPACES}`
3. (Optional) Fetch bucket details when enabled
4. Logout
5. Return a single JSON payload

### LLD discovery rules
- **Namespaces discovery** reads `$.namespaces_lld`
- **Buckets discovery** reads `$.buckets_lld`

## Items and preprocessing

### Namespace item prototypes
- `ecs.namespace.objects[{#NAMESPACE}]`
  - JSONPath: `$.namespaces_lld.data[?(@.namespace=="{#NAMESPACE}")].namespace_total_objects.first()`
- `ecs.namespace.size.bytes[{#NAMESPACE}]`
  - JSONPath: `$.namespaces_lld.data[?(@.namespace=="{#NAMESPACE}")].namespace_total_size_bytes.first()`

### Bucket item prototypes
All bucket items filter by namespace + bucket:
- Objects:
  - `ecs.bucket.objects[{#NAMESPACE},{#BUCKET}]`
  - JSONPath: `$.buckets_lld.data[?(@.namespace=="{#NAMESPACE}" && @.bucket=="{#BUCKET}")].total_objects.first()`
- Size (bytes):
  - `ecs.bucket.size.bytes[{#NAMESPACE},{#BUCKET}]`
  - JSONPath: `$.buckets_lld.data[?(@.namespace=="{#NAMESPACE}" && @.bucket=="{#BUCKET}")].total_size_bytes.first()`
- MPU size (bytes):
  - `ecs.bucket.mpu.size.bytes[{#NAMESPACE},{#BUCKET}]`
  - JSONPath: `$.buckets_lld.data[?(@.namespace=="{#NAMESPACE}" && @.bucket=="{#BUCKET}")].total_mpu_size_bytes.first()`
- MPU parts:
  - `ecs.bucket.mpu.parts[{#NAMESPACE},{#BUCKET}]`
  - JSONPath: `$.buckets_lld.data[?(@.namespace=="{#NAMESPACE}" && @.bucket=="{#BUCKET}")].total_mpu_parts.first()`
- Sample time:
  - `ecs.bucket.sample_time[{#NAMESPACE},{#BUCKET}]`
  - JSONPath: `$.buckets_lld.data[?(@.namespace=="{#NAMESPACE}" && @.bucket=="{#BUCKET}")].sample_time.first()`
- Up-to-date till:
  - `ecs.bucket.uptodate_till[{#NAMESPACE},{#BUCKET}]`
  - JSONPath: `$.buckets_lld.data[?(@.namespace=="{#NAMESPACE}" && @.bucket=="{#BUCKET}")].uptodate_till.first()`

## Troubleshooting

### “Cannot find the data array …”
- Ensure the discovery rule preprocessing points to:
  - `$.namespaces_lld` (not `$.namespaces_lld.data`)
  - `$.buckets_lld` (not `$.buckets_lld.data`)
- Verify the master item returns JSON including:
  - `"namespaces_lld":{"data":[...]}`
  - `"buckets_lld":{"data":[...]}`

### Buckets not discovered
- Enable bucket details in the master item:
  - Parameter `include_bucket_detail = true`
- Verify the ECS user has sufficient privileges for bucket-level billing details.

### HTTP 401 / 403 / 500
- 401: invalid credentials / TLS issues
- 403: insufficient ECS permissions
- 500 with `code:7000`: ECS internal error or invalid namespace input (ensure namespaces are passed individually; template splits comma-separated list)

## Security Notes

- Use a dedicated ECS monitoring user with least privileges.
- Prefer storing passwords in host macros (masked) and limit read access to Zabbix configuration.

## License

Specify your preferred license (MIT/Apache-2.0/GPLv3 etc.)

## Contributing

Issues and pull requests are welcome:
- ECS version compatibility notes
- Additional metrics/triggers/dashboards
- Bug fixes and improvements
