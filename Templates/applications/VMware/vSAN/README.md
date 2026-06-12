# VMware vSAN by API (Zabbix 7.0 Template)

This repository provides a Zabbix 7.0 template to monitor **VMware vSAN** environments through the **vCenter / vSAN API** using an external Python collector.

- Template name: **Template VMware vSAN by API**
- Zabbix export: **7.0**
- File: `template_vmware_vsan_by_api_zabbix_7_0.yaml`
- Collector script: `zbx_vsan_api.py`
- Collection method: **External check** → **JSON payload** → **Dependent items** → **LLD** → **Item/trigger prototypes**

> Note: This is a community template and is not an official VMware/Broadcom or Zabbix release.

---

## What’s Included

### Collector Health
- Collector status
- Collector message
- Collector duration
- Last successful timestamp
- Total discovered vSAN clusters

### vSAN Cluster Monitoring
- Cluster health
- Capacity total / used / free
- Capacity used percentage
- Deduplication ratio
- Compression ratio
- Resync components
- Resync bytes remaining
- Resync ETA
- Inaccessible objects
- Non-compliant objects
- Reduced availability objects
- Performance service health
- Cluster read/write latency
- Cluster read/write IOPS
- Cluster read/write throughput
- Network errors and drops
- Rebalance status
- Congestion

### vSAN Host Monitoring
- Host health
- Contributing stats
- Maintenance mode
- Disk group count
- Failed/degraded disk count
- Network errors and drops
- Read/write latency
- Read/write IOPS
- Read/write throughput
- Congestion

### Disk Group Monitoring
- Disk group health
- Capacity / used / free
- Used percentage
- Cache disk health
- Capacity disk count
- Failed disk count
- Read/write latency
- Read/write IOPS
- Read/write throughput
- Congestion

### Capacity Disk Monitoring
- Disk health
- Capacity / used / free
- Used percentage
- Read/write latency
- Read/write IOPS
- Read/write throughput

### VM and Virtual Disk Performance
- Per-VM read/write latency
- Per-VM read/write IOPS
- Per-VM read/write throughput
- Per-VM congestion
- Per-vDisk read/write latency
- Per-vDisk read/write IOPS
- Per-vDisk read/write throughput
- Per-vDisk congestion

### vSAN Network Monitoring
- Network health
- RX/TX throughput
- RX/TX packets
- Utilization percentage
- Errors
- Drops

### vSAN Health Check Discovery
- Health check status
- Health check message
- Warning/failed health check triggers

---

## Requirements

- Zabbix Server/Proxy: **7.0**
- Python 3
- Python virtual environment recommended
- Python modules:
  - `pyvmomi`
  - `requests`
- vCenter reachable from the Zabbix Server/Proxy
- A vCenter user with read-only access and visibility to vSAN clusters
- vSAN helper modules available with the collector:
  - `vsanapiutils.py`
  - `vsanmgmtObjects.py`

---

## Repository Files

Recommended repository structure:

~~~text
.
├── template_vmware_vsan_by_api_zabbix_7_0.yaml
├── zbx_vsan_api.py
├── vsanapiutils.py
├── vsanmgmtObjects.py
├── README.md
└── LICENSE
~~~

> The Zabbix template does not embed the collector script.  
> `zbx_vsan_api.py` must be deployed manually to the Zabbix Server/Proxy ExternalScripts directory.

---

## Installation

## 1) Import the Zabbix Template

Zabbix UI:

**Data collection → Templates → Import**

Import:

~~~text
template_vmware_vsan_by_api_zabbix_7_0_fixed_uuidv4.yaml
~~~

After import, the template name should be:

~~~text
Template VMware vSAN by API
~~~

---

## 2) Prepare the Python Virtual Environment

The collector should run with a dedicated Python virtual environment.

Recommended path:

~~~text
/opt/zabbix-vsan-venv
~~~

Create the virtual environment:

~~~bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip

sudo python3 -m venv /opt/zabbix-vsan-venv
sudo /opt/zabbix-vsan-venv/bin/pip install --upgrade pip
sudo /opt/zabbix-vsan-venv/bin/pip install pyvmomi requests
~~~

Why this is needed:

- Keeps Python dependencies isolated from the OS Python.
- Avoids PEP 668 / externally-managed-environment issues on modern Linux distributions.
- Ensures the collector always runs with the expected Python libraries.
- Makes the collector path predictable for the shebang line.

The collector script should start with:

~~~python
#!/opt/zabbix-vsan-venv/bin/python3
~~~

---

## 3) Deploy the Collector Script

Copy these files to the Zabbix ExternalScripts directory:

~~~text
zbx_vsan_api.py
vsanapiutils.py
vsanmgmtObjects.py
~~~

