# HPE StoreOnce by iLO and API (Zabbix Template)

This repository provides a Zabbix template to monitor **HPE StoreOnce** using **two data sources**:
- **HPE iLO via SNMP** (hardware sensors / server health)
- **StoreOnce Management API** (capacity, storage health, services, alerts)

- Template name: **HPE StoreOnce by ILO and API**
- Zabbix export: **7.0**
- File: **HPE StoreOnce by ILO and API.yaml**

> Note: This is a community template and is not an official HPE release.

---

## What’s Included

### Availability & Connectivity
- ICMP ping, packet loss, and response time
- SNMP agent availability (Zabbix internal check)

### iLO Hardware Health (SNMP)
Monitors HPE server health via standard HPE/Compaq MIBs (e.g., `CPQHLTH-MIB`, `CPQSINFO-MIB`, `CPQIDA-MIB`):
- Overall system health status
- System temperature condition and temperature sensors
- Fans condition
- Power supplies condition
- Disk array controllers and cache/battery status
- Physical disks (status + S.M.A.R.T.)
- Virtual disks (status)

### StoreOnce Management API (Script + Dependent items/LLD)
Uses StoreOnce API to collect:
- Storage overview and capacity (TiB)
- Storage health (numeric + string)
- Used space percentage
- Latest alert message and alert UUID (detects new alerts)
- LLD for:
  - Catalyst stores
  - Services (cat/nas/replication/vtl)
  - Storage volumes
  - Monitored servers (hardware monitor)

---

## Requirements

- Zabbix Server/Proxy: **7.0** (or compatible newer versions)
- StoreOnce management access (HTTPS)
- iLO SNMP enabled and reachable from Zabbix (UDP/161)
- Network access:
  - Zabbix → StoreOnce Management (TCP/443)
  - Zabbix → iLO (UDP/161)
  - Optional: ICMP allowed from Zabbix → StoreOnce/iLO

---

## Quick Start

### 1) Import the Template
Zabbix UI → **Data collection → Templates → Import**  
Import: `HPE StoreOnce by ILO and API.yaml`

### 2) Create/Update the Host (Two Interfaces Required)
During host creation, add **two interfaces**:

1. **Agent interface** (used for StoreOnce API calls)  
   - Enter **only the StoreOnce management IP/FQDN**
2. **SNMP interface** (used for iLO SNMP polling)  
   - Enter the **iLO IP/FQDN**
   - Set SNMP community/v3 accordingly

> Practical recommendation: Keep the **Agent interface as the default** interface so `{HOST.CONN}` resolves to the StoreOnce management address for API scripts.

### 3) Configure Required Macros
Set macros at **host level** (recommended), see the next section.

---

## Macros

### Required (Must be set)
| Macro | Example | Description |
|------|---------|-------------|
| `{$STOREONCE.USER}` | `observer_user` | StoreOnce UI user with **Observer** role |
| `{$STOREONCE.PASSWORD}` | *(secret)* | Password for the Observer user (store as **Secret macro**) |
| `{$SNMP_COMMUNITY}` | `public` | iLO SNMP community (if using SNMPv2c) |

