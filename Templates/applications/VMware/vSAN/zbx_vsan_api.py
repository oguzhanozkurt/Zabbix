#!/opt/zabbix-vsan-venv/bin/python3
# -*- coding: utf-8 -*-
"""
zbx_vsan_api.py

Zabbix 7.0 external check collector for the template:
  Template VMware vSAN by API

Expected Zabbix item key:
  zbx_vsan_api.py["{$VMWARE.URL}","{$VMWARE.USER}","{$VMWARE.PASSWORD}","{$VSAN.CLUSTER.MATCHES}","{$VSAN.CLUSTER.NOT_MATCHES}","{$VSAN.API.TIMEOUT}"]

What this script does:
  * Connects to vCenter with pyVmomi.
  * Discovers vSAN enabled clusters, ESXi hosts, vSAN datastores, disk groups,
    capacity disks, VMkernel/vSAN network interfaces, VMs and virtual disks.
  * Queries vSAN Health API when vsanapiutils.py and vsanmgmtObjects.py are available.
  * Queries vSphere performance counters for datastore/VM/vDisk/network metrics.
  * Produces one JSON payload consumed by the dependent items and LLD rules in the template.

Important:
  * vSAN Health and vSAN managed objects require VMware/Broadcom pyVmomi vSAN helper files
    (vsanapiutils.py and vsanmgmtObjects.py) to be in this script's directory or PYTHONPATH.
  * Disk group and physical disk performance metrics are best-effort. Where the vSAN
    Performance Manager API cannot be queried reliably in the local vCenter/vSAN version,
    the script returns 0 for these performance-only fields but still discovers/monitors
    health and capacity.

Exit behavior for Zabbix:
  * Always prints valid JSON to stdout.
  * On fatal failure, collector.status = 0 and collector.message contains the error.
"""

from __future__ import annotations

import atexit
import datetime as _dt
import json
import os
import re
import signal
import socket
import ssl
import sys
import time
import traceback
import urllib.parse
from typing import Any, Dict, Iterable, List, Optional, Tuple

SCRIPT_VERSION = "1.0.0"

# Optional runtime toggles. Keep defaults conservative for big environments.
ENABLE_VM_PERF = os.getenv("ZBX_VSAN_ENABLE_VM_PERF", "1") not in ("0", "false", "False", "no")
ENABLE_VDISK_PERF = os.getenv("ZBX_VSAN_ENABLE_VDISK_PERF", "1") not in ("0", "false", "False", "no")
ENABLE_NETWORK_DISCOVERY = os.getenv("ZBX_VSAN_ENABLE_NETWORK_DISCOVERY", "1") not in ("0", "false", "False", "no")
VM_LIMIT = int(os.getenv("ZBX_VSAN_VM_LIMIT", "300"))
VDISK_LIMIT = int(os.getenv("ZBX_VSAN_VDISK_LIMIT", "1200"))
PERF_INTERVAL_ID = int(os.getenv("ZBX_VSAN_PERF_INTERVAL_ID", "300"))
PERF_LOOKBACK_MIN = int(os.getenv("ZBX_VSAN_PERF_LOOKBACK_MIN", "15"))
DEBUG = os.getenv("ZBX_VSAN_DEBUG", "0") in ("1", "true", "True", "yes")

# Zabbix value map used by the template.
STATUS_UNKNOWN = 0
STATUS_OK = 1
STATUS_WARNING = 2
STATUS_CRITICAL = 3


def _debug(msg: str) -> None:
    if DEBUG:
        print(f"DEBUG: {msg}", file=sys.stderr)


def _json_default(obj: Any) -> str:
    return str(obj)


def build_empty_payload(status: int = STATUS_OK, message: str = "OK") -> Dict[str, Any]:
    return {
        "collector": {
            "status": int(status),
            "message": str(message),
            "timestamp": int(time.time()),
            "duration_sec": 0.0,
            "clusters_total": 0,
            "script_version": SCRIPT_VERSION,
        },
        "lld": {
            "clusters": [],
            "hosts": [],
            "diskgroups": [],
            "capacity_disks": [],
            "vms": [],
            "virtual_disks": [],
            "networks": [],
            "health_checks": [],
        },
        "clusters": [],
        "hosts": [],
        "diskgroups": [],
        "capacity_disks": [],
        "vms": [],
        "virtual_disks": [],
        "networks": [],
        "health_checks": [],
    }


def output_payload(payload: Dict[str, Any]) -> None:
    print(json.dumps(payload, default=_json_default, ensure_ascii=False, separators=(",", ":")))


def fatal_json(message: str, duration: float = 0.0) -> None:
    payload = build_empty_payload(STATUS_UNKNOWN, message)
    payload["collector"]["status"] = 0
    payload["collector"]["duration_sec"] = round(duration, 3)
    output_payload(payload)


def parse_url(url: str) -> Tuple[str, int]:
    """Return vCenter host and port from https://vcenter/sdk or https://vcenter:443/sdk."""
    parsed = urllib.parse.urlparse(url if "://" in url else f"https://{url}")
    host = parsed.hostname or parsed.path.split("/")[0]
    port = parsed.port or 443
    if not host:
        raise ValueError(f"Cannot parse vCenter host from URL: {url}")
    return host, int(port)


def install_timeout(seconds: int) -> None:
    if seconds <= 0:
        return

    def _handler(signum, frame):  # type: ignore[no-untyped-def]
        raise TimeoutError(f"Collector timeout after {seconds} seconds")

    try:
        signal.signal(signal.SIGALRM, _handler)
        signal.alarm(seconds)
    except Exception:
        # Not available on all platforms; socket timeout is still applied.
        pass