Default path for package-based Zabbix installations:

~~~text
/usr/lib/zabbix/externalscripts
~~~

Example:

~~~bash
sudo install -o zabbix -g zabbix -m 0755 zbx_vsan_api.py /usr/lib/zabbix/externalscripts/zbx_vsan_api.py
sudo install -o zabbix -g zabbix -m 0644 vsanapiutils.py /usr/lib/zabbix/externalscripts/vsanapiutils.py
sudo install -o zabbix -g zabbix -m 0644 vsanmgmtObjects.py /usr/lib/zabbix/externalscripts/vsanmgmtObjects.py
~~~

Validate permissions:

~~~bash
ls -l /usr/lib/zabbix/externalscripts/zbx_vsan_api.py
ls -l /usr/lib/zabbix/externalscripts/vsanapiutils.py
ls -l /usr/lib/zabbix/externalscripts/vsanmgmtObjects.py
~~~

The collector must be executable:

~~~bash
sudo chmod 755 /usr/lib/zabbix/externalscripts/zbx_vsan_api.py
~~~

---

## 4) Docker-Based Zabbix Installation Notes

If Zabbix runs in Docker, the external script is executed **inside the Zabbix Server or Proxy container**.

Important points:

- Do not edit the file inside the container if the ExternalScripts path is mounted as read-only.
- Place/update the script on the **host-side mounted directory**.
- The script path inside the container must match the Zabbix ExternalScripts location.
- The virtual environment path used in the shebang must also be visible inside the container.

Example host-side layout:

~~~text
/opt/zabbix/externalscripts/zbx_vsan_api.py
/opt/zabbix/externalscripts/vsanapiutils.py
/opt/zabbix/externalscripts/vsanmgmtObjects.py
/opt/zabbix-vsan-venv/
~~~

Example Docker Compose volume mapping:

~~~yaml
volumes:
  - /opt/zabbix/externalscripts:/usr/lib/zabbix/externalscripts:ro
  - /opt/zabbix-vsan-venv:/opt/zabbix-vsan-venv:ro
~~~

Example Zabbix Server environment setting:

~~~yaml
environment:
  ZBX_TIMEOUT: 30
~~~

> External checks are limited by the Zabbix Server/Proxy timeout.  
> If the collector takes longer than the configured Zabbix timeout, the item becomes unsupported even if `{$VSAN.API.TIMEOUT}` is higher.

After updating the script on the host, restart the Zabbix Server/Proxy container if needed:

~~~bash
docker compose restart zabbix-server
~~~

or:

~~~bash
docker restart <zabbix_server_container_name>
~~~

---

## 5) Validate the Collector Manually

Run the collector as the `zabbix` user on a package-based installation:

~~~bash
sudo -u zabbix /usr/lib/zabbix/externalscripts/zbx_vsan_api.py \
"https://vcenter.example.local/sdk" \
"zabbix-readonly@vsphere.local" \
"PASSWORD" \
".*" \
"CHANGE_IF_NEEDED" \
"60" | jq '.collector'
~~~

Expected collector output example:

~~~json
{
  "status": 1,
  "message": "OK",
  "duration_sec": 4.21,
  "timestamp": 1760000000,
  "clusters_total": 1
}
~~~

For Docker-based Zabbix, test inside the container:

~~~bash
docker exec -u zabbix -it <zabbix_server_container_name> bash -lc '
/usr/lib/zabbix/externalscripts/zbx_vsan_api.py \
"https://vcenter.example.local/sdk" \
"zabbix-readonly@vsphere.local" \
"PASSWORD" \
".*" \
"CHANGE_IF_NEEDED" \
"60" | head -c 1000
'
~~~

---

## 6) Create or Update the Zabbix Host

Create a host that represents the vCenter/vSAN monitoring scope.

Example host name:

~~~text
VMware vSAN API
~~~

Link the template:

~~~text
Template VMware vSAN by API
~~~

This template uses an **External check**, so an agent interface is not required for the collector itself.  
However, adding a standard host interface is still recommended for inventory consistency.

---

## 7) Configure Required Macros

Set these macros at host level.

| Macro | Example | Description |
|---|---|---|
| `{$VMWARE.URL}` | `https://vcenter.example.local/sdk` | vCenter SDK URL used by the collector. |
| `{$VMWARE.USER}` | `zabbix-readonly@vsphere.local` | vCenter user with read-only vSAN visibility. |
| `{$VMWARE.PASSWORD}` | Secret macro | Password for the vCenter user. |
| `{$VSAN.CLUSTER.MATCHES}` | `.*` | Regex filter for vSAN clusters to include. |
| `{$VSAN.CLUSTER.NOT_MATCHES}` | `CHANGE_IF_NEEDED` | Regex filter for vSAN clusters to exclude. |
| `{$VSAN.UPDATE.INTERVAL}` | `5m` | Master collector interval. |
| `{$VSAN.API.TIMEOUT}` | `60` | Timeout passed to the external collector in seconds. |

