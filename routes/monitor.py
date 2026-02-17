import time
import psutil
from flask import render_template, jsonify
from utils import get_gpu_info

def monitor():
    return render_template("monitor.html")

def metrics():
    mem = psutil.virtual_memory()
    cpu = psutil.cpu_percent(interval=None)
    cpu_freq = psutil.cpu_freq()
    cpu_cur = int(cpu_freq.current) if cpu_freq else None
    cpu_max = int(cpu_freq.max) if cpu_freq else None
    # Aggregate disks
    total_disk = 0
    used_disk = 0
    for part in psutil.disk_partitions(all=False):
        try:
            usage = psutil.disk_usage(part.mountpoint)
            total_disk += usage.total
            used_disk += usage.used
        except Exception:
            continue
    disk_percent = round((used_disk / total_disk) * 100, 1) if total_disk else 0
    net = psutil.net_io_counters()
    disk_io = psutil.disk_io_counters()
    gpus = get_gpu_info()
    return jsonify(
        {
            "ts": time.time(),
            "cpu_percent": cpu,
            "cpu_freq_cur": cpu_cur,
            "cpu_freq_max": cpu_max,
            "cpu_cores": psutil.cpu_count(logical=False) or 0,
            "cpu_threads": psutil.cpu_count() or 0,
            "mem_total": mem.total,
            "mem_used": mem.used,
            "mem_percent": mem.percent,
            "mem_available": mem.available,
            "disk_total": total_disk,
            "disk_used": used_disk,
            "disk_percent": disk_percent,
            "net_bytes_sent": net.bytes_sent,
            "net_bytes_recv": net.bytes_recv,
            "disk_read_bytes": getattr(disk_io, "read_bytes", 0),
            "disk_write_bytes": getattr(disk_io, "write_bytes", 0),
            "gpus": gpus,
        }
    )