### Recommended / Thresholds (Defaults included in template)
| Macro | Default | Description |
|------|---------|-------------|
| `{$ICMP_LOSS_WARN}` | `20` | ICMP loss warning threshold (%) |
| `{$ICMP_RESPONSE_TIME_WARN}` | `0.15` | ICMP RTT warning threshold (seconds) |
| `{$SNMP.TIMEOUT}` | `5m` | Window used to detect missing SNMP polling |
| `{$HEALTH_WARN_STATUS}` | `3` | iLO overall health “warning” state (cpqHeMibCondition) |
| `{$HEALTH_CRIT_STATUS}` | `4` | iLO overall health “critical” state (cpqHeMibCondition) |
| `{$FAN_WARN_STATUS}` | `3` | Fan warning state |
| `{$FAN_CRIT_STATUS}` | `4` | Fan critical state |
| `{$PSU_WARN_STATUS}` | `3` | PSU warning state |
| `{$PSU_CRIT_STATUS}` | `4` | PSU critical state |
| `{$DISK_WARN_STATUS}` | `4` | Physical disk warning state |
| `{$DISK_FAIL_STATUS}` | `3` | Physical disk failed state |
| `{$DISK_SMART_FAIL_STATUS:"replaceDrive"}` | `3` | S.M.A.R.T. failure (replace drive) |
| `{$DISK_SMART_FAIL_STATUS:"replaceDriveSSDWearOut"}` | `4` | S.M.A.R.T. failure (SSD wear out) |
| `{$DISK_ARRAY_CACHE_OK_STATUS:"enabled"}` | `3` | Cache OK state |
| `{$DISK_ARRAY_CACHE_WARN_STATUS:"invalid"}` | `2` | Cache warning state |
| `{$DISK_ARRAY_CACHE_WARN_STATUS:"cacheModFlashMemNotAttached"}` | `6` | Cache warning state |
| `{$DISK_ARRAY_CACHE_WARN_STATUS:"cacheModDegradedFailsafeSpeed"}` | `7` | Cache warning state |
| `{$DISK_ARRAY_CACHE_WARN_STATUS:"cacheReadCacheNotMapped"}` | `9` | Cache warning state |
| `{$DISK_ARRAY_CACHE_CRIT_STATUS:"cacheModCriticalFailure"}` | `8` | Cache critical state |
| `{$DISK_ARRAY_CACHE_BATTERY_WARN_STATUS:"degraded"}` | `5` | Cache battery warning state |
| `{$DISK_ARRAY_CACHE_BATTERY_WARN_STATUS:"notPresent"}` | `6` | Cache battery warning state |
| `{$DISK_ARRAY_CACHE_BATTERY_CRIT_STATUS:"failed"}` | `4` | Cache battery critical state |
| `{$DISK_ARRAY_CACHE_BATTERY_CRIT_STATUS:"capacitorFailed"}` | `7` | Cache battery critical state |

---

## Monitored Items (Highlights)

### StoreOnce API (Scripts + Dependent)
**Authentication:** Token is obtained via:  
`POST /pml/login/authenticatewithobject` → `access_token` (Bearer)

Key API master items (Script):
- `storeonce.get.storage` – Storage overview (`api/v1/management-services/local-storage/overview`)
- `storeonce.get.volume` – Volumes (`api/v1/management-services/local-storage/volumes`)
- `storeonce.get.services` – Services (cat/nas/rep/vtl)
- `storeonce.get.catalyst.store` – Catalyst stores
- `storeonce.get.alert` – Latest alert (`rest/alerts?...count=1`)
- `storeonce.get.hardware_monitor*` – Hardware monitor endpoints (`hwmonitor/*`)

Core dependent/calculated items:
- Free space (TiB), used space (TiB)
- Total space (TiB) *(calculated)*
- Used space percentage *(calculated)*
- Storage health (numeric + string)
- Latest alert UUID + message
- “Storage Health Status percent” extracted from health string

### iLO SNMP (System & Hardware)
- Overall system health
- Temperature status and detailed temperature sensors
- Fans, PSU status
- Array controllers, cache, cache battery
- Physical disks and S.M.A.R.T.
- Virtual disks

---

## Low-Level Discovery (LLD)

### StoreOnce API LLD (Dependent)
- **Catalyst Stores** (`storeonce.catalyst.storage.discovery`)
  - Dedupe ratio, health, store size on disk, user data stored, etc.
- **Services** (`storeonce.discovery.services`)
  - Health + health string per service: `catalyst`, `nas`, `replication`, `vtl`
- **Storage Volumes** (`storeonce.discovery.volumes`)
  - Volume UUID, pool, status, serial number, etc.
- **Monitored Servers** (`storeonce.discovery.monitored.servers`)
  - Per-server status payload (as calculated items)