Recommended:

- Store `{$VMWARE.PASSWORD}` as a **Secret macro**.
- Use a dedicated vCenter read-only account.
- If you do not need exclusions, you can set `{$VSAN.CLUSTER.NOT_MATCHES}` to `^$`.

---

## 8) Review Threshold Macros

| Macro | Default | Description |
|---|---:|---|
| `{$VSAN.DATA.MAXAGE}` | `15m` | Maximum age without collector timestamp before stale data alarm. |
| `{$VSAN.COLLECTOR.DURATION.MAX}` | `30` | Collector runtime threshold in seconds. |
| `{$VSAN.CAPACITY.HIGH}` | `85` | Cluster capacity used percentage high threshold. |
| `{$VSAN.CAPACITY.DISASTER}` | `90` | Cluster capacity used percentage disaster threshold. |
| `{$VSAN.DISK.USED.WARN}` | `80` | Disk group used percentage warning threshold. |
| `{$VSAN.DISK.USED.HIGH}` | `90` | Disk group used percentage high threshold. |
| `{$VSAN.CAPACITY_DISK.USED.HIGH}` | `90` | Capacity disk used percentage high threshold. |
| `{$VSAN.LATENCY.HIGH}` | `50` | Cluster/disk group/disk latency high threshold in ms. |
| `{$VSAN.LATENCY.DISASTER}` | `100` | Cluster latency disaster threshold in ms. |
| `{$VSAN.VM.LATENCY.HIGH}` | `50` | VM latency threshold in ms. |
| `{$VSAN.VDISK.LATENCY.HIGH}` | `50` | Virtual disk latency threshold in ms. |
| `{$VSAN.RESYNC.MAX.TIME}` | `1h` | Resync duration threshold. |
| `{$VSAN.NET.ERROR.MAX}` | `0` | Network errors/drops threshold. |
| `{$VSAN.NET.UTIL.WARN}` | `80` | Network utilization warning threshold. |
| `{$VSAN.CONGESTION.HIGH}` | `30` | vSAN congestion percentage threshold. |

---

## How It Works

The template has one master external item:

~~~text
vSAN: API raw data
~~~

Key:

~~~text
zbx_vsan_api.py["{$VMWARE.URL}","{$VMWARE.USER}","{$VMWARE.PASSWORD}","{$VSAN.CLUSTER.MATCHES}","{$VSAN.CLUSTER.NOT_MATCHES}","{$VSAN.API.TIMEOUT}"]
~~~

The collector returns one JSON payload.

The template then uses:

- Dependent items for collector status and summary metrics
- Dependent LLD rules for vSAN objects
- Item prototypes for per-cluster, per-host, per-disk group, per-disk, per-VM, per-vDisk and per-network metrics
- Trigger prototypes for health, capacity, latency, network and resync conditions

---

## Low-Level Discovery Rules

| Discovery rule | Key | Purpose |
|---|---|---|
| vSAN: Cluster discovery | `vsan.cluster.discovery` | Discovers vSAN clusters. |
| vSAN: Host discovery | `vsan.host.discovery` | Discovers ESXi hosts participating in vSAN. |
| vSAN: Disk group discovery | `vsan.diskgroup.discovery` | Discovers vSAN disk groups. |
| vSAN: Capacity disk discovery | `vsan.capacity_disk.discovery` | Discovers vSAN capacity disks. |
| vSAN: VM performance discovery | `vsan.vm.discovery` | Discovers VM-level vSAN performance objects. |
| vSAN: Virtual disk performance discovery | `vsan.vdisk.discovery` | Discovers virtual disk performance objects. |
| vSAN: Network discovery | `vsan.network.discovery` | Discovers vSAN network interfaces/objects. |
| vSAN: Health check discovery | `vsan.health_check.discovery` | Discovers vSAN health checks. |

---

## Triggers Included

### Collector
- vSAN collector failed
- vSAN collector is slow
- vSAN API data is stale

### Cluster
- Cluster health warning/critical
- Capacity high/disaster
- Resync components detected
- Resync running too long
- Inaccessible objects
- Non-compliant objects
- Reduced availability objects
- Performance service not healthy
- Read/write latency high/disaster
- Network errors/drops
- Rebalance running
- Congestion high

### Host
- Host health not OK
- Host not contributing stats
- Failed/degraded disks
- Network errors/drops