def cancel_timeout() -> None:
    try:
        signal.alarm(0)
    except Exception:
        pass


def safe_get(obj: Any, *names: str, default: Any = None) -> Any:
    """Try multiple attribute/key names on pyVmomi objects, dicts or plain objects."""
    if obj is None:
        return default
    for name in names:
        try:
            if isinstance(obj, dict) and name in obj:
                return obj[name]
            if hasattr(obj, name):
                val = getattr(obj, name)
                if val is not None:
                    return val
        except Exception:
            continue
    return default


def to_int(value: Any, default: int = 0) -> int:
    try:
        if value is None:
            return default
        if isinstance(value, bool):
            return 1 if value else 0
        return int(float(str(value)))
    except Exception:
        return default


def to_float(value: Any, default: float = 0.0) -> float:
    try:
        if value is None:
            return default
        return float(str(value))
    except Exception:
        return default


def pct(used: float, total: float) -> float:
    if total <= 0:
        return 0.0
    return round((used / total) * 100.0, 3)


def moid(obj: Any) -> str:
    return str(safe_get(obj, "_moId", "moid", default=""))


def obj_name(obj: Any) -> str:
    return str(safe_get(obj, "name", default=moid(obj) or "unknown"))


def datacenter_name(obj: Any) -> str:
    """Walk parents until Datacenter is reached."""
    current = obj
    for _ in range(20):
        if current is None:
            return ""
        if current.__class__.__name__ == "vim.Datacenter" or current.__class__.__name__.endswith("Datacenter"):
            return obj_name(current)
        current = safe_get(current, "parent", default=None)
    return ""


def normalize_status(value: Any) -> int:
    """Normalize vSphere/vSAN health values to 0/1/2/3."""
    if value is None:
        return STATUS_UNKNOWN
    if isinstance(value, bool):
        return STATUS_OK if value else STATUS_CRITICAL
    if isinstance(value, (int, float)):
        iv = int(value)
        if iv in (0, 1, 2, 3):
            return iv
        return STATUS_UNKNOWN
    text = str(value).strip().lower()
    # Enum values often look like vim.ManagedEntity.Status.green.
    if "." in text:
        text = text.split(".")[-1]
    ok_values = {"ok", "green", "healthy", "health", "passed", "pass", "success", "normal", "online", "up", "true"}
    warn_values = {"yellow", "warning", "warn", "degraded", "reduced", "reducedavailability", "reduced-availability"}
    crit_values = {"red", "critical", "crit", "error", "failed", "failure", "down", "inaccessible", "false"}
    unknown_values = {"unknown", "gray", "grey", "unset", "notavailable", "na", "none", ""}
    if text in ok_values:
        return STATUS_OK
    if text in warn_values:
        return STATUS_WARNING
    if text in crit_values:
        return STATUS_CRITICAL
    if text in unknown_values:
        return STATUS_UNKNOWN
    if "green" in text or "pass" in text or "healthy" in text:
        return STATUS_OK
    if "yellow" in text or "warn" in text or "reduced" in text or "degrad" in text:
        return STATUS_WARNING
    if "red" in text or "fail" in text or "error" in text or "critical" in text or "inaccessible" in text:
        return STATUS_CRITICAL
    return STATUS_UNKNOWN


def try_import_pyvmomi():
    try:
        from pyVim import connect  # type: ignore
        from pyVmomi import vim, vmodl  # type: ignore
        return connect, vim, vmodl
    except Exception as exc:
        raise RuntimeError(
            "pyVmomi is not installed or cannot be imported. Install with: pip3 install pyvmomi. "
            f"Original error: {exc}"
        )


def connect_vcenter(url: str, username: str, password: str, timeout: int):
    connect, vim, _vmodl = try_import_pyvmomi()
    host, port = parse_url(url)
    socket.setdefaulttimeout(max(timeout, 10))
    context = ssl._create_unverified_context()
    si = connect.SmartConnect(host=host, user=username, pwd=password, port=port, sslContext=context)
    atexit.register(connect.Disconnect, si)
    return si, vim, context, host, port


def get_view(content: Any, vim: Any, types: List[Any]) -> List[Any]:
    view = content.viewManager.CreateContainerView(content.rootFolder, types, True)
    try:
        return list(view.view)
    finally:
        try:
            view.Destroy()
        except Exception:
            pass


def is_vsan_datastore(ds: Any) -> bool:
    try:
        summary = ds.summary
        ds_type = str(getattr(summary, "type", "")).lower()
        name = str(getattr(summary, "name", getattr(ds, "name", ""))).lower()
        return ds_type == "vsan" or "vsan" in name
    except Exception:
        return False


def get_cluster_vsan_datastores(cluster: Any) -> List[Any]:
    out = []
    for ds in list(safe_get(cluster, "datastore", default=[]) or []):
        if is_vsan_datastore(ds):
            out.append(ds)
    return out


def cluster_vsan_enabled(cluster: Any) -> bool:
    try:
        cfg = safe_get(cluster, "configurationEx", default=None)
        vsan_cfg = safe_get(cfg, "vsanConfigInfo", default=None)
        enabled = safe_get(vsan_cfg, "enabled", default=None)
        if enabled is not None:
            return bool(enabled)
    except Exception:
        pass
    return bool(get_cluster_vsan_datastores(cluster))


