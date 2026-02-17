import os
import subprocess
import psutil
from flask import abort

def safe_join(base, *paths):
    candidate = os.path.abspath(os.path.join(base, *paths))
    base_abs = os.path.abspath(base)
    if os.path.commonpath([candidate, base_abs]) != base_abs:
        abort(403)
    return candidate

def is_text_file(path, read_bytes=1024):
    try:
        with open(path, "rb") as f:
            chunk = f.read(read_bytes)
        if b"\x00" in chunk:
            return False
        return True
    except Exception:
        return False

def bytes_human(value):
    try:
        v = float(value)
    except Exception:
        return value
    units = ["B", "KB", "MB", "GB", "TB"]
    i = 0
    while v >= 1024 and i < len(units) - 1:
        v /= 1024.0
        i += 1
    if i == 0:
        return f"{int(v)} {units[i]}"
    return f"{v:.1f} {units[i]}"

def get_gpu_info():
    gpus = []
    # Try NVML (NVIDIA)
    try:
        import pynvml
        pynvml.nvmlInit()
        count = pynvml.nvmlDeviceGetCount()
        for i in range(count):
            h = pynvml.nvmlDeviceGetHandleByIndex(i)
            util = pynvml.nvmlDeviceGetUtilizationRates(h)
            mem = pynvml.nvmlDeviceGetMemoryInfo(h)
            name = pynvml.nvmlDeviceGetName(h).decode("utf-8", errors="ignore")
            gpus.append(
                {
                    "index": i,
                    "name": name,
                    "util_percent": int(getattr(util, "gpu", 0)),
                    "mem_total": int(getattr(mem, "total", 0)),
                    "mem_used": int(getattr(mem, "used", 0)),
                }
            )
        pynvml.nvmlShutdown()
        return gpus
    except Exception:
        pass
    # Fallback to nvidia-smi if available
    try:
        proc = subprocess.run(
            ["nvidia-smi", "--query-gpu=name,utilization.gpu,memory.total,memory.used", "--format=csv,noheader,nounits"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=3,
        )
        if proc.returncode == 0 and proc.stdout:
            for idx, line in enumerate(proc.stdout.strip().splitlines()):
                parts = [p.strip() for p in line.split(",")]
                if len(parts) >= 4:
                    try:
                        name, util, mem_total, mem_used = parts[:4]
                        gpus.append(
                            {
                                "index": idx,
                                "name": name,
                                "util_percent": int(float(util)),
                                "mem_total": int(float(mem_total) * 1024 * 1024),  # MB -> bytes
                                "mem_used": int(float(mem_used) * 1024 * 1024),
                            }
                        )
                    except Exception:
                        continue
    except Exception:
        pass
    return gpus

def parse_sc_query():
    try:
        proc = subprocess.run(["sc", "query", "state=", "all"], capture_output=True, text=True, encoding="cp866", errors="replace")
        lines = proc.stdout.splitlines()
        items = []
        current = {}
        for line in lines:
            if "SERVICE_NAME:" in line:
                if current:
                    items.append(current)
                current = {"service_name": line.split("SERVICE_NAME:")[1].strip()}
            elif "DISPLAY_NAME:" in line:
                current["display_name"] = line.split("DISPLAY_NAME:")[1].strip()
            elif "STATE" in line and ":" in line:
                state = line.split(":", 1)[1].strip().split("  ")[0].strip()
                current["state"] = state
        if current:
            items.append(current)
        return items
    except Exception:
        return []

def schtasks_list():
    tasks = []
    try:
        res = subprocess.run(["schtasks", "/Query", "/FO", "CSV"], capture_output=True, text=True, encoding="cp866", errors="replace")
        if res.returncode == 0:
            import csv, io
            reader = csv.DictReader(io.StringIO(res.stdout))
            for row in reader:
                tasks.append({"name": row.get("TaskName"), "status": row.get("Status"), "next_run": row.get("Next Run Time")})
    except Exception:
        pass
    return tasks

def tail_file(path, lines=200):
    try:
        with open(path, "rb") as f:
            f.seek(0, os.SEEK_END)
            size = f.tell()
            block = 4096
            data = b""
            while size > 0 and data.count(b"\n") <= lines:
                read_size = min(block, size)
                size -= read_size
                f.seek(size)
                data = f.read(read_size) + data
            text = data.decode("utf-8", errors="replace")
            return "\n".join(text.splitlines()[-lines:])
    except Exception:
        return ""

def get_dir_sizes(path, max_items=30):
    items = []
    try:
        with os.scandir(path) as it:
            for entry in it:
                try:
                    if entry.is_file():
                        size = entry.stat().st_size
                    elif entry.is_dir():
                        size = 0
                        with os.scandir(entry.path) as it2:
                            for e2 in it2:
                                try:
                                    if e2.is_file():
                                        size += e2.stat().st_size
                                except Exception:
                                    continue
                    else:
                        size = 0
                    items.append({"name": entry.name, "is_dir": entry.is_dir(), "size": size})
                except Exception:
                    continue
    except Exception:
        pass
    items.sort(key=lambda x: x["size"], reverse=True)
    return items[:max_items]