### iLO SNMP LLD
- Array controllers and cache (including cache battery)
- Physical disks (including S.M.A.R.T.)
- Virtual disks
- Fans
- Power supplies
- Temperature sensors (general + categorized discovery rules: ambient/cpu/io/memory/psu/system)

---

## Triggers (Included)

### Availability / Connectivity
- Unavailable by ICMP ping (DISASTER)
- High ICMP ping loss (WARNING)
- High ICMP ping response time (WARNING)
- No SNMP data collection (DISASTER)
- Host restarted (uptime < 10m) (DISASTER)

### StoreOnce API
- Storage disk usage is higher than 80% (DISASTER)
- Storage used space percentage > 90% (DISASTER)
- Storage used space percentage > 95% (DISASTER)
- Storage is not healthy (HIGH)
- New alert detected (UUID changed) (HIGH, manual close)

### iLO Hardware (LLD Trigger Prototypes)
- PSU critical/warning
- Fan critical/warning
- Temperature outside normal range / failed
- Physical disk failed / warning
- Physical disk S.M.A.R.T. failed
- Virtual disk failed / not OK
- Disk array cache/battery critical/warning

---

## Validation & Troubleshooting

### SNMP (iLO)
From your Zabbix server/proxy:

~~~bash
# Basic SNMP system info
snmpwalk -v2c -c <COMMUNITY> <ILO_IP> 1.3.6.1.2.1.1

# HPE/Compaq health subtree examples
snmpwalk -v2c -c <COMMUNITY> <ILO_IP> 1.3.6.1.4.1.232.6

# Disk array subtree examples
snmpwalk -v2c -c <COMMUNITY> <ILO_IP> 1.3.6.1.4.1.232.3.2
~~~

### StoreOnce API (basic manual test)
1) Authenticate and get a token:

~~~bash
curl -sS -X POST "https://<STOREONCE_MGMT>/pml/login/authenticatewithobject" \
  -H "Content-Type: application/json" \
  -H "Accept: application/json" \
  -d '{"username":"<USER>","password":"<PASS>","grant_type":"password"}'
~~~

2) Query storage overview with the Bearer token:

~~~bash
curl -sS "https://<STOREONCE_MGMT>/api/v1/management-services/local-storage/overview" \
  -H "Authorization: Bearer <ACCESS_TOKEN>" \
  -H "Accept: application/json"
~~~

> If HTTPS requests fail due to certificate validation, ensure the StoreOnce certificate chain is trusted by the Zabbix server/proxy OS trust store.

### If you see “No SNMP data collection”
- Confirm UDP/161 reachability (firewall/ACL).
- Verify SNMP community/v3 credentials.
- Ensure the host has an SNMP interface configured in Zabbix.
- Check whether iLO restricts SNMP by source IP.

### If StoreOnce API items fail
- Confirm `{$STOREONCE.USER}` / `{$STOREONCE.PASSWORD}` are correct and the user has **Observer** role.
- Verify the host’s default interface (`{HOST.CONN}`) resolves to the StoreOnce management address.
- Review item latest data for script error messages (HTTP status, parsing errors).

---

## Security Notes

- StoreOnce credentials are sensitive:
  - Store `{$STOREONCE.PASSWORD}` as a **Secret macro**
  - Restrict access to host/template macros to authorized administrators
- Limit API and SNMP access with:
  - Source IP allow-lists (only Zabbix server/proxy)
  - Network segmentation
  - Firewall policies and logging
- Use HTTPS and maintain proper certificate management.

---

## Contributing

Contributions are welcome, including:
- Additional StoreOnce endpoints and metrics
- Improved parsing / preprocessing
- Additional triggers and thresholds based on operational best practices
- Documentation improvements and tested examples

Please open an issue with:
- StoreOnce model and software version
- iLO model/firmware version
- Zabbix version
- Sanitized sample API response or `snmpwalk` output
- Expected vs. actual behavior (including any preprocessing errors)