def matches_filters(name: str, include_re: str, exclude_re: str) -> bool:
    try:
        if include_re and not re.search(include_re, name):
            return False
    except re.error:
        if include_re not in name:
            return False
    if exclude_re and exclude_re != "CHANGE_IF_NEEDED":
        try:
            if re.search(exclude_re, name):
                return False
        except re.error:
            if exclude_re in name:
                return False
    return True


def sum_vsan_datastore_capacity(cluster: Any) -> Dict[str, float]:
    total = free = uncommitted = 0.0
    for ds in get_cluster_vsan_datastores(cluster):
        summary = safe_get(ds, "summary", default=None)
        total += to_float(safe_get(summary, "capacity", default=0))
        free += to_float(safe_get(summary, "freeSpace", default=0))
        uncommitted += to_float(safe_get(summary, "uncommitted", default=0))
    used = max(total - free, 0.0)
    return {
        "capacity_total_bytes": int(total),
        "capacity_used_bytes": int(used),
        "capacity_free_bytes": int(free),
        "capacity_used_pct": pct(used, total),
        "uncommitted_bytes": int(uncommitted),
    }


class PerfHelper:
    def __init__(self, content: Any, vim: Any):
        self.content = content
        self.vim = vim
        self.pm = content.perfManager
        self.counter_by_name: Dict[str, int] = {}
        self.counter_name_by_id: Dict[int, str] = {}
        self._build_counter_cache()

    def _build_counter_cache(self) -> None:
        for c in self.pm.perfCounter:
            try:
                full = f"{c.groupInfo.key}.{c.nameInfo.key}.{c.rollupType}"
                self.counter_by_name[full] = int(c.key)
                self.counter_name_by_id[int(c.key)] = full
            except Exception:
                continue

    def query(self, entity: Any, counters: Dict[str, str], instance: str = "*", max_sample: int = 1) -> Dict[str, List[Tuple[str, float]]]:
        """Return {logical_name: [(instance, value), ...]} for one entity."""
        now = _dt.datetime.now(_dt.timezone.utc).replace(tzinfo=None)
        start = now - _dt.timedelta(minutes=PERF_LOOKBACK_MIN)
        metric_ids = []
        logical_by_counter: Dict[int, str] = {}
        for logical, full_name in counters.items():
            cid = self.counter_by_name.get(full_name)
            if cid is None:
                continue
            logical_by_counter[cid] = logical
            metric_ids.append(self.vim.PerformanceManager.MetricId(counterId=cid, instance=instance))
        if not metric_ids:
            return {}
        spec = self.vim.PerformanceManager.QuerySpec(
            entity=entity,
            metricId=metric_ids,
            startTime=start,
            endTime=now,
            maxSample=max_sample,
            intervalId=PERF_INTERVAL_ID,
        )
        try:
            results = self.pm.QueryPerf(querySpec=[spec])
        except Exception as exc:
            _debug(f"QueryPerf failed for {obj_name(entity)}: {exc}")
            return {}
        out: Dict[str, List[Tuple[str, float]]] = {k: [] for k in counters.keys()}
        for res in results or []:
            for series in safe_get(res, "value", default=[]) or []:
                cid = to_int(safe_get(series, "id", default=None).counterId, -1) if safe_get(series, "id", default=None) else -1
                logical = logical_by_counter.get(cid)
                if not logical:
                    continue
                values = safe_get(series, "value", default=[]) or []
                if not values:
                    continue
                inst = str(safe_get(safe_get(series, "id", default=None), "instance", default=""))
                out.setdefault(logical, []).append((inst, to_float(values[-1], 0.0)))
        return out

    @staticmethod
    def aggregate(rows: List[Tuple[str, float]], mode: str = "sum") -> float:
        vals = [v for _i, v in rows if v is not None]
        if not vals:
            return 0.0
        if mode == "avg":
            return round(sum(vals) / len(vals), 3)
        if mode == "max":
            return round(max(vals), 3)
        return round(sum(vals), 3)


DATASTORE_COUNTERS = {
    "read_latency_ms": "datastore.totalReadLatency.average",
    "write_latency_ms": "datastore.totalWriteLatency.average",
    "read_iops": "datastore.numberReadAveraged.average",
    "write_iops": "datastore.numberWriteAveraged.average",
    "read_kbps": "datastore.read.average",
    "write_kbps": "datastore.write.average",
}

VIRTUAL_DISK_COUNTERS = {
    "read_latency_ms": "virtualDisk.totalReadLatency.average",
    "write_latency_ms": "virtualDisk.totalWriteLatency.average",
    "read_iops": "virtualDisk.numberReadAveraged.average",
    "write_iops": "virtualDisk.numberWriteAveraged.average",
    "read_kbps": "virtualDisk.read.average",
    "write_kbps": "virtualDisk.write.average",
}

NETWORK_COUNTERS = {
    "rx_kbps": "net.received.average",
    "tx_kbps": "net.transmitted.average",
    "rx_packets": "net.packetsRx.summation",
    "tx_packets": "net.packetsTx.summation",
    "errors_rx": "net.errorsRx.summation",
    "errors_tx": "net.errorsTx.summation",
    "drops_rx": "net.droppedRx.summation",
    "drops_tx": "net.droppedTx.summation",
}


