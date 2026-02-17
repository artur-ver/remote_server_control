import os
import psutil
from flask import current_app, render_template, request
from utils import get_dir_sizes

def disks():
    parts = []
    for p in psutil.disk_partitions(all=False):
        try:
            u = psutil.disk_usage(p.mountpoint)
            parts.append({"device": p.device, "mount": p.mountpoint, "fstype": p.fstype, "total": u.total, "used": u.used, "percent": u.percent})
        except Exception:
            continue
    path = request.args.get("path")
    du_items = None
    if path:
        try:
            target = path if os.path.isabs(path) else os.path.join(current_app.config["BASE_DIR"], path)
            du_items = get_dir_sizes(target)
        except Exception:
            du_items = None
    return render_template("disks.html", parts=parts, du_path=path, du_items=du_items)