### Disk Group
- Disk group health not OK
- Disk group usage high/very high
- Cache disk not healthy
- Failed disk detected
- Write latency high

### Capacity Disk
- Disk not healthy
- Disk usage high
- Disk write latency high

### VM / vDisk
- VM write latency high
- Virtual disk write latency high

### Network
- vSAN network health not OK
- Network utilization high
- Network errors/drops

### Health Checks
- vSAN health check warning
- vSAN health check failed

---

## Value Maps

### vSAN collector status
| Value | Meaning |
|---:|---|
| 0 | Failed |
| 1 | OK |

### vSAN health status
| Value | Meaning |
|---:|---|
| 0 | Unknown |
| 1 | OK |
| 2 | Warning |
| 3 | Critical |

### Yes/No
| Value | Meaning |
|---:|---|
| 0 | No |
| 1 | Yes |

---

## Validation & Troubleshooting

### Check ExternalScripts path

Package-based installation:

~~~bash
grep -i '^ExternalScripts' /etc/zabbix/zabbix_server.conf
ls -l /usr/lib/zabbix/externalscripts/
~~~

Docker-based installation:

~~~bash
docker exec -it <zabbix_server_container_name> bash -lc '
ls -l /usr/lib/zabbix/externalscripts/
ls -l /opt/zabbix-vsan-venv/bin/python3
'
~~~

### Test Python dependencies

~~~bash
/opt/zabbix-vsan-venv/bin/python3 -c "import pyVim, pyVmomi; print('pyVmomi OK')"
~~~

Inside Docker:

~~~bash
docker exec -it <zabbix_server_container_name> bash -lc '
/opt/zabbix-vsan-venv/bin/python3 -c "import pyVim, pyVmomi; print(\"pyVmomi OK\")"
'
~~~

### Test vCenter connectivity

~~~bash
curl -k -I https://vcenter.example.local/sdk
~~~

### If the master item is unsupported

Check:

- `zbx_vsan_api.py` is executable.
- The shebang points to a valid Python interpreter:
  - `#!/opt/zabbix-vsan-venv/bin/python3`
- The virtual environment exists inside the Zabbix Server/Proxy runtime.
- `pyvmomi` is installed in the virtual environment.
- `vsanapiutils.py` and `vsanmgmtObjects.py` are in the same directory as the collector or available in `PYTHONPATH`.
- Zabbix Server/Proxy timeout is high enough for the collector runtime.
- vCenter URL, username and password are correct.
- The vCenter user can see vSAN clusters.

### If the collector returns status 0

Check the dependent item:

~~~text
vSAN collector: Message
~~~

It contains the collector error message.

Common causes:

- Invalid vCenter credentials
- vCenter SDK URL unreachable
- Missing Python dependency
- Missing `vsanapiutils.py` or `vsanmgmtObjects.py`
- vSAN API call timeout
- Insufficient vCenter permissions

### If performance metrics are 0

Health and capacity metrics may still work even if vSAN Performance Manager API is unavailable or unreliable.

Check:

- vSAN Performance Service is enabled.
- vSAN performance data exists in vCenter.
- Collector can query performance objects.
- The selected time range has performance samples.

### If the collector is killed by timeout

The external script is controlled by the Zabbix Server/Proxy timeout.

Review:

- Zabbix Server/Proxy `Timeout`
- Docker environment variable, for example `ZBX_TIMEOUT`
- `{$VSAN.API.TIMEOUT}`
- `{$VSAN.UPDATE.INTERVAL}`
- Number of clusters/hosts/VMs being collected

If the environment is large, reduce scope first:

~~~text
{$VSAN.CLUSTER.MATCHES}
{$VSAN.CLUSTER.NOT_MATCHES}
~~~

---

## Security Notes

- Store `{$VMWARE.PASSWORD}` as a **Secret macro**.
- Use a dedicated read-only vCenter account.
- Restrict access to Zabbix template/host macros.
- Limit network access from Zabbix Server/Proxy to vCenter.
- Avoid placing credentials in scripts, logs, screenshots or tickets.
- Ensure ExternalScripts directory is writable only by administrators.

---

## Contributing

Contributions are welcome, including:

- Additional vSAN object coverage
- Improved collector error handling
- Performance optimization for large environments
- Trigger tuning and macro-based thresholds
- Dashboard examples
- Documentation improvements

Please open an issue with:

- Zabbix version
- vCenter version
- vSAN version
- Sanitized collector JSON sample
- Expected vs. actual behavior
- Relevant collector error message, if any

---

## License

Licensed under the MIT License. See the `LICENSE` file for details.

## Trademarks

All product names and trademarks are property of their respective owners.  
This project is not affiliated with, endorsed by, or sponsored by VMware, Broadcom or Zabbix.