def query_cluster_datastore_perf(cluster: Any, perf: PerfHelper) -> Dict[str, float]:
    rows_by_metric: Dict[str, List[Tuple[str, float]]] = {k: [] for k in DATASTORE_COUNTERS}
    for ds in get_cluster_vsan_datastores(cluster):
        ds_perf = perf.query(ds, DATASTORE_COUNTERS, instance="*")
        for k, rows in ds_perf.items():
            rows_by_metric.setdefault(k, []).extend(rows)
    read_kbps = perf.aggregate(rows_by_metric.get("read_kbps", []), "sum")
    write_kbps = perf.aggregate(rows_by_metric.get("write_kbps", []), "sum")
    return {
        "read_latency_ms": perf.aggregate(rows_by_metric.get("read_latency_ms", []), "avg"),
        "write_latency_ms": perf.aggregate(rows_by_metric.get("write_latency_ms", []), "avg"),
        "read_iops": perf.aggregate(rows_by_metric.get("read_iops", []), "sum"),
        "write_iops": perf.aggregate(rows_by_metric.get("write_iops", []), "sum"),
        "read_throughput_bps": int(read_kbps * 1024),
        "write_throughput_bps": int(write_kbps * 1024),
    }


def query_vm_vdisk_perf(vm: Any, cluster_name: str, perf: PerfHelper) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
    vm_id = moid(vm) or obj_name(vm)
    vm_name = obj_name(vm)
    vm_perf = perf.query(vm, VIRTUAL_DISK_COUNTERS, instance="*")

    def agg(metric: str, mode: str = "sum") -> float:
        return perf.aggregate(vm_perf.get(metric, []), mode)

    vm_entry = {
        "cluster": cluster_name,
        "id": vm_id,
        "name": vm_name,
        "read_latency_ms": agg("read_latency_ms", "avg"),
        "write_latency_ms": agg("write_latency_ms", "avg"),
        "read_iops": agg("read_iops", "sum"),
        "write_iops": agg("write_iops", "sum"),
        "read_throughput_bps": int(agg("read_kbps", "sum") * 1024),
        "write_throughput_bps": int(agg("write_kbps", "sum") * 1024),
        "congestion": 0,
    }

    # Build per-virtual-disk rows from metric instances returned by vCenter.
    instances = set()
    for rows in vm_perf.values():
        for inst, _val in rows:
            if inst:
                instances.add(inst)
    vdisks: List[Dict[str, Any]] = []
    for inst in sorted(instances):
        metric_rows = {}
        for metric, rows in vm_perf.items():
            metric_rows[metric] = [v for i, v in rows if i == inst]

        def one(metric: str, mode: str = "sum") -> float:
            vals = metric_rows.get(metric, [])
            if not vals:
                return 0.0
            if mode == "avg":
                return round(sum(vals) / len(vals), 3)
            return round(sum(vals), 3)

        vdisks.append({
            "cluster": cluster_name,
            "vm_id": vm_id,
            "vm_name": vm_name,
            "id": inst,
            "name": inst,
            "read_latency_ms": one("read_latency_ms", "avg"),
            "write_latency_ms": one("write_latency_ms", "avg"),
            "read_iops": one("read_iops", "sum"),
            "write_iops": one("write_iops", "sum"),
            "read_throughput_bps": int(one("read_kbps", "sum") * 1024),
            "write_throughput_bps": int(one("write_kbps", "sum") * 1024),
            "congestion": 0,
        })
    return vm_entry, vdisks


def get_vms_on_vsan_datastores(cluster: Any) -> List[Any]:
    seen = set()
    out: List[Any] = []
    for ds in get_cluster_vsan_datastores(cluster):
        for vm in list(safe_get(ds, "vm", default=[]) or []):
            mid = moid(vm) or obj_name(vm)
            if mid not in seen:
                seen.add(mid)
                out.append(vm)
    return out


def list_host_vsan_vmks(host: Any) -> List[str]:
    """Best-effort vSAN VMkernel interface discovery."""
    devices: List[str] = []
    try:
        vsan_sys = host.configManager.vsanSystem
        cfg = safe_get(vsan_sys, "config", default=None)
        net_info = safe_get(cfg, "networkInfo", default=None)
        ports = safe_get(net_info, "port", "ports", default=[]) or []
        for p in ports:
            dev = safe_get(p, "device", "portgroup", "vmknic", default=None)
            if dev:
                devices.append(str(dev))
    except Exception:
        pass
    if devices:
        return sorted(set(devices))

    # Fallback: include all VMkernel NICs. This may include management/vMotion, but
    # keeps the network panels populated when vSAN networkInfo is not exposed.
    try:
        for vnic in host.config.network.vnic:
            dev = safe_get(vnic, "device", default="")
            portgroup = str(safe_get(safe_get(vnic, "spec", default=None), "portgroup", default="")).lower()
            if dev and ("vsan" in portgroup or os.getenv("ZBX_VSAN_NETWORK_ALL_VMK", "0") == "1"):
                devices.append(str(dev))
    except Exception:
        pass
    return sorted(set(devices))


