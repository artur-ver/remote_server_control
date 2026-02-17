import platform
import getpass
import psutil
from flask import render_template

def system_info():
    info = {
        "hostname": platform.node(),
        "os": f"{platform.system()} {platform.release()} ({platform.version()})",
        "python": platform.python_version(),
        "user": getpass.getuser(),
        "boot_time": psutil.boot_time(),
        "cpu_count": psutil.cpu_count(),
        "cpu_count_phys": psutil.cpu_count(logical=False),
        "mem": psutil.virtual_memory()._asdict(),
    }
    return render_template("system.html", info=info)