def query_host_network_perf(host: Any, cluster_name: str, perf: PerfHelper) -> Tuple[List[Dict[str, Any]], Dict[str, float]]:
    networks: List[Dict[str, Any]] = []
    host_totals = {"network_rx_bps": 0.0, "network_tx_bps": 0.0, "network_errors": 0.0, "network_drops": 0.0}
    if not ENABLE_NETWORK_DISCOVERY:
        return networks, host_totals
    vmks = list_host_vsan_vmks(host)
    if not vmks:
        return networks, host_totals
    perf_rows = perf.query(host, NETWORK_COUNTERS, instance="*")
    # Perf instances can be vmnic/vmk names depending on vCenter counters. Match by interface name.
    for ifname in vmks:
        def rows_for(metric: str) -> List[Tuple[str, float]]:
            return [(i, v) for i, v in perf_rows.get(metric, []) if i == ifname or ifname in i]
        rx_bps = int(perf.aggregate(rows_for("rx_kbps"), "sum") * 1024)
        tx_bps = int(perf.aggregate(rows_for("tx_kbps"), "sum") * 1024)
        errors = int(perf.aggregate(rows_for("errors_rx"), "sum") + perf.aggregate(rows_for("errors_tx"), "sum"))
        drops = int(perf.aggregate(rows_for("drops_rx"), "sum") + perf.aggregate(rows_for("drops_tx"), "sum"))
        rx_packets = int(perf.aggregate(rows_for("rx_packets"), "sum"))
        tx_packets = int(perf.aggregate(rows_for("tx_packets"), "sum"))
        # Link speed per vmk is not simple to map; util_pct is left at 0 unless the
        # user extends the script with pNIC mapping.
        networks.append({
            "cluster": cluster_name,
            "host": obj_name(host),
            "ifname": ifname,
            "health": STATUS_OK if errors == 0 and drops == 0 else STATUS_WARNING,
            "rx_bps": rx_bps,
            "tx_bps": tx_bps,
            "rx_packets": rx_packets,
            "tx_packets": tx_packets,
            "util_pct": 0,
            "errors": errors,
            "drops": drops,
        })
        host_totals["network_rx_bps"] += rx_bps
        host_totals["network_tx_bps"] += tx_bps
        host_totals["network_errors"] += errors
        host_totals["network_drops"] += drops
    return networks, host_totals


def disk_capacity_bytes(disk: Any) -> int:
    cap = safe_get(disk, "capacity", default=None)
    if cap is None:
        return 0
    block = to_int(safe_get(cap, "block", default=0), 0)
    block_size = to_int(safe_get(cap, "blockSize", default=0), 0)
    if block and block_size:
        return int(block * block_size)
    return to_int(cap, 0)


def disk_health_from_state(disk: Any) -> int:
    state = safe_get(disk, "operationalState", "state", default=None)
    if isinstance(state, (list, tuple)):
        text = " ".join(str(x).lower() for x in state)
    else:
        text = str(state or "").lower()
    if not text:
        return STATUS_OK
    if any(x in text for x in ["error", "off", "lost", "degraded", "dead", "failed"]):
        return STATUS_CRITICAL
    return STATUS_OK


def collect_diskgroups_from_host(cluster_name: str, host: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Read host.configManager.vsanSystem.config.storageInfo.diskMapping."""
    groups: List[Dict[str, Any]] = []
    disks: List[Dict[str, Any]] = []
    try:
        vsan_sys = host.configManager.vsanSystem
        cfg = safe_get(vsan_sys, "config", default=None)
        storage = safe_get(cfg, "storageInfo", default=None)
        mappings = safe_get(storage, "diskMapping", "diskMappings", default=[]) or []
    except Exception as exc:
        _debug(f"Cannot read disk mappings for {obj_name(host)}: {exc}")
        return groups, disks

    for idx, mapping in enumerate(mappings, start=1):
        cache = safe_get(mapping, "ssd", "cache", "cacheDisk", default=None)
        capacity_disks = list(safe_get(mapping, "nonSsd", "capacity", "capacityDisks", default=[]) or [])
        cache_uuid = str(
            safe_get(safe_get(cache, "vsanDiskInfo", default=None), "vsanUuid", default=None)
            or safe_get(cache, "canonicalName", "deviceName", "uuid", default=None)
            or f"{obj_name(host)}-dg-{idx}"
        )
        dg_name = f"{obj_name(host)} - DG{idx}"
        total = sum(disk_capacity_bytes(d) for d in capacity_disks)
        # vSphere local disk mapping does not expose per-disk used capacity consistently.
        used = 0
        failed = sum(1 for d in capacity_disks if disk_health_from_state(d) == STATUS_CRITICAL)
        cache_health = disk_health_from_state(cache)
        dg_health = STATUS_CRITICAL if failed > 0 or cache_health == STATUS_CRITICAL else STATUS_OK
        groups.append({
            "cluster": cluster_name,
            "host": obj_name(host),
            "uuid": cache_uuid,
            "name": dg_name,
            "health": dg_health,
            "used_pct": pct(used, total),
            "capacity_bytes": int(total),
            "used_bytes": int(used),
            "free_bytes": int(max(total - used, 0)),
            "cache_disk_health": cache_health,
            "capacity_disk_count": len(capacity_disks),
            "failed_disk_count": failed,
            "read_latency_ms": 0,
            "write_latency_ms": 0,
            "read_iops": 0,
            "write_iops": 0,
            "read_throughput_bps": 0,
            "write_throughput_bps": 0,
            "congestion": 0,
        })
        for d in capacity_disks:
            d_uuid = str(
                safe_get(safe_get(d, "vsanDiskInfo", default=None), "vsanUuid", default=None)
                or safe_get(d, "canonicalName", "deviceName", "uuid", default=None)
                or f"{cache_uuid}-{len(disks)+1}"
            )
            d_name = str(safe_get(d, "canonicalName", "deviceName", "displayName", default=d_uuid))
            d_total = disk_capacity_bytes(d)
            d_health = disk_health_from_state(d)
            disks.append({
                "cluster": cluster_name,
                "host": obj_name(host),
                "diskgroup_uuid": cache_uuid,
                "uuid": d_uuid,
                "name": d_name,
                "type": "capacity",
                "health": d_health,
                "used_pct": 0,
                "capacity_bytes": int(d_total),
                "used_bytes": 0,
                "free_bytes": int(d_total),
                "read_latency_ms": 0,
                "write_latency_ms": 0,
                "read_iops": 0,
                "write_iops": 0,
                "read_throughput_bps": 0,
                "write_throughput_bps": 0,
            })
    return groups, disks


def get_vsan_mos(si: Any, context: Any, host: str, port: int) -> Tuple[Optional[Dict[str, Any]], List[str]]:
    warnings: List[str] = []
    try:
        # These files are distributed in the pyVmomi repository samples and are
        # required for vSAN managed object bindings.
        import vsanapiutils  # type: ignore
        try:
            version = vsanapiutils.GetLatestVmodlVersion(host, port)
            vc_mos = vsanapiutils.GetVsanVcMos(si._stub, context=context, version=version)
        except Exception:
            vc_mos = vsanapiutils.GetVsanVcMos(si._stub, context=context)
        return vc_mos, warnings
    except Exception as exc:
        warnings.append(
            "vSAN API helper import failed; vSAN Health API metrics will be limited. "
            "Copy vsanapiutils.py and vsanmgmtObjects.py to externalscripts or PYTHONPATH. "
            f"Original error: {exc}"
        )
        return None, warnings


def call_first(obj: Any, method_names: Iterable[str], *args: Any, **kwargs: Any) -> Any:
    for method_name in method_names:
        method = safe_get(obj, method_name, default=None)
        if not method:
            continue
        # Try keyword call first, then positional fallbacks.
        try:
            return method(*args, **kwargs)
        except TypeError:
            try:
                return method(*args)
            except Exception:
                continue
        except Exception:
            continue
    return None


def query_health_summary(vc_mos: Optional[Dict[str, Any]], cluster: Any) -> Tuple[Optional[Any], List[str]]:
    warnings: List[str] = []
    if not vc_mos:
        return None, warnings
    health_sys = vc_mos.get("vsan-cluster-health-system")
    if not health_sys:
        warnings.append("vSAN health system managed object was not found")
        return None, warnings
    # The preferred API for vSAN cluster-wide health. Signatures vary slightly
    # across vSAN bindings, so try multiple safe forms.
    attempts = [
        lambda: health_sys.VsanQueryVcClusterHealthSummary(cluster=cluster, fetchFromCache=True),
        lambda: health_sys.VsanQueryVcClusterHealthSummary(cluster=cluster, includeObjUuids=False, fetchFromCache=True),
        lambda: health_sys.VsanQueryVcClusterHealthSummary(cluster=cluster),
        lambda: health_sys.VsanQueryVcClusterHealthSummary(cluster),
    ]
    for f in attempts:
        try:
            return f(), warnings
        except Exception as exc:
            last = exc
            continue
    warnings.append(f"VsanQueryVcClusterHealthSummary failed for {obj_name(cluster)}: {last}")
    return None, warnings


def extract_health_groups(summary: Any) -> List[Any]:
    return list(
        safe_get(summary, "groups", "group", "healthSummary", "healthGroups", "testGroups", default=[]) or []
    )


def extract_tests(group: Any) -> List[Any]:
    return list(safe_get(group, "tests", "test", "testResult", "results", default=[]) or [])


def parse_health_summary(cluster_name: str, summary: Any) -> Tuple[int, List[Dict[str, Any]], Dict[str, int]]:
    health_checks: List[Dict[str, Any]] = []
    counts = {
        "inaccessible_objects": 0,
        "noncompliant_objects": 0,
        "reduced_availability_objects": 0,
    }
    if summary is None:
        return STATUS_UNKNOWN, health_checks, counts

    overall_raw = safe_get(summary, "overallHealth", "overallStatus", "clusterStatus", "health", default=None)
    overall = normalize_status(overall_raw)
    worst = overall
    groups = extract_health_groups(summary)

    for gidx, group in enumerate(groups, start=1):
        group_name = str(safe_get(group, "groupName", "name", "label", "id", default=f"Group {gidx}"))
        group_id = str(safe_get(group, "groupId", "id", "key", default=group_name))
        group_status = normalize_status(safe_get(group, "groupHealth", "health", "status", default=None))
        tests = extract_tests(group)
        if not tests:
            if group_status != STATUS_UNKNOWN:
                health_checks.append({
                    "cluster": cluster_name,
                    "id": group_id,
                    "group": group_name,
                    "name": group_name,
                    "status": group_status,
                    "message": str(safe_get(group, "description", "message", "details", default="")),
                })
                worst = max(worst, group_status)
            continue
        for tidx, test in enumerate(tests, start=1):
            check_id = str(safe_get(test, "testId", "id", "key", default=f"{group_id}.{tidx}"))
            check_name = str(safe_get(test, "testName", "name", "label", default=check_id))
            status = normalize_status(safe_get(test, "testHealth", "health", "status", "result", default=None))
            message = str(safe_get(test, "details", "detail", "description", "message", "summary", default=""))
            health_checks.append({
                "cluster": cluster_name,
                "id": check_id,
                "group": group_name,
                "name": check_name,
                "status": status,
                "message": message,
            })
            worst = max(worst, status)
            # Best-effort object health count extraction from text/details.
            text = f"{group_name} {check_name} {message}".lower()
            nums = [int(x) for x in re.findall(r"\b(\d+)\b", text)]
            n = max(nums) if nums else 0
            if "inaccessible" in text:
                counts["inaccessible_objects"] = max(counts["inaccessible_objects"], n)
            if "non-compliant" in text or "noncompliant" in text or "non compliant" in text:
                counts["noncompliant_objects"] = max(counts["noncompliant_objects"], n)
            if "reduced availability" in text or "reduced-availability" in text:
                counts["reduced_availability_objects"] = max(counts["reduced_availability_objects"], n)

    if overall == STATUS_UNKNOWN and worst != STATUS_UNKNOWN:
        overall = worst
    return overall, health_checks, counts


def query_rebalance_running(vc_mos: Optional[Dict[str, Any]], cluster: Any) -> int:
    if not vc_mos:
        return 0
    health_sys = vc_mos.get("vsan-cluster-health-system")
    if not health_sys:
        return 0
    for method_name in ["VsanHealthIsRebalanceRunning", "VsanIsRebalanceRunning"]:
        method = safe_get(health_sys, method_name, default=None)
        if method:
            try:
                return 1 if bool(method(cluster=cluster)) else 0
            except Exception:
                try:
                    return 1 if bool(method(cluster)) else 0
                except Exception:
                    pass
    return 0


def build_lld_from_payload(payload: Dict[str, Any]) -> None:
    lld = payload["lld"]

    for c in payload["clusters"]:
        lld["clusters"].append({
            "{#CLUSTER.ID}": c.get("id", c.get("name", "")),
            "{#CLUSTER.NAME}": c.get("name", ""),
            "{#DATACENTER.NAME}": c.get("datacenter", ""),
        })
    for h in payload["hosts"]:
        lld["hosts"].append({
            "{#CLUSTER.ID}": h.get("cluster_id", h.get("cluster", "")),
            "{#CLUSTER.NAME}": h.get("cluster", ""),
            "{#HOST.ID}": h.get("id", h.get("name", "")),
            "{#HOST.NAME}": h.get("name", ""),
        })
    for dg in payload["diskgroups"]:
        lld["diskgroups"].append({
            "{#CLUSTER.NAME}": dg.get("cluster", ""),
            "{#HOST.NAME}": dg.get("host", ""),
            "{#DISKGROUP.UUID}": dg.get("uuid", ""),
            "{#DISKGROUP.NAME}": dg.get("name", dg.get("uuid", "")),
        })
    for d in payload["capacity_disks"]:
        lld["capacity_disks"].append({
            "{#CLUSTER.NAME}": d.get("cluster", ""),
            "{#HOST.NAME}": d.get("host", ""),
            "{#DISKGROUP.UUID}": d.get("diskgroup_uuid", ""),
            "{#DISK.UUID}": d.get("uuid", ""),
            "{#DISK.NAME}": d.get("name", d.get("uuid", "")),
            "{#DISK.TYPE}": d.get("type", "capacity"),
        })
    for vm in payload["vms"]:
        lld["vms"].append({
            "{#CLUSTER.NAME}": vm.get("cluster", ""),
            "{#VM.ID}": vm.get("id", ""),
            "{#VM.NAME}": vm.get("name", ""),
        })
    for vd in payload["virtual_disks"]:
        lld["virtual_disks"].append({
            "{#CLUSTER.NAME}": vd.get("cluster", ""),
            "{#VM.ID}": vd.get("vm_id", ""),
            "{#VM.NAME}": vd.get("vm_name", ""),
            "{#VDISK.ID}": vd.get("id", ""),
            "{#VDISK.NAME}": vd.get("name", ""),
        })
    for net in payload["networks"]:
        lld["networks"].append({
            "{#CLUSTER.NAME}": net.get("cluster", ""),
            "{#HOST.NAME}": net.get("host", ""),
            "{#IF.NAME}": net.get("ifname", ""),
        })
    for hc in payload["health_checks"]:
        lld["health_checks"].append({
            "{#CLUSTER.NAME}": hc.get("cluster", ""),
            "{#CHECK.ID}": hc.get("id", ""),
            "{#CHECK.GROUP}": hc.get("group", ""),
            "{#CHECK.NAME}": hc.get("name", ""),
        })


def collect(url: str, username: str, password: str, include_re: str, exclude_re: str, timeout: int) -> Dict[str, Any]:
    start_ts = time.time()
    payload = build_empty_payload(STATUS_OK, "OK")
    warnings: List[str] = []

    si, vim, ssl_context, vc_host, vc_port = connect_vcenter(url, username, password, timeout)
    content = si.RetrieveContent()
    perf = PerfHelper(content, vim)
    vc_mos, mos_warnings = get_vsan_mos(si, ssl_context, vc_host, vc_port)
    warnings.extend(mos_warnings)

    clusters = [c for c in get_view(content, vim, [vim.ClusterComputeResource]) if cluster_vsan_enabled(c)]
    clusters = [c for c in clusters if matches_filters(obj_name(c), include_re, exclude_re)]

    for cluster in clusters:
        c_name = obj_name(cluster)
        c_id = moid(cluster) or c_name
        dc_name = datacenter_name(cluster)
        cap = sum_vsan_datastore_capacity(cluster)
        health_summary, health_warnings = query_health_summary(vc_mos, cluster)
        warnings.extend(health_warnings)
        health_status, health_checks, object_counts = parse_health_summary(c_name, health_summary)
        ds_perf = query_cluster_datastore_perf(cluster, perf)
        rebalance = query_rebalance_running(vc_mos, cluster)

        c_entry = {
            "id": c_id,
            "name": c_name,
            "datacenter": dc_name,
            "health": health_status if health_status != STATUS_UNKNOWN else STATUS_OK,
            "health_text": {0: "unknown", 1: "green", 2: "yellow", 3: "red"}.get(health_status, "unknown"),
            "dedup_ratio": 0,
            "compression_ratio": 0,
            "resync_components": 0,
            "resync_bytes_remaining": 0,
            "resync_eta_sec": 0,
            "inaccessible_objects": object_counts.get("inaccessible_objects", 0),
            "noncompliant_objects": object_counts.get("noncompliant_objects", 0),
            "reduced_availability_objects": object_counts.get("reduced_availability_objects", 0),
            "object_count": 0,
            "perf_service_health": STATUS_OK,
            "network_rx_bps": 0,
            "network_tx_bps": 0,
            "network_errors": 0,
            "network_drops": 0,
            "rebalance_running": rebalance,
            "congestion": 0,
        }
        c_entry.update(cap)
        c_entry.update(ds_perf)
        payload["clusters"].append(c_entry)

        payload["health_checks"].extend(health_checks)

        # Hosts, disk groups, capacity disks, network.
        for host in list(safe_get(cluster, "host", default=[]) or []):
            h_name = obj_name(host)
            h_id = moid(host) or h_name
            dgs, cap_disks = collect_diskgroups_from_host(c_name, host)
            payload["diskgroups"].extend(dgs)
            payload["capacity_disks"].extend(cap_disks)
            networks, net_totals = query_host_network_perf(host, c_name, perf)
            payload["networks"].extend(networks)
            failed_disks = sum(to_int(dg.get("failed_disk_count", 0)) for dg in dgs)
            degraded_disks = 0
            maintenance = 1 if bool(safe_get(safe_get(host, "runtime", default=None), "inMaintenanceMode", default=False)) else 0
            host_health = STATUS_WARNING if maintenance else (STATUS_CRITICAL if failed_disks else STATUS_OK)
            payload["hosts"].append({
                "cluster": c_name,
                "cluster_id": c_id,
                "id": h_id,
                "name": h_name,
                "health": host_health,
                "contributing_stats": STATUS_OK,
                "maintenance_mode": maintenance,
                "diskgroup_count": len(dgs),
                "failed_disk_count": int(failed_disks),
                "degraded_disk_count": int(degraded_disks),
                "network_errors": int(net_totals.get("network_errors", 0)),
                "network_drops": int(net_totals.get("network_drops", 0)),
                "read_latency_ms": 0,
                "write_latency_ms": 0,
                "read_iops": 0,
                "write_iops": 0,
                "read_throughput_bps": 0,
                "write_throughput_bps": 0,
                "network_rx_bps": int(net_totals.get("network_rx_bps", 0)),
                "network_tx_bps": int(net_totals.get("network_tx_bps", 0)),
            })
            # Roll network totals up to cluster.
            c_entry["network_rx_bps"] += int(net_totals.get("network_rx_bps", 0))
            c_entry["network_tx_bps"] += int(net_totals.get("network_tx_bps", 0))
            c_entry["network_errors"] += int(net_totals.get("network_errors", 0))
            c_entry["network_drops"] += int(net_totals.get("network_drops", 0))

        # VM and virtual disk performance from vSAN datastores.
        if ENABLE_VM_PERF:
            vms = get_vms_on_vsan_datastores(cluster)[:VM_LIMIT]
            if len(get_vms_on_vsan_datastores(cluster)) > VM_LIMIT:
                warnings.append(f"VM discovery for {c_name} was limited to {VM_LIMIT} VMs by ZBX_VSAN_VM_LIMIT")
            vdisk_counter = 0
            for vm in vms:
                try:
                    vm_entry, vdisk_entries = query_vm_vdisk_perf(vm, c_name, perf)
                    payload["vms"].append(vm_entry)
                    if ENABLE_VDISK_PERF:
                        remaining = max(VDISK_LIMIT - vdisk_counter, 0)
                        payload["virtual_disks"].extend(vdisk_entries[:remaining])
                        vdisk_counter += min(len(vdisk_entries), remaining)
                        if vdisk_counter >= VDISK_LIMIT:
                            warnings.append(f"Virtual disk discovery was limited to {VDISK_LIMIT} disks by ZBX_VSAN_VDISK_LIMIT")
                            break
                except Exception as exc:
                    warnings.append(f"VM performance query failed for {obj_name(vm)}: {exc}")

    payload["collector"]["clusters_total"] = len(payload["clusters"])
    if warnings:
        # Keep collector status OK because the template should not raise collector failed
        # when only optional sections are unavailable. Detail is visible in collector.message.
        payload["collector"]["message"] = "; ".join(warnings)[:2000]
    payload["collector"]["duration_sec"] = round(time.time() - start_ts, 3)
    build_lld_from_payload(payload)
    return payload


def main(argv: List[str]) -> int:
    start = time.time()
    if len(argv) < 7:
        fatal_json(
            "Usage: zbx_vsan_api.py <vcenter_sdk_url> <user> <password> <cluster_matches> <cluster_not_matches> <timeout>",
            duration=time.time() - start,
        )
        return 0
    url = argv[1]
    username = argv[2]
    password = argv[3]
    include_re = argv[4] or ".*"
    exclude_re = argv[5] or "CHANGE_IF_NEEDED"
    timeout = max(to_int(argv[6], 60), 10)
    install_timeout(timeout)
    try:
        payload = collect(url, username, password, include_re, exclude_re, timeout)
        output_payload(payload)
    except Exception as exc:
        if DEBUG:
            traceback.print_exc(file=sys.stderr)
        fatal_json(f"Collector failed: {exc}", duration=time.time() - start)
    finally:
        cancel_timeout()
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
